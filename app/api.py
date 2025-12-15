"""FastAPI gateway for code review service."""

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import JSONResponse

from app import __version__
from app.config import config
# Lazy import: get_crew imported after env cleanup in lifespan
from app.guardrails import get_guardrail_orchestrator
from app.schemas import HealthResponse, ReviewRequest, ReviewResponse
from app.utils import generate_request_id, sanitize_diff

# Configure logging
config.configure_logging()
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Rate limiting (simple in-memory store for MVP)
request_timestamps: dict[str, list[float]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Code Reviewer CI Agent API")
    logger.info(f"Version: {__version__}")
    logger.info(f"LLM Provider: {config.llm_provider}")
    logger.info(f"LLM Model: {config.llm_model}")
    logger.info(f"Ray Serve Enabled: {config.enable_ray_serve}")

    # CRITICAL: Clean up unused LLM provider API keys BEFORE importing crew
    # CrewAI reads environment variables directly, must remove wrong ones early
    if config.llm_provider == "groq":
        # Set dummy OPENAI_API_KEY to prevent CrewAI errors (it checks even when not used)
        os.environ["OPENAI_API_KEY"] = "sk-dummy-key-not-used"
        logger.info("✓ Set dummy OPENAI_API_KEY (using Groq - OpenAI not used)")
    elif config.llm_provider == "openai":
        os.environ.pop("GROQ_API_KEY", None)
        logger.info("✓ Removed GROQ_API_KEY from environment (using OpenAI)")

    # Initialize crew (warm up) - import here after env cleanup
    try:
        from app.crew.crew import get_crew
        get_crew()
        logger.info("Code review crew initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize crew: {e}")

    yield

    logger.info("Shutting down Code Reviewer CI Agent API")


# Create FastAPI app
app = FastAPI(
    title="Code Reviewer CI Agent",
    description="AI-powered code review using CrewAI multi-agent framework",
    version=__version__,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing."""
    request_id = generate_request_id()
    start_time = time.time()

    # Add request ID to state
    request.state.request_id = request_id

    logger.info(
        f"[{request_id}] {request.method} {request.url.path} - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )

    response = await call_next(request)

    duration_ms = int((time.time() - start_time) * 1000)
    logger.info(
        f"[{request_id}] Completed in {duration_ms}ms - Status: {response.status_code}"
    )

    return response


def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Verify API key from Authorization header.

    Args:
        credentials: HTTP credentials

    Returns:
        API key

    Raises:
        HTTPException: If API key is invalid
    """
    token = credentials.credentials

    if token != config.review_api_key:
        logger.warning(f"Invalid API key attempt: {token[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token


def check_rate_limit(api_key: str) -> None:
    """
    Check rate limit for API key.

    Args:
        api_key: API key to check

    Raises:
        HTTPException: If rate limit exceeded
    """
    current_time = time.time()
    minute_ago = current_time - 60

    # Clean up old timestamps
    if api_key in request_timestamps:
        request_timestamps[api_key] = [
            ts for ts in request_timestamps[api_key] if ts > minute_ago
        ]
    else:
        request_timestamps[api_key] = []

    # Check limit
    if len(request_timestamps[api_key]) >= config.rate_limit_per_minute:
        logger.warning(f"Rate limit exceeded for API key: {api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {config.rate_limit_per_minute} requests per minute.",
        )

    # Add current request
    request_timestamps[api_key].append(current_time)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        Health status information
    """
    return HealthResponse(
        status="healthy",
        version=__version__,
        ray_serve_enabled=config.enable_ray_serve,
        llm_provider=config.llm_provider,
    )


@app.post("/review", response_model=ReviewResponse, tags=["Review"])
async def review_code(
    request: ReviewRequest,
    api_key: Annotated[str, Depends(verify_api_key)],
) -> ReviewResponse:
    """
    Review code changes using AI agents.

    Args:
        request: Review request with diff and context
        api_key: API key for authentication

    Returns:
        Structured review response with findings and summary

    Raises:
        HTTPException: If review fails or timeout occurs
    """
    # Check rate limit
    check_rate_limit(api_key)

    logger.info(f"Received review request for {request.language} code")

    try:
        # Sanitize diff
        sanitized_diff = sanitize_diff(request.diff)
        request.diff = sanitized_diff

        # Get crew and execute review (lazy import)
        from app.crew.crew import get_crew
        crew = get_crew()

        # Execute with timeout
        import asyncio
        from concurrent.futures import TimeoutError

        try:
            # Run crew in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(None, crew.review_code, request),
                timeout=config.request_timeout_seconds,
            )
        except asyncio.TimeoutError:
            logger.error("Review timed out")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Review timed out after {config.request_timeout_seconds} seconds",
            )

        # Apply guardrails
        orchestrator = get_guardrail_orchestrator()
        response = orchestrator.apply(
            response,
            context={
                "diff": request.diff,
                "language": request.language,
            },
        )

        logger.info(
            f"Review completed successfully: {len(response.findings)} findings, "
            f"score: {response.score:.1f}"
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during code review: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code review failed: {str(e)}",
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured error responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.api:app",
        host="0.0.0.0",
        port=8000,
        reload=config.debug,
        log_level=config.log_level.lower(),
    )
