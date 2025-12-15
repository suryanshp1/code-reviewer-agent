# 🤖 Code Reviewer CI Agent

**Production-ready AI-powered code review using CrewAI multi-agent framework**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Automatically review pull requests using a multi-agent AI system powered by CrewAI. Get instant, actionable feedback on security, performance, code quality, and maintainability.

## ✨ Features

- **Multi-Agent Architecture**: 5 specialized AI agents analyzing different aspects of your code
- **Automated PR Reviews**: GitHub Actions integration for seamless CI/CD
- **Structured Output**: JSON-based findings with severity levels and actionable suggestions
- **Production-Ready**: Ray Serve deployment for horizontal scaling
- **Guardrails**: Built-in validation to prevent hallucinations and ensure quality
- **Flexible LLM Support**: Works with OpenAI GPT-4o or Groq Llama models
- **Self-Hosted**: Run on your own infrastructure with Docker

## 📋 Table of Contents

- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [GitHub Actions Setup](#github-actions-setup)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

## 🏗️ Architecture

```
┌─────────────────────┐
│   GitHub PR/Push    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  GitHub Actions     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   FastAPI Gateway   │  ← Authentication, Rate Limiting
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Ray Serve         │  ← Horizontal Scaling (Optional)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│         CrewAI Multi-Agent System        │
│  ┌─────────────────────────────────┐   │
│  │  Parallel Phase                  │   │
│  │  • Code Analyzer                 │   │
│  │  • Security Reviewer             │   │
│  │  • Performance Reviewer          │   │
│  │  • Style & Maintainability       │   │
│  └─────────────┬───────────────────┘   │
│                │                        │
│                ▼                        │
│  ┌─────────────────────────────────┐   │
│  │  Sequential Phase               │   │
│  │  • Review Synthesizer           │   │
│  └─────────────────────────────────┘   │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────┐
│    Guardrails       │  ← Validation, Deduplication
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Structured Review  │  ← JSON + Markdown
└─────────────────────┘
```

### Agent Responsibilities

| Agent | Role | Focus Areas |
|-------|------|-------------|
| **Code Analyzer** | Senior Software Engineer | Logic, complexity, architecture, design patterns |
| **Security Reviewer** | AppSec Engineer | Vulnerabilities, injection, auth issues, secrets |
| **Performance Reviewer** | Performance Engineer | N+1 queries, algorithmic complexity, resource usage |
| **Style Reviewer** | Staff Engineer | Naming, maintainability, code smells, SOLID principles |
| **Review Synthesizer** | Tech Lead | Merge findings, prioritize, create final report |

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)
- OpenAI API key OR Groq API key

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/code-reviewer-ci-agent.git
cd code-reviewer-ci-agent
```

2. **Set up environment**

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# Minimum required:
# - LLM_PROVIDER (openai or groq)
# - OPENAI_API_KEY or GROQ_API_KEY
# - REVIEW_API_KEY (create a secure random string)
```

3. **Install dependencies**

```bash
# Using pip
pip install -e .

# Or using Docker
docker-compose build
```

4. **Run the service**

```bash
# Development mode (direct FastAPI)
uvicorn app.api:app --reload

# Production mode (Docker)
docker-compose up

# Production mode with Ray Serve
docker-compose --profile production up
```

5. **Test the API**

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "ray_serve_enabled": false,
  "llm_provider": "openai"
}
```

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_PROVIDER` | Yes | `openai` | LLM provider: `openai` or `groq` |
| `OPENAI_API_KEY` | If using OpenAI | - | OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model name |
| `GROQ_API_KEY` | If using Groq | - | Groq API key |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq model name |
| `REVIEW_API_KEY` | Yes | - | API key for authentication |
| `RATE_LIMIT_PER_MINUTE` | No | `10` | Max requests per minute |
| `MAX_FINDINGS_PER_REVIEW` | No | `20` | Max findings to return |
| `REQUEST_TIMEOUT_SECONDS` | No | `120` | Review timeout in seconds |
| `ENABLE_RAY_SERVE` | No | `false` | Enable Ray Serve deployment |

### Model Recommendations

| Provider | Model | Cost/1M tokens | Speed | Quality | Best For |
|----------|-------|----------------|-------|---------|----------|
| OpenAI | gpt-4o | $5.00 | Fast | Excellent | Production |
| OpenAI | gpt-4o-mini | $0.15 | Very Fast | Good | Development, Cost-sensitive |
| Groq | llama-3.3-70b-versatile | Free* | Ultra Fast | Good | High volume |

*Groq has usage limits on free tier

## 🔧 GitHub Actions Setup

### 1. Add Repository Secrets

Go to your repository → Settings → Secrets and variables → Actions

Add these secrets:
- `REVIEW_API_URL`: Your deployed API URL (e.g., `https://your-domain.com`)
- `REVIEW_API_KEY`: The same key from your `.env` file

### 2. Enable Workflow Permissions

Go to Settings → Actions → General → Workflow permissions

- Select "Read and write permissions"
- Check "Allow GitHub Actions to create and approve pull requests"

### 3. Create a Test PR

The workflow is already included at `.github/workflows/code-review.yml`. Create a PR to test it!

### Example Review Comment

The workflow will post comments like this:

> ## 🤖 AI Code Review
> 
> **Summary:** Found 2 security issues and 1 performance concern
> **Quality Score:** 7.5/10
> 
> ### 🔴 Critical Issues
> 
> - **Security** in `app/auth.py:24`
>   > SQL injection vulnerability in user authentication
>   > **Suggestion:** Use parameterized queries instead of string concatenation
> 
> ### 🟡 Medium Severity
> 
> - **Performance** in `app/db.py:45`
>   > N+1 query pattern detected in user retrieval
>   > **Suggestion:** Use eager loading or batch queries

## 📚 API Documentation

### POST `/review`

Review code changes using AI agents.

**Request:**
```json
{
  "diff": "diff --git a/main.py b/main.py...",
  "language": "python",
  "context": {
    "repo": "org/repo",
    "commit_sha": "abc123",
    "pr_number": 42,
    "author": "username"
  }
}
```

**Headers:**
```
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

**Response:**
```json
{
  "summary": "Found 3 issues...",
  "score": 7.5,
  "findings": [
    {
      "category": "security",
      "severity": "high",
      "file": "app/auth.py",
      "line": 24,
      "message": "SQL injection vulnerability",
      "suggestion": "Use parameterized queries"
    }
  ],
  "metadata": {
    "execution_time_ms": 4523,
    "tokens_used": 12453,
    "agent_count": 5,
    "guardrails_applied": ["file_validation", "max_findings"],
    "model": "gpt-4o-mini"
  }
}
```

### GET `/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "ray_serve_enabled": false,
  "llm_provider": "openai"
}
```

## 🐳 Deployment

### Docker (Simple)

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Docker with Ray Serve (Production)

```bash
# Build and run with Ray Serve
docker-compose --profile production up -d

# Access Ray dashboard at http://localhost:8265
```

### Manual Deployment

```bash
# Install dependencies
pip install -e .

# Run with Uvicorn
uvicorn app.api:app --host 0.0.0.0 --port 8000 --workers 4

# Or with Ray Serve
python -m app.serve
```

### Cloud Deployment

The application can be deployed to:

- **AWS**: ECS + Fargate with Application Load Balancer
- **GCP**: Cloud Run or GKE
- **Azure**: Container Apps or AKS
- **Fly.io**: Simple deployment with `fly.toml`

Example for Fly.io:

```bash
fly launch
fly secrets set OPENAI_API_KEY=sk-...
fly secrets set REVIEW_API_KEY=your-key
fly deploy
```

## 💻 Development

### Project Structure

```
code-reviewer-ci-agent/
├── app/
│   ├── api.py                 # FastAPI gateway
│   ├── schemas.py             # Pydantic models
│   ├── config.py              # Configuration
│   ├── utils.py               # Utilities
│   ├── guardrails.py          # Validation layer
│   ├── serve.py               # Ray Serve deployment
│   └── crew/
│       ├── agents.yaml        # Agent definitions
│       ├── tasks.yaml         # Task definitions
│       └── crew.py            # Crew orchestration
├── tests/                     # Test suite
├── .github/workflows/         # GitHub Actions
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_api.py
```

### Code Quality

```bash
# Format code
black app tests

# Lint
ruff check app tests

# Type check
mypy app
```

## 🐛 Troubleshooting

### Issue: "Review failed: Invalid API key"

**Solution:** Check that your `OPENAI_API_KEY` or `GROQ_API_KEY` is correctly set in `.env`

### Issue: "Review timed out after 120 seconds"

**Solution:** 
- Increase `REQUEST_TIMEOUT_SECONDS` in `.env`
- Try using a faster model (gpt-4o-mini or Groq)
- Reduce diff size by reviewing smaller changes

### Issue: "Rate limit exceeded"

**Solution:**
- Increase `RATE_LIMIT_PER_MINUTE` in `.env`
- Deploy multiple Ray Serve replicas
- Use a different API key

### Issue: "Too many findings"

**Solution:** Increase `MAX_FINDINGS_PER_REVIEW` in `.env` (not recommended) or focus on critical issues only

### Debugging

Enable debug mode:

```bash
# In .env
DEBUG=true
LOG_LEVEL=DEBUG
```

View detailed logs:

```bash
# Docker
docker-compose logs -f api

# Direct run
tail -f logs/app.log
```

## 📊 Performance

Expected performance metrics:

| Metric | Value |
|--------|-------|
| Avg review time | 15-45 seconds |
| Max diff size | 1 MB |
| Concurrent requests | 10 per replica |
| Token usage | ~10K per review |
| Cost per review | $0.002 - $0.15 |

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

- Built with [CrewAI](https://www.crewai.com/)
- Powered by [FastAPI](https://fastapi.tiangolo.com/)
- Scaled with [Ray Serve](https://docs.ray.io/en/latest/serve/index.html)

---

**Made with ❤️ for better code reviews**
