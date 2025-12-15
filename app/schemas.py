"""Pydantic schemas for structured code review output."""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class FindingCategory(str, Enum):
    """Category of code review finding."""

    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    LOGIC = "logic"
    MAINTAINABILITY = "maintainability"


class FindingSeverity(str, Enum):
    """Severity level of finding."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReviewFinding(BaseModel):
    """Individual code review finding."""

    category: FindingCategory = Field(
        ..., description="Category of the issue (security, performance, style, logic, maintainability)"
    )
    severity: FindingSeverity = Field(..., description="Severity level of the issue")
    file: str = Field(..., description="File path where the issue was found")
    line: Optional[int] = Field(None, description="Line number where the issue occurs")
    message: str = Field(..., description="Clear description of the issue")
    suggestion: str = Field(..., description="Actionable suggestion for fixing the issue")

    @field_validator("message", "suggestion")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure message and suggestion are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class ReviewContext(BaseModel):
    """Additional context about the code review request."""

    repo: str = Field(..., description="Repository identifier (org/repo)")
    commit_sha: Optional[str] = Field(None, description="Commit SHA being reviewed")
    pr_number: Optional[int] = Field(None, description="Pull request number if applicable")
    author: Optional[str] = Field(None, description="Code author username")
    branch: Optional[str] = Field(None, description="Branch name")


class ReviewRequest(BaseModel):
    """Code review request payload."""

    diff: str = Field(..., description="Git diff to review", min_length=1)
    language: str = Field(
        "python", description="Primary programming language of the diff"
    )
    context: Optional[ReviewContext] = Field(
        None, description="Additional context about the request"
    )

    @field_validator("diff")
    @classmethod
    def validate_diff_size(cls, v: str) -> str:
        """Ensure diff is not too large."""
        max_size = 1_048_576  # 1MB
        if len(v.encode("utf-8")) > max_size:
            raise ValueError(f"Diff exceeds maximum size of {max_size} bytes")
        return v


class ReviewMetadata(BaseModel):
    """Metadata about the review execution."""

    execution_time_ms: int = Field(..., description="Time taken to execute review in milliseconds")
    tokens_used: int = Field(..., description="Total tokens consumed by LLM")
    agent_count: int = Field(5, description="Number of agents involved in review")
    guardrails_applied: list[str] = Field(
        default_factory=list, description="List of guardrails that were applied"
    )
    model: str = Field(..., description="LLM model used for review")


class ReviewResponse(BaseModel):
    """Structured code review response."""

    summary: str = Field(..., description="High-level summary of the review")
    score: float = Field(
        ..., ge=0.0, le=10.0, description="Overall code quality score (0-10)"
    )
    findings: list[ReviewFinding] = Field(
        default_factory=list, description="List of review findings"
    )
    metadata: ReviewMetadata = Field(..., description="Execution metadata")

    @property
    def critical_count(self) -> int:
        """Count of critical severity findings."""
        return sum(1 for f in self.findings if f.severity == FindingSeverity.CRITICAL)

    @property
    def high_count(self) -> int:
        """Count of high severity findings."""
        return sum(1 for f in self.findings if f.severity == FindingSeverity.HIGH)

    @property
    def findings_by_category(self) -> dict[FindingCategory, list[ReviewFinding]]:
        """Group findings by category."""
        result: dict[FindingCategory, list[ReviewFinding]] = {cat: [] for cat in FindingCategory}
        for finding in self.findings:
            result[finding.category].append(finding)
        return result

    def to_markdown(self) -> str:
        """Convert review to markdown format for GitHub PR comments."""
        lines = [
            "## 🤖 AI Code Review",
            "",
            f"**Summary:** {self.summary}",
            f"**Quality Score:** {self.score:.1f}/10",
            "",
        ]

        if not self.findings:
            lines.append("✅ No issues found! Great work!")
            return "\n".join(lines)

        # Group by severity
        critical = [f for f in self.findings if f.severity == FindingSeverity.CRITICAL]
        high = [f for f in self.findings if f.severity == FindingSeverity.HIGH]
        medium = [f for f in self.findings if f.severity == FindingSeverity.MEDIUM]
        low = [f for f in self.findings if f.severity == FindingSeverity.LOW]

        def format_findings(findings: list[ReviewFinding], emoji: str, title: str) -> list[str]:
            if not findings:
                return []
            result = [f"### {emoji} {title}", ""]
            for f in findings:
                location = f"`{f.file}:{f.line}`" if f.line else f"`{f.file}`"
                result.append(f"- **{f.category.value.title()}** in {location}")
                result.append(f"  > {f.message}")
                result.append(f"  > **Suggestion:** {f.suggestion}")
                result.append("")
            return result

        lines.extend(format_findings(critical, "🔴", "Critical Issues"))
        lines.extend(format_findings(high, "🟠", "High Severity"))
        lines.extend(format_findings(medium, "🟡", "Medium Severity"))
        lines.extend(format_findings(low, "🟢", "Low Severity"))

        # Footer
        lines.extend(
            [
                "---",
                f"*Reviewed by {self.metadata.agent_count} AI agents "
                f"using {self.metadata.model} "
                f"in {self.metadata.execution_time_ms}ms*",
            ]
        )

        return "\n".join(lines)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    ray_serve_enabled: bool = Field(..., description="Whether Ray Serve is enabled")
    llm_provider: str = Field(..., description="Active LLM provider")
