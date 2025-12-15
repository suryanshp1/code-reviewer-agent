"""Ray Serve deployment for scalable code review service."""

import logging
from typing import Dict

from ray import serve
from fastapi import FastAPI

from app.api import app as fastapi_app
from app.config import config
from app.crew.crew import CodeReviewCrew
from app.guardrails import GuardrailOrchestrator
from app.schemas import ReviewRequest, ReviewResponse

logger = logging.getLogger(__name__)


@serve.deployment(
    num_replicas=config.ray_num_replicas,
    max_concurrent_queries=config.ray_max_concurrent_queries,
    ray_actor_options={
        "num_cpus": 2,
        "num_gpus": 0,
    },
)
@serve.ingress(fastapi_app)
class CodeReviewDeployment:
    """
    Ray Serve deployment for code review service.

    This wraps the FastAPI app and provides horizontal scaling capabilities.
    """

    def __init__(self):
        """Initialize the deployment."""
        logger.info("Initializing CodeReviewDeployment")
        config.configure_logging()

        # Initialize crew and guardrails (warm up)
        self.crew = CodeReviewCrew()
        self.guardrails = GuardrailOrchestrator()

        logger.info(
            f"CodeReviewDeployment initialized with {config.ray_num_replicas} replicas"
        )


# Deployment configuration
deployment = CodeReviewDeployment.bind()


def start_serve():
    """Start Ray Serve deployment."""
    import ray

    # Initialize Ray if not already initialized
    if not ray.is_initialized():
        ray.init()

    # Deploy the application
    serve.run(
        deployment,
        host=config.ray_serve_host,
        port=config.ray_serve_port,
        name="code_review_service",
    )

    logger.info(
        f"Ray Serve deployment started at http://{config.ray_serve_host}:{config.ray_serve_port}"
    )


if __name__ == "__main__":
    start_serve()
