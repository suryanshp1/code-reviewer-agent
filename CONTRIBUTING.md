# Contributing to Code Reviewer CI Agent

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## 🌟 How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- Clear, descriptive title
- Detailed steps to reproduce
- Expected vs actual behavior
- Your environment details (OS, Python version, deployment type)
- Error logs and stack traces
- Configuration (with sensitive data removed)

Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.yml).

### Suggesting Features

Feature requests are welcome! Please:

- Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.yml)
- Explain the problem you're trying to solve
- Describe your proposed solution
- Consider alternative approaches
- Indicate if you're willing to implement it

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following our coding standards
3. **Add tests** for new functionality
4. **Update documentation** as needed
5. **Ensure tests pass** locally
6. **Submit a pull request** using our template

## 🛠️ Development Setup

### Prerequisites

- Python 3.11+
- Git
- Docker (optional, for testing)

### Local Development

```bash
# Clone your fork
git checkout https://github.com/YOUR-USERNAME/code-reviewer-ci-agent.git
cd code-reviewer-ci-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e ".[dev]"  # Install dev dependencies

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Run tests
pytest

# Run the application locally
uvicorn app.api:app --reload
```

### Environment Variables

Required for testing:

```bash
# LLM Provider (choose one or more)
OPENAI_API_KEY=your-key
GROQ_API_KEY=your-key

# Optional
LOG_LEVEL=DEBUG
MAX_FINDINGS_PER_REVIEW=20
```

## 📝 Coding Standards

### Python Style

We follow [PEP 8](https://peps.python.org/pep-0008/) with some modifications:

- Line length: 100 characters (not 79)
- Use type hints for all functions
- Use docstrings (Google style) for all public functions
- Use `black` for formatting
- Use `ruff` for linting

```bash
# Format code
black app/ tests/

# Lint code
ruff check app/ tests/

# Type checking
mypy app/
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes
- `build`: Build system changes

**Examples:**
```
feat(crew): add support for custom review templates
fix(api): handle timeout errors in code review endpoint
docs(readme): update deployment instructions
test(utils): add tests for token counting function
```

### Code Structure

```
app/
├── __init__.py
├── api.py              # FastAPI routes
├── config.py           # Configuration management
├── schemas.py          # Pydantic models
├── utils.py            # Utility functions
├── guardrails.py       # Input validation
├── crew/               # CrewAI agents
│   ├── __init__.py
│   └── crew.py
└── serve.py            # Ray Serve (optional)
```

### Testing

- Write tests for all new functionality
- Maintain or increase code coverage
- Use pytest fixtures for common setup
- Mock external API calls

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::test_review_endpoint
```

## 🔍 Pull Request Process

1. **Update Documentation**
   - Update README.md if adding features
   - Add docstrings to new functions
   - Update CHANGELOG.md

2. **Pass CI Checks**
   - All tests must pass
   - Code must be formatted with `black`
   - No linting errors from `ruff`
   - Type checking with `mypy` passes

3. **Review Process**
   - At least one maintainer approval required
   - Address all review comments
   - Keep PR focused and atomic
   - Rebase on main if needed

4. **Merging**
   - Maintainers will merge approved PRs
   - Use "Squash and merge" for feature PRs
   - Use "Rebase and merge" for simple fixes

## 🏗️ Project Structure

### Core Components

- **FastAPI Application** (`app/api.py`): REST API endpoints
- **CrewAI Agents** (`app/crew/`): Multi-agent code review system
- **Configuration** (`app/config.py`): Environment-based config
- **Schemas** (`app/schemas.py`): Request/response models
- **Utilities** (`app/utils.py`): Helper functions

### Testing Components

- **Unit Tests** (`tests/`): Test individual functions
- **Integration Tests**: Test API endpoints
- **Workflow Tests** (`.github/workflows/`): CI/CD testing

## 🎯 Development Workflow

### Feature Development

```bash
# Create feature branch
git checkout -b feat/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add awesome feature"

# Push to your fork
git push origin feat/your-feature-name

# Create pull request on GitHub
```

### Bug Fixes

```bash
# Create bugfix branch
git checkout -b fix/issue-123-bug-description

# Make changes
# ...

git commit -m "fix: resolve issue #123"
git push origin fix/issue-123-bug-description
```

## 📚 Additional Resources

- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [CrewAI Documentation](https://docs.crewai.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)

## 💬 Getting Help

- 💬 [GitHub Discussions](https://github.com/suryanshp1/code-reviewer-ci/discussions)
- 🐛 [Issue Tracker](https://github.com/suryanshp1/code-reviewer-ci/issues)
- 📧 Contact maintainers via GitHub

## 📜 Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project (see [LICENSE](LICENSE)).

---

**Thank you for contributing!** 🎉
