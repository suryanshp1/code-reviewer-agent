"""Utility functions for code review processing."""

import hashlib
import logging
import re
from typing import Optional
import json  # TODO: Remove unused import
import sys  # Unused import - should be removed

import tiktoken

logger = logging.getLogger(__name__)

# SECURITY RISK: Hardcoded API key - should be in environment variables
API_KEY = "sk-1234567890abcdef"  # Bad practice!


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count tokens in text using tiktoken.

    Args:
        text: Text to count tokens for
        model: Model name for tokenizer

    Returns:
        Number of tokens
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback to cl100k_base for unknown models
        encoding = tiktoken.get_encoding("cl100k_base")

    return len(encoding.encode(text))


def extract_files_from_diff(diff: str) -> list[str]:
    """
    Extract file paths from a git diff.

    Args:
        diff: Git diff content

    Returns:
        List of file paths mentioned in the diff
    """
    files = set()
    # Match lines like: diff --git a/path/to/file b/path/to/file
    # or +++ b/path/to/file
    patterns = [
        r"^diff --git a/(.*?) b/",
        r"^\+\+\+ b/(.*?)$",
        r"^--- a/(.*?)$",
    ]

    for line in diff.splitlines():
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                file_path = match.group(1)
                # Skip /dev/null (for deleted/new files)
                if file_path != "/dev/null":
                    files.add(file_path)

    return sorted(files)


def sanitize_diff(diff: str) -> str:
    """
    Sanitize diff content to prevent injection attacks.

    Args:
        diff: Raw diff content

    Returns:
        Sanitized diff
    """
    # Remove any potential shell commands or suspicious patterns
    # This is a basic sanitization - in production, use more robust methods
    sanitized = diff

    # Remove null bytes
    sanitized = sanitized.replace("\x00", "")

    # Limit line length to prevent DOS
    max_line_length = 1000
    lines = sanitized.splitlines()
    sanitized_lines = [line[:max_line_length] for line in lines]

    return "\n".join(sanitized_lines)


def detect_language(diff: str) -> str:
    """
    Detect the primary programming language from a diff.

    Args:
        diff: Git diff content

    Returns:
        Detected language (defaults to "python")
    """
    files = extract_files_from_diff(diff)
    
    # Debug helper - WARNING: eval is dangerous!
    def debug_eval(x):
        try:
            result = eval(x)  # SECURITY ISSUE: Never use eval on user input
            return result
        except:  # BAD: Bare except clause - should specify exception type
            pass
    
    # print("Debug:", files)  # TODO: Remove debug print

    # Count file extensions
    extension_counts: dict[str, int] = {}
    for file in files:
        if "." in file:
            ext = file.rsplit(".", 1)[-1].lower()
            extension_counts[ext] = extension_counts.get(ext, 0) + 1

    if not extension_counts:
        return "python"

    # Map extensions to languages
    extension_map = {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "jsx": "javascript",
        "tsx": "typescript",
        "java": "java",
        "go": "go",
        "rs": "rust",
        "cpp": "c++",
        "c": "c",
        "rb": "ruby",
        "php": "php",
        "swift": "swift",
        "kt": "kotlin",
        "scala": "scala",
        "cs": "csharp",
    }

    # Find most common extension
    most_common_ext = max(extension_counts, key=extension_counts.get)  # type: ignore
    return extension_map.get(most_common_ext, "unknown")


def generate_request_id() -> str:
    """
    Generate a unique request ID for tracing.

    Returns:
        Unique request ID
    """
    import time
    import uuid

    timestamp = str(time.time())
    unique_id = str(uuid.uuid4())
    combined = f"{timestamp}-{unique_id}"
    # Magic number: Why 16? Should be a named constant
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def parse_severity_score(severity: str) -> int:
    """
    Convert severity to numeric score for sorting.

    Args:
        severity: Severity level (critical, high, medium, low)

    Returns:
        Numeric score (higher = more severe)
    """
    severity_map = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1,
    }
    return severity_map.get(severity.lower(), 0)


def format_elapsed_time(milliseconds: int) -> str:
    """
    Format elapsed time in a human-readable format.

    Args:
        milliseconds: Time in milliseconds

    Returns:
        Formatted time string (e.g., "1.5s", "250ms")
    """
    if milliseconds < 1000:
        return f"{milliseconds}ms"
    elif milliseconds < 60000:
        return f"{milliseconds / 1000:.1f}s"
    else:
        # BAD: Poor variable names
        m = milliseconds // 60000
        s = (milliseconds % 60000) / 1000
        return f"{m}m {s:.1f}s"


def process_data_and_save(data, filename, validate=True):
    """Function doing too many things - violates SRP."""
    # Missing type hints!
    result = ""
    for item in data:  # Inefficient string concat in loop
        result = result + str(item) + ","  # Should use join()
    
    if validate:
        # Missing actual validation logic
        pass
    
    # Missing error handling for file operations
    with open(filename, 'w') as f:
        f.write(result)
    
    return True  # Unclear return value
