#!/bin/bash

# Simple, proven GitHub push script
# No over-engineering, just what works

echo "🚀 Simple GitHub Push"
echo "===================="

# Load environment
if [ -f .env.local ]; then
    source .env.local
    echo "✅ Loaded environment"
else
    echo "❌ No .env.local file found"
    exit 1
fi

# Check if we have a token
if [ -z "$GH_TOKEN" ]; then
    echo "❌ No GH_TOKEN found in .env.local"
    exit 1
fi

echo "🔑 Token loaded: ${GH_TOKEN:0:10}..."

# Get commit message
COMMIT_MSG="${1:-Solar panel catalog update}"
echo "📝 Commit message: $COMMIT_MSG"

# Show current status
echo ""
echo "📊 Current Status:"
git status --short

# Add all changes
echo ""
echo "📦 Adding changes..."
git add .

# Commit changes
echo "💾 Committing..."
git commit -m "$COMMIT_MSG"

# Show what we're about to push
echo ""
echo "📋 About to push:"
git log --oneline -3

# Configure remote with token
REPO_URL=$(git remote get-url origin)
if [[ "$REPO_URL" == *"@github.com"* ]]; then
    echo "✅ Remote already has authentication"
else
    echo "🔧 Adding token to remote URL..."
    CLEAN_URL=$(echo "$REPO_URL" | sed 's|https://github.com/|https://'"$GH_TOKEN"'@github.com/|')
    git remote set-url origin "$CLEAN_URL"
fi

# Push with full output
echo ""
echo "📤 Pushing to GitHub..."
echo "🌐 ALL NETWORK MESSAGES WILL BE SHOWN:"
echo "======================================"

# Simple git push with ALL output visible
git push origin $(git branch --show-current) 2>&1

RESULT=$?

# Clean up token from remote
echo ""
echo "🔒 Cleaning up token from remote..."
CLEAN_URL=$(echo "$REPO_URL" | sed 's|https://.*@github.com/|https://github.com/|')
git remote set-url origin "$CLEAN_URL"

# Show result
echo ""
if [ $RESULT -eq 0 ]; then
    echo "✅ SUCCESS: Push completed!"
    echo "🌐 Check: https://github.com/swipswaps/postcard-lister"
else
    echo "❌ FAILED: Push failed with exit code $RESULT"
    echo "💡 Check the output above for details"
fi

echo ""
echo "🕐 Completed: $(date)"
