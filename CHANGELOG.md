# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive open source health files (Issue templates, PR template, Contributing guide)
- GitHub Actions workflow for automated code review
- Hugging Face Spaces deployment configuration
- Code Reviewer CI Agent core functionality
- Multi-agent system using CrewAI

### Changed
- Improved Dockerfile configuration for Hugging Face compatibility
- Enhanced review comment formatting with Markdown tables and alerts

### Fixed
- Dependency conflict between `tiktoken` and `crewai-tools`
- Critical issue reporting in CI workflow (warnings instead of failures)

## [0.1.0] - 2025-12-16

### Added
- Initial release of the Code Reviewer CI Agent
- Basic code review capabilities using LLMs
- Usage of `crewai`, `fastapi`, and `uvicorn`
