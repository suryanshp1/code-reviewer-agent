---
title: Code Reviewer CI Agent
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
---

# 🤖 AI Code Reviewer Agent

**Production-ready AI-powered code review using CrewAI multi-agent framework**

Automatically review code changes with specialized AI agents analyzing security, performance, code quality, and maintainability.

## 🚀 Quick Start

### API Endpoints

#### Health Check
```bash
curl https://YOUR-USERNAME-YOUR-SPACE.hf.space/health
```

#### Code Review
```bash
curl -X POST https://YOUR-USERNAME-YOUR-SPACE.hf.space/review \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "diff": "diff --git a/app.py b/app.py\n+def login(user, pwd):\n+    query = f\"SELECT * FROM users WHERE user='\''{user}'\''\"",
    "language": "python",
    "context": {
      "repo": "myorg/myrepo",
      "pr_number": 123
    }
  }'
```

## 📊 Multi-Agent Architecture

This system uses **5 specialized AI agents** working in parallel:

| Agent | Role | Focus |
|-------|------|-------|
| 🔍 **Code Analyzer** | Senior Engineer | Logic, complexity, architecture |
| 🔒 **Security Reviewer** | AppSec Engineer | Vulnerabilities, injection attacks |
| ⚡ **Performance Reviewer** | Performance Engineer | N+1 queries, algorithmic complexity |
| ✨ **Style Reviewer** | Staff Engineer | Naming, maintainability, SOLID |
| 📝 **Review Synthesizer** | Tech Lead | Prioritization, final report |

## ⚙️ Configuration

### Environment Variables

**Required** (set in Space Settings → Variables):

- `LLM_PROVIDER` - `openai` or `groq`
- `OPENAI_API_KEY` or `GROQ_API_KEY` - Your LLM API key
- `REVIEW_API_KEY` - API key for authenticating requests

**Optional:**

- `RATE_LIMIT_PER_MINUTE` - Max requests per minute (default: 5)
- `REQUEST_TIMEOUT_SECONDS` - Review timeout (default: 90)
- `MAX_FINDINGS_PER_REVIEW` - Max findings to return (default: 15)

### Recommended LLM Configuration

**For Free Tier:**
```bash
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

**For Production:**
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk_your_key_here
OPENAI_MODEL=gpt-4o-mini
```

## 📝 API Response Format

```json
{
  "summary": "Found 2 security issues and 1 performance concern",
  "score": 7.5,
  "findings": [
    {
      "category": "security",
      "severity": "high",
      "file": "app/auth.py",
      "line": 24,
      "message": "SQL injection vulnerability detected",
      "suggestion": "Use parameterized queries instead of string interpolation"
    }
  ],
  "metadata": {
    "execution_time_ms": 15234,
    "tokens_used": 12453,
    "agent_count": 5,
    "model": "gpt-4o-mini"
  }
}
```

## 🔧 GitHub Integration

Integrate with your CI/CD pipeline:

```yaml
# .github/workflows/code-review.yml
- name: AI Code Review
  run: |
    curl -X POST https://YOUR-SPACE.hf.space/review \
      -H "Authorization: Bearer ${{ secrets.REVIEW_API_KEY }}" \
      -d @review_request.json
```

## 📈 Performance

| Metric | Value |
|--------|-------|
| Avg review time | 15-45 seconds |
| Max diff size | 1 MB |
| Token usage | ~10K per review |
| Cost per review | $0.002 - $0.15 |

## ⚠️ Limitations on Free Tier

- **Single worker**: Can handle 1 request at a time
- **Cold starts**: First request after sleep takes ~60 seconds
- **Resource limits**: 2 vCPU, 16GB RAM
- **Timeouts**: Long reviews may timeout (increase `REQUEST_TIMEOUT_SECONDS`)

## 🔒 Security

- API key authentication required for `/review` endpoint
- Rate limiting prevents abuse
- No data persistence (stateless reviews)
- Secrets managed via HF Space settings

## 📚 Documentation

Full documentation: [GitHub Repository](https://github.com/YOUR-USERNAME/code-reviewer-ci-agent)

## 💡 Tips

1. **Use Groq for free tier** - Faster and free API calls
2. **Keep diffs small** - Large changes may timeout
3. **Set rate limits** - Prevent quota exhaustion
4. **Monitor usage** - Track LLM API costs

## 🙏 Credits

Built with:
- [CrewAI](https://www.crewai.com/) - Multi-agent orchestration
- [FastAPI](https://fastapi.tiangolo.com/) - API framework
- [OpenAI](https://openai.com/) / [Groq](https://groq.com/) - LLM providers

---

**Made with ❤️ for better code reviews**
