"""Guardrails for ensuring review quality and safety."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Tuple

from app.config import config
from app.schemas import ReviewResponse, FindingSeverity
from app.utils import extract_files_from_diff

logger = logging.getLogger(__name__)


class Guardrail(ABC):
    """Base class for guardrails."""

    @abstractmethod
    def validate(
        self, response: ReviewResponse, context: dict
    ) -> Tuple[bool, ReviewResponse, str]:
        """
        Validate and potentially modify the review response.

        Args:
            response: Review response to validate
            context: Additional context (e.g., original diff)

        Returns:
            Tuple of (is_valid, modified_response, guardrail_name)
        """
        pass


class MaxFindingsGuardrail(Guardrail):
    """Limit the maximum number of findings to prevent noise."""

    def validate(
        self, response: ReviewResponse, context: dict
    ) -> Tuple[bool, ReviewResponse, str]:
        """Limit findings to maximum allowed."""
        max_findings = config.max_findings_per_review

        if len(response.findings) <= max_findings:
            return True, response, "max_findings"

        logger.warning(
            f"Truncating findings from {len(response.findings)} to {max_findings}"
        )

        # Keep highest severity findings
        sorted_findings = sorted(
            response.findings,
            key=lambda f: (
                ["low", "medium", "high", "critical"].index(f.severity.value),
                f.category.value,
            ),
            reverse=True,
        )

        response.findings = sorted_findings[:max_findings]
        response.metadata.guardrails_applied.append("max_findings")

        return True, response, "max_findings"


class FileNameValidationGuardrail(Guardrail):
    """Ensure all file references exist in the original diff."""

    def validate(
        self, response: ReviewResponse, context: dict
    ) -> Tuple[bool, ReviewResponse, str]:
        """Validate file names against diff."""
        diff = context.get("diff", "")
        valid_files = set(extract_files_from_diff(diff))

        if not valid_files:
            # If we can't extract files, skip validation
            logger.warning("Could not extract files from diff, skipping file validation")
            return True, response, "file_validation"

        # Filter findings with invalid file references
        original_count = len(response.findings)
        response.findings = [
            f for f in response.findings if f.file in valid_files or f.file == "unknown"
        ]

        removed = original_count - len(response.findings)
        if removed > 0:
            logger.warning(f"Removed {removed} findings with invalid file references")
            response.metadata.guardrails_applied.append("file_validation")

        return True, response, "file_validation"


class EmptyMessageGuardrail(Guardrail):
    """Remove findings with empty or trivial messages."""

    def validate(
        self, response: ReviewResponse, context: dict
    ) -> Tuple[bool, ReviewResponse, str]:
        """Remove findings with empty messages."""
        original_count = len(response.findings)

        response.findings = [
            f
            for f in response.findings
            if f.message.strip()
            and f.suggestion.strip()
            and len(f.message) > 10
            and len(f.suggestion) > 10
        ]

        removed = original_count - len(response.findings)
        if removed > 0:
            logger.warning(f"Removed {removed} findings with empty/trivial messages")
            response.metadata.guardrails_applied.append("empty_message")

        return True, response, "empty_message"


class DuplicateDetectionGuardrail(Guardrail):
    """Remove duplicate findings."""

    def validate(
        self, response: ReviewResponse, context: dict
    ) -> Tuple[bool, ReviewResponse, str]:
        """Remove duplicate findings based on file, line, and message similarity."""
        seen = set()
        unique_findings = []

        for finding in response.findings:
            # Create a fingerprint for the finding
            fingerprint = (
                finding.file,
                finding.line,
                finding.category.value,
                # Use first 50 chars of message for similarity
                finding.message[:50].lower().strip(),
            )

            if fingerprint not in seen:
                seen.add(fingerprint)
                unique_findings.append(finding)

        removed = len(response.findings) - len(unique_findings)
        if removed > 0:
            logger.info(f"Removed {removed} duplicate findings")
            response.findings = unique_findings
            response.metadata.guardrails_applied.append("duplicate_detection")

        return True, response, "duplicate_detection"


class SeverityValidationGuardrail(Guardrail):
    """Ensure severity levels are reasonable."""

    def validate(
        self, response: ReviewResponse, context: dict
    ) -> Tuple[bool, ReviewResponse, str]:
        """Validate severity assignments."""
        # Downgrade security findings marked as "low" for serious vulnerabilities
        # This is a simple heuristic-based check

        serious_keywords = [
            "injection",
            "xss",
            "sql",
            "authentication",
            "authorization",
            "credential",
            "password",
            "secret",
            "token",
        ]

        modified = False
        for finding in response.findings:
            if finding.category.value == "security" and finding.severity == FindingSeverity.LOW:
                # Check if message contains serious keywords
                message_lower = finding.message.lower()
                if any(keyword in message_lower for keyword in serious_keywords):
                    logger.warning(
                        f"Upgrading security finding severity from LOW to MEDIUM: {finding.message[:50]}"
                    )
                    finding.severity = FindingSeverity.MEDIUM
                    modified = True

        if modified:
            response.metadata.guardrails_applied.append("severity_validation")

        return True, response, "severity_validation"


class GuardrailOrchestrator:
    """Orchestrate multiple guardrails."""

    def __init__(self):
        """Initialize guardrails."""
        self.guardrails: list[Guardrail] = [
            EmptyMessageGuardrail(),
            DuplicateDetectionGuardrail(),
            FileNameValidationGuardrail(),
            SeverityValidationGuardrail(),
            MaxFindingsGuardrail(),  # Run last to limit final count
        ]
        logger.info(f"Initialized {len(self.guardrails)} guardrails")

    def apply(self, response: ReviewResponse, context: dict) -> ReviewResponse:
        """
        Apply all guardrails to the review response.

        Args:
            response: Review response to validate
            context: Additional context (original diff, etc.)

        Returns:
            Validated and potentially modified response
        """
        logger.info(
            f"Applying guardrails to review with {len(response.findings)} findings"
        )

        for guardrail in self.guardrails:
            try:
                is_valid, response, name = guardrail.validate(response, context)
                if not is_valid:
                    logger.warning(f"Guardrail {name} marked response as invalid")
            except Exception as e:
                logger.error(f"Error in guardrail {guardrail.__class__.__name__}: {e}")
                # Continue with other guardrails

        logger.info(
            f"Guardrails applied: {response.metadata.guardrails_applied}, "
            f"final findings count: {len(response.findings)}"
        )

        return response


# Singleton instance
_orchestrator: GuardrailOrchestrator | None = None


def get_guardrail_orchestrator() -> GuardrailOrchestrator:
    """Get or create the singleton guardrail orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = GuardrailOrchestrator()
    return _orchestrator
