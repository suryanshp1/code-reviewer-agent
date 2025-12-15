"""Application configuration using Pydantic Settings."""

import logging
import os
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def is_huggingface_space() -> bool:
    """Detect if running in Hugging Face Spaces environment."""
    return os.getenv("SPACE_ID") is not None or os.getenv("SPACE_REPO_NAME") is not None


class AppConfig(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM Provider Configuration
    llm_provider: Literal["openai", "groq"] = Field(
        "openai", description="LLM provider to use"
    )
    openai_api_key: str = Field("", description="OpenAI API key")
    openai_model: str = Field("gpt-4o-mini", description="OpenAI model to use")
    groq_api_key: str = Field("", description="Groq API key")
    groq_model: str = Field("llama-3.3-70b-versatile", description="Groq model to use")

    # API Authentication
    review_api_key: str = Field(..., description="API key for authentication")

    # Rate Limiting
    rate_limit_per_minute: int = Field(10, ge=1, le=100, description="Max requests per minute")

    # Ray Serve Configuration
    enable_ray_serve: bool = Field(False, description="Enable Ray Serve deployment")
    ray_serve_host: str = Field("0.0.0.0", description="Ray Serve host")
    ray_serve_port: int = Field(8000, ge=1024, le=65535, description="Ray Serve port")
    ray_num_replicas: int = Field(2, ge=1, le=10, description="Number of Ray replicas")
    ray_max_concurrent_queries: int = Field(
        10, ge=1, le=100, description="Max concurrent queries per replica"
    )

    # Guardrails Configuration
    max_findings_per_review: int = Field(
        20, ge=1, le=100, description="Maximum findings to return"
    )
    max_tokens_per_review: int = Field(
        15000, ge=1000, le=100000, description="Maximum tokens per review"
    )
    enable_llm_judge_guardrails: bool = Field(
        True, description="Enable LLM-as-Judge guardrails"
    )

    # Application Settings
    log_level: str = Field("INFO", description="Logging level")
    request_timeout_seconds: int = Field(
        120, ge=30, le=300, description="Request timeout in seconds"
    )
    max_diff_size_bytes: int = Field(
        1_048_576, ge=1024, le=10_485_760, description="Max diff size in bytes"
    )

    # CORS Settings
    cors_origins: str = Field("*", description="Comma-separated CORS origins")

    # Debug Mode
    debug: bool = Field(False, description="Enable debug mode")

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        """Validate LLM provider is supported."""
        if v not in ["openai", "groq"]:
            raise ValueError(f"Unsupported LLM provider: {v}")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins into a list."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def llm_api_key(self) -> str:
        """Get API key for the active LLM provider."""
        if self.llm_provider == "openai":
            if not self.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            return self.openai_api_key
        elif self.llm_provider == "groq":
            if not self.groq_api_key:
                raise ValueError("Groq API key not configured")
            return self.groq_api_key
        raise ValueError(f"Unknown LLM provider: {self.llm_provider}")

    @property
    def llm_model(self) -> str:
        """Get model name for the active LLM provider."""
        if self.llm_provider == "openai":
            return self.openai_model
        elif self.llm_provider == "groq":
            return self.groq_model
        raise ValueError(f"Unknown LLM provider: {self.llm_provider}")

    def optimize_for_huggingface(self) -> None:
        """Automatically optimize settings for Hugging Face Spaces free tier."""
        if not is_huggingface_space():
            return
        
        logger = logging.getLogger(__name__)
        logger.info("🤗 Detected Hugging Face Spaces environment - optimizing configuration")
        
        # Disable Ray Serve (not suitable for free tier)
        if self.enable_ray_serve:
            logger.warning("Disabling Ray Serve for HF free tier")
            self.enable_ray_serve = False
        
        # Lower rate limits for free tier
        if self.rate_limit_per_minute > 5:
            logger.info(f"Adjusting rate limit from {self.rate_limit_per_minute} to 5 for HF free tier")
            self.rate_limit_per_minute = 5
        
        # Shorter timeout to prevent resource exhaustion
        if self.request_timeout_seconds > 90:
            logger.info(f"Adjusting timeout from {self.request_timeout_seconds} to 90s for HF free tier")
            self.request_timeout_seconds = 90
        
        # Reduce max findings to save tokens
        if self.max_findings_per_review > 15:
            logger.info(f"Adjusting max findings from {self.max_findings_per_review} to 15 for HF free tier")
            self.max_findings_per_review = 15
        
        logger.info("✅ Configuration optimized for Hugging Face Spaces")

    def configure_logging(self) -> None:
        """Configure application logging."""
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


# Global config instance
config = AppConfig()

# Auto-optimize for Hugging Face if detected
config.optimize_for_huggingface()
