# Deployment Guide: Hugging Face Spaces

This guide explains how to deploy the Code Reviewer CI Agent to Hugging Face Spaces with automatic GitHub synchronization.

## Prerequisites

- **GitHub Account** with repository access
- **Hugging Face Account** (free) - sign up at https://huggingface.co
- **API Keys**:
  - OpenAI API key OR Groq API key
  - Custom API key for your application (generate a secure random string)

## Step-by-Step Setup

### 1. Create Hugging Face Access Token

1. Go to https://huggingface.co/settings/tokens
2. Click **"New token"**
3. Name: `github-deployment`
4. Type: **Write** access
5. Click **"Generate token"**
6. **Copy the token** (you won't see it again!)

### 2. Create Hugging Face Space

1. Go to https://huggingface.co/new-space
2. Fill in details:
   - **Owner**: Your username
   - **Space name**: `code-reviewer-ci` (or your choice)
   - **License**: MIT
   - **Select SDK**: **Docker**
   - **Visibility**: Public or Private (your choice)
3. Click **"Create Space"**
4. **Don't add any files yet** - GitHub Actions will push them

### 3. Configure GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"** and add these three secrets:

| Secret Name | Value | Example |
|------------|-------|---------|
| `HF_TOKEN` | Your HF access token from step 1 | `hf_abcdefghijklmnop...` |
| `HF_USERNAME` | Your Hugging Face username | `johndoe` |
| `HF_SPACE_NAME` | Your Space name from step 2 | `code-reviewer-ci` |

### 4. Configure Hugging Face Space Variables

1. Go to your Space on Hugging Face
2. Click **Settings** tab
3. Scroll to **Variables and secrets** section
4. Add these environment variables:

**Required:**

| Variable | Value | Example |
|----------|-------|---------|
| `LLM_PROVIDER` | `openai` or `groq` | `groq` |
| `REVIEW_API_KEY` | Your custom API key | `my-secret-key-12345` |

**For OpenAI:**

| Variable | Value |
|----------|-------|
| `OPENAI_API_KEY` | `sk-proj-...` |
| `OPENAI_MODEL` | `gpt-4o-mini` |

**For Groq (Recommended for Free Tier):**

| Variable | Value |
|----------|-------|
| `GROQ_API_KEY` | `gsk_...` |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` |

**Optional (with defaults):**

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_PER_MINUTE` | `5` | Max requests per minute |
| `REQUEST_TIMEOUT_SECONDS` | `90` | Review timeout |
| `MAX_FINDINGS_PER_REVIEW` | `15` | Max findings per review |
| `DEBUG` | `false` | Enable debug logging |

### 5. Deploy to Hugging Face

Simply push to your `main` branch:

```bash
git add .
git commit -m "Deploy to Hugging Face"
git push origin main
```

**GitHub Actions will automatically:**

1. ✅ Run tests
2. ✅ Build optimized Docker image
3. ✅ Push to Hugging Face Space
4. ✅ Verify deployment health

### 6. Monitor Deployment

1. Go to your GitHub repository → **Actions** tab
2. Click on the latest workflow run
3. Watch the deployment progress
4. Check the deployment summary at the end

### 7. Verify Deployment

Once deployed, test your Space:

```bash
# Health check
curl https://YOUR-USERNAME-YOUR-SPACE.hf.space/health

# Should return:
# {"status":"healthy","version":"0.1.0",...}
```

### 8. Test Code Review

```bash
# Sample review request
curl -X POST https://YOUR-USERNAME-YOUR-SPACE.hf.space/review \
  -H "Authorization: Bearer YOUR_REVIEW_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "diff": "diff --git a/app.py b/app.py\n+def login(user, pwd):\n+    query = f\"SELECT * FROM users WHERE user='"'"'{user}'"'"'\"",
    "language": "python",
    "context": {"repo": "test/repo"}
  }'
```

## Architecture

```
┌──────────────────┐
│   Developer      │
│   git push main  │
└────────┬─────────┘
         │
         ▼
┌────────────────────────┐
│   GitHub Actions       │
│   • Test               │
│   • Build Docker       │
│   • Push to HF        │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│  Hugging Face Space    │
│  • Auto-rebuild        │
│  • Deploy container    │
│  • Expose on port 7860 │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│  Public API Endpoint   │
│  username-space.hf.space│
└────────────────────────┘
```

## Updating Your Deployment

Just push to `main`:

```bash
# Make changes
git add .
git commit -m "Update review logic"
git push origin main

# Deployment happens automatically!
```

## Common Issues

### Issue: "Space not found"

**Solution:** Make sure you created the Space on Hugging Face first (Step 2)

### Issue: "Authentication failed"

**Solution:** 
- Check `HF_TOKEN` secret is correct
- Ensure token has **Write** access
- Try regenerating the token

### Issue: "Deployment fails with Docker build error"

**Solution:**
- Check GitHub Actions logs for details
- Ensure all dependencies in `Dockerfile.hf` are correct
- Try pushing manually first to test

### Issue: "Space is sleeping / Cold start"

**Solution:**
- First request after inactivity takes ~60 seconds
- Consider upgrading to paid tier for always-on
- Or implement a cron job to ping `/health` every 30 minutes

### Issue: "Review timeout"

**Solution:**
- Increase `REQUEST_TIMEOUT_SECONDS` in Space variables
- Use Groq instead of OpenAI (faster)
- Reduce diff size

## Cost Considerations

### Hosting (FREE ✅)
- Hugging Face Spaces CPU-basic tier is **free forever**
- Limitations: 2 vCPU, 16GB RAM, sleeps after 48h inactivity

### LLM API Costs (YOU PAY 💰)

**OpenAI gpt-4o-mini:**
- ~$0.002-0.05 per review
- Good for production

**Groq llama-3.3-70b-versatile:**
- **FREE** tier available
- Faster than OpenAI
- **Recommended for free tier**

**Monthly estimate (100 reviews/month):**
- OpenAI: ~$2-5
- Groq: $0 (within free limits)

## Monitoring

### View Application Logs

1. Go to your Space on Hugging Face
2. Click **Logs** tab
3. View real-time logs

### View Deployment Status

- GitHub Actions tab shows all deployments
- Green checkmark = successful
- Red X = failed (check logs)

## Manual Deployment (Alternative)

If you prefer manual deployment without CI/CD:

```bash
# Clone your Space
git clone https://huggingface.co/spaces/YOUR-USERNAME/YOUR-SPACE

# Copy files
cd YOUR-SPACE
cp -r ../code-reviewer-ci-agent/app .
cp ../code-reviewer-ci-agent/Dockerfile.hf Dockerfile
cp ../code-reviewer-ci-agent/README_HF.md README.md

# Push to HF
git add .
git commit -m "Manual deployment"
git push
```

## Security Best Practices

1. ✅ **Never commit API keys** - Use HF Space variables
2. ✅ **Use strong `REVIEW_API_KEY`** - Generate random 32+ char string
3. ✅ **Set rate limits** - Prevent abuse
4. ✅ **Monitor usage** - Check LLM API costs regularly
5. ✅ **Use private Space** - If handling sensitive code

## Next Steps

1. ✅ Set up GitHub Actions integration (Step 5-7)
2. ✅ Configure webhook for automatic PR reviews
3. ✅ Monitor and optimize costs
4. ✅ Consider upgrading to paid tier for production use

## Support

- **GitHub Issues**: Report bugs or feature requests
- **Hugging Face Discussions**: Ask questions on your Space
- **Documentation**: See README.md for full API docs

---

**Happy Reviewing! 🤖**
