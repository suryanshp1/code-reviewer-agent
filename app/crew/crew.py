"""CrewAI orchestration for code review multi-agent system."""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Optional

from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task
import yaml

from app.config import config
from app.schemas import ReviewMetadata, ReviewRequest, ReviewResponse
from app.utils import count_tokens, detect_language

logger = logging.getLogger(__name__)


@CrewBase
class CodeReviewCrew:
    """CrewAI-based code review orchestration."""

    # Use absolute paths to avoid CrewAI path resolution issues
    agents_config = str(Path(__file__).parent / "agents.yaml")
    tasks_config = str(Path(__file__).parent / "tasks.yaml")

    def __init__(self):
        """Initialize the code review crew."""
        self.llm = self._initialize_llm()
        logger.info(
            f"Initialized CodeReviewCrew with {config.llm_provider} "
            f"using model {config.llm_model}"
        )

    def _initialize_llm(self):
        """Initialize the LLM based on configuration."""
        # CrewAI's LLM class uses format: 'provider/model'
        # For Groq: 'groq/model-name'
        # For OpenAI: 'openai/model-name' or just 'model-name'
        if config.llm_provider == "groq":
            model_string = f"groq/{config.llm_model}"
        elif config.llm_provider == "openai":
            model_string = config.llm_model  # OpenAI is default, no prefix needed
        else:
            raise ValueError(f"Unsupported LLM provider: {config.llm_provider}")
        
        return LLM(
            model=model_string,
            api_key=config.llm_api_key,
            temperature=0.1,  # Low temperature for consistent reviews
        )

    @agent
    def code_analyzer(self) -> Agent:
        """Create code analyzer agent."""
        return Agent(
            role="Senior Software Engineer",
            goal="Analyze code structure, identify complexity patterns, architectural issues, and logical flaws in the provided code diff",
            backstory="You are a seasoned software engineer with 15+ years of experience across multiple programming languages and paradigms. You have a deep understanding of software architecture, design patterns, and code organization.",
            verbose=config.debug,
            allow_delegation=False,
            max_iter=3,
            llm=self.llm,
        )

    @agent
    def security_reviewer(self) -> Agent:
        """Create security reviewer agent."""
        return Agent(
            role="Application Security Engineer",
            goal="Identify security vulnerabilities, potential attack vectors, and unsafe coding practices in the code diff",
            backstory="You are an OWASP expert and certified penetration tester with extensive experience in application security. You excel at identifying SQL injection, XSS, CSRF, authentication flaws, and cryptographic issues.",
            verbose=config.debug,
            allow_delegation=False,
            max_iter=3,
            llm=self.llm,
        )

    @agent
    def performance_reviewer(self) -> Agent:
        """Create performance reviewer agent."""
        return Agent(
            role="Performance Engineering Specialist",
            goal="Analyze the following code diff for performance issues, inefficiencies, and scalability concerns",
            backstory="You are a performance optimization expert specializing in profiling, benchmarking, and scalability. You understand Big O complexity, caching strategies, database optimization, and async patterns.",
            verbose=config.debug,
            allow_delegation=False,
            max_iter=3,
            llm=self.llm,
        )

    @agent
    def style_reviewer(self) -> Agent:
        """Create style reviewer agent."""
        return Agent(
            role="Staff Engineer and Code Quality Advocate",
            goal="Review the following code diff for code style, maintainability, readability, and adherence to best practices",
            backstory="You are a staff engineer passionate about code quality, readability, and maintainability. You champion clean code principles, proper naming, documentation, and SOLID principles.",
            verbose=config.debug,
            allow_delegation=False,
            max_iter=3,
            llm=self.llm,
        )

    @agent
    def review_synthesizer(self) -> Agent:
        """Create review synthesizer agent."""
        return Agent(
            role="Principal Engineer and Code Review Lead",
            goal="Synthesize all review findings from the specialist agents into a comprehensive, prioritized code review report",
            backstory="You are a principal engineer who coordinates code reviews across teams. You excel at synthesizing multiple perspectives, prioritizing issues, and providing actionable feedback.",
            verbose=config.debug,
            allow_delegation=False,
            max_iter=5,
            llm=self.llm,
        )

    @task
    def analyze_code_task(self) -> Task:
        """Create code analysis task."""
        return Task(
            config=self.tasks_config["analyze_code"],
        )

    @task
    def review_security_task(self) -> Task:
        """Create security review task."""
        return Task(
            config=self.tasks_config["review_security"],
        )

    @task
    def review_performance_task(self) -> Task:
        """Create performance review task."""
        return Task(
            config=self.tasks_config["review_performance"],
        )

    @task
    def review_style_task(self) -> Task:
        """Create style review task."""
        return Task(
            config=self.tasks_config["review_style"],
        )

    @task
    def synthesize_review_task(self) -> Task:
        """Create review synthesis task."""
        return Task(
            config=self.tasks_config["synthesize_review"],
        )

    @crew
    def crew(self) -> Crew:
        """Create the code review crew with hybrid parallel-sequential execution."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,  # CrewAI handles async tasks internally
            verbose=config.debug,
            memory=False,  # Disable memory for MVP (deterministic behavior)
        )

    def review_code(self, request: ReviewRequest) -> ReviewResponse:
        """
        Execute code review using the multi-agent crew.

        Args:
            request: Review request with diff and context

        Returns:
            Structured review response

        Raises:
            Exception: If review execution fails
        """
        start_time = time.time()

        # Auto-detect language if not provided or set to default
        language = request.language
        if language == "python" or not language:
            detected = detect_language(request.diff)
            if detected != "unknown":
                language = detected

        logger.info(
            f"Starting code review for {language} code, "
            f"diff size: {len(request.diff)} chars"
        )

        # Prepare inputs for the crew
        inputs = {
            "diff": request.diff,
            "language": language,
        }

        try:
            # Execute the crew
            result = self.crew().kickoff(inputs=inputs)

            # Parse the result
            review_data = self._parse_crew_output(result)

            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Count tokens (approximate)
            total_tokens = count_tokens(request.diff + str(review_data), config.llm_model)

            # Create metadata
            metadata = ReviewMetadata(
                execution_time_ms=execution_time_ms,
                tokens_used=total_tokens,
                agent_count=5,
                guardrails_applied=[],  # Will be populated by guardrails layer
                model=config.llm_model,
            )

            # Create response
            response = ReviewResponse(
                summary=review_data.get("summary", "Code review completed"),
                score=review_data.get("score", 8.0),
                findings=review_data.get("findings", []),
                metadata=metadata,
            )

            logger.info(
                f"Review completed: {len(response.findings)} findings, "
                f"score: {response.score:.1f}, time: {execution_time_ms}ms"
            )

            return response

        except Exception as e:
            logger.error(f"Error during code review: {e}", exc_info=True)
            # Return a fallback response
            execution_time_ms = int((time.time() - start_time) * 1000)
            metadata = ReviewMetadata(
                execution_time_ms=execution_time_ms,
                tokens_used=0,
                agent_count=5,
                guardrails_applied=[],
                model=config.llm_model,
            )
            return ReviewResponse(
                summary=f"Review failed: {str(e)}",
                score=5.0,
                findings=[],
                metadata=metadata,
            )

    def _parse_crew_output(self, result: Any) -> dict:
        """
        Parse crew output into structured data.

        Args:
            result: Raw crew output

        Returns:
            Parsed review data
        """
        try:
            # CrewAI result can be accessed via result.raw
            output_str = str(result.raw) if hasattr(result, "raw") else str(result)

            # Try to extract JSON from the output
            # The synthesizer should return JSON, but we need to handle markdown code blocks
            json_str = output_str

            # Remove markdown code blocks if present
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()

            # Parse JSON
            data = json.loads(json_str)

            # Validate structure
            if not isinstance(data, dict):
                raise ValueError("Output is not a dictionary")

            # Ensure required fields
            if "findings" not in data:
                data["findings"] = []
            if "summary" not in data:
                data["summary"] = "Code review completed"
            if "score" not in data:
                data["score"] = 8.0

            return data

        except Exception as e:
            logger.warning(f"Failed to parse crew output as JSON: {e}")
            logger.debug(f"Raw output: {result}")

            # Return a safe fallback
            return {
                "summary": "Review completed but output parsing failed",
                "score": 7.0,
                "findings": [],
            }


# Singleton instance for reuse
_crew_instance: Optional[CodeReviewCrew] = None


def get_crew() -> CodeReviewCrew:
    """Get or create the singleton crew instance."""
    global _crew_instance
    if _crew_instance is None:
        _crew_instance = CodeReviewCrew()
    return _crew_instance
