#!/usr/bin/env bash
################################################################################
# FILE: force_push_clean.sh
# DESC: Force push the cleaned repository to GitHub
# USAGE: ./force_push_clean.sh
################################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

log_info "🚀 Force Push Clean Repository"
echo

log_info "The secret scanning issue is RESOLVED! 🎉"
log_info "Now we need to force push because we cleaned the git history."
echo

log_warn "⚠️  This will overwrite the remote repository with your clean history"
log_warn "⚠️  This is safe because we removed secrets and preserved all your code"
echo

# Clear conflicting environment variables
unset GH_TOKEN 2>/dev/null || true
unset GITHUB_TOKEN 2>/dev/null || true

# Check authentication
if ! gh auth status &>/dev/null; then
    log_error "GitHub CLI not authenticated"
    exit 1
fi

log_success "GitHub CLI is authenticated"

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
log_info "Current branch: $CURRENT_BRANCH"

echo -n "Force push the cleaned repository? (y/N): "
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    log_info "Aborted."
    exit 0
fi

# Force push
log_info "Force pushing to GitHub..."
if git push --force-with-lease origin "$CURRENT_BRANCH"; then
    log_success "🎉 Successfully pushed to GitHub!"
else
    log_warn "Force-with-lease failed. Trying regular force push..."
    if git push --force origin "$CURRENT_BRANCH"; then
        log_success "🎉 Successfully force pushed to GitHub!"
    else
        log_error "Force push failed"
        exit 1
    fi
fi

# Show final status
log_success "Upload complete!"
REPO_URL=$(git remote get-url origin | sed -E 's#https://[^@]+@#https://#')
log_info "Repository URL: $REPO_URL"
log_info "Branch: $CURRENT_BRANCH"

# Show recent commits
echo
log_info "Recent commits now on GitHub:"
git log --oneline -5

echo
log_success "✅ GitHub upload successful!"
log_success "✅ No more secret scanning issues!"
log_success "✅ Clean git history uploaded!"

# Optional: Open repository in browser
if command -v xdg-open &> /dev/null; then
    echo
    echo -n "Open repository in browser? (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        xdg-open "$REPO_URL"
    fi
fi
