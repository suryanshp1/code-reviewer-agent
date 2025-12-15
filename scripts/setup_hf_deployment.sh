#!/bin/bash
# Quick Start Script for Hugging Face Deployment Setup

set -e

echo "🚀 Hugging Face Deployment Quick Start"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "app/api.py" ]; then
    echo "❌ Error: Not in project root directory"
    echo "Please run this script from the code-reviewer-ci-agent directory"
    exit 1
fi

# Step 1: Check GitHub repository
echo "📋 Step 1: Checking GitHub repository..."
if git remote get-url origin > /dev/null 2>&1; then
    REPO_URL=$(git remote get-url origin)
    echo "✅ GitHub repository configured: $REPO_URL"
else
    echo "❌ No GitHub remote found"
    echo "Please initialize git and add GitHub remote first:"
    echo "  git init"
    echo "  git remote add origin https://github.com/YOUR-USERNAME/code-reviewer-ci-agent.git"
    exit 1
fi
echo ""

# Step 2: Check if files exist
echo "📋 Step 2: Verifying deployment files..."
FILES=(
    ".github/workflows/deploy-huggingface.yml"
    "Dockerfile.hf"
    "README_HF.md"
    ".spacesignore"
    "DEPLOYMENT.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file - MISSING!"
        exit 1
    fi
done
echo ""

# Step 3: Instructions for HF setup
echo "📋 Step 3: Next Steps - Hugging Face Setup"
echo "=========================================="
echo ""
echo "1️⃣  CREATE HUGGING FACE TOKEN:"
echo "   Go to: https://huggingface.co/settings/tokens"
echo "   - Click 'New token'"
echo "   - Name: github-deployment"
echo "   - Type: Write access"
echo "   - Copy the token"
echo ""

echo "2️⃣  CREATE HUGGING FACE SPACE:"
echo "   Go to: https://huggingface.co/new-space"
echo "   - Space name: code-reviewer-ci (or your choice)"
echo "   - SDK: Docker"
echo "   - Click 'Create Space'"
echo ""

echo "3️⃣  ADD GITHUB SECRETS:"
echo "   Go to: GitHub Repo → Settings → Secrets → Actions"
echo "   Add these 3 secrets:"
echo "   - HF_TOKEN: (your HF token from step 1)"
echo "   - HF_USERNAME: (your HF username)"
echo "   - HF_SPACE_NAME: (your space name from step 2)"
echo ""

echo "4️⃣  CONFIGURE HF SPACE VARIABLES:"
echo "   Go to: Your HF Space → Settings → Variables"
echo "   Add these variables:"
echo "   - LLM_PROVIDER: groq (or openai)"
echo "   - REVIEW_API_KEY: (generate a secure random string)"
echo "   - GROQ_API_KEY: gsk_... (or OPENAI_API_KEY)"
echo ""

echo "5️⃣  DEPLOY:"
echo "   Just push to main branch:"
echo "   $ git add ."
echo "   $ git commit -m 'Deploy to Hugging Face'"
echo "   $ git push origin main"
echo ""
echo "   GitHub Actions will automatically deploy to HF!"
echo ""

echo "📖 For detailed instructions, see: DEPLOYMENT.md"
echo ""

read -p "Have you completed steps 1-4? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Ready to deploy!"
    echo "Run: git push origin main"
    echo ""
    echo "Monitor deployment at:"
    echo "  GitHub: https://github.com/$(git config user.name || echo "YOUR-USERNAME")/$(basename $(git rev-parse --show-toplevel))/actions"
else
    echo ""
    echo "ℹ️  Complete the setup steps above, then run this script again"
    echo "Or see DEPLOYMENT.md for detailed instructions"
fi

echo ""
echo "✨ Setup complete! Good luck with your deployment!"
