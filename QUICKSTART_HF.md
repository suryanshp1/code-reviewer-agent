# 🚀 Quick Start: Deploy to Hugging Face

Follow these steps to deploy your Code Reviewer CI Agent to Hugging Face Spaces for FREE!

## Prerequisites

- GitHub account with this repository
- Hugging Face account (sign up at https://huggingface.co)
- LLM API key (Groq or OpenAI)

## Setup Steps

### 1. Create Hugging Face Token

1. Go to https://huggingface.co/settings/tokens
2. Click "New token" → Name: `github-deployment` → Type: **Write**
3. Copy the token

### 2. Create Hugging Face Space

1. Go to https://huggingface.co/new-space
2. Space name: `code-reviewer-ci`
3. SDK: **Docker**
4. Create Space

### 3. Add GitHub Secrets

Go to: **GitHub Repository → Settings → Secrets → Actions**

Add 3 secrets:
- `HF_TOKEN` = your token from step 1
- `HF_USERNAME` = your HF username  
- `HF_SPACE_NAME` = `code-reviewer-ci`

### 4. Configure HF Space

Go to: **Your HF Space → Settings → Variables**

Add variables:
- `LLM_PROVIDER` = `groq`
- `REVIEW_API_KEY` = `(random secure string)`
- `GROQ_API_KEY` = `gsk_your_groq_key`

### 5. Deploy!

```bash
git add .
git commit -m "Deploy to Hugging Face"
git push origin main
```

✅ **Done!** GitHub Actions will automatically deploy to HF.

## Verify Deployment

```bash
# Health check
curl https://YOUR-USERNAME-YOUR-SPACE.hf.space/health
```

## Full Documentation

- **Detailed setup:** [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Troubleshooting:** See DEPLOYMENT.md#troubleshooting
- **Setup wizard:** Run `./scripts/setup_hf_deployment.sh`

---

**Need help?** See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete instructions.
