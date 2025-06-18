#!/usr/bin/env bash
################################################################################
# FILE: github_upload_clean.sh
# DESC: Clean GitHub upload using gh CLI (avoiding token conflicts)
# USAGE: ./github_upload_clean.sh [commit_message]
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

# Check if we're in a git repository
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    log_error "Not inside a Git repository"
    exit 1
fi

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    log_error "GitHub CLI (gh) not found. Please install it first."
    exit 1
fi

# Get commit message from argument or use default
COMMIT_MSG="${1:-Auto-commit $(date '+%Y-%m-%d %H:%M:%S')}"

# Clear conflicting environment variables
unset GH_TOKEN
unset GITHUB_TOKEN

log_info "Using GitHub CLI (gh) with keyring authentication"

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
log_info "Current branch: $CURRENT_BRANCH"

# Add all changes
log_info "Adding all changes..."
git add -A

# Check if there are changes to commit
if git diff --cached --quiet; then
    log_info "No changes to commit"
else
    log_info "Committing changes..."
    git commit -m "$COMMIT_MSG"
    log_success "Changes committed: $COMMIT_MSG"
fi

# Check gh authentication status
log_info "Checking GitHub CLI authentication..."
if gh auth status &>/dev/null; then
    log_success "GitHub CLI is authenticated"
else
    log_error "GitHub CLI not authenticated. Please run: gh auth login"
    exit 1
fi

# Push using git (gh CLI will handle authentication)
log_info "Pushing to GitHub..."
if git push origin "$CURRENT_BRANCH"; then
    log_success "Successfully pushed to GitHub!"
else
    log_error "Push failed"
    exit 1
fi

# Show final status
log_success "Upload complete!"
REPO_URL=$(git remote get-url origin | sed -E 's#https://[^@]+@#https://#')
log_info "Repository URL: $REPO_URL"
log_info "Branch: $CURRENT_BRANCH"

# Show recent commits
log_info "Recent commits:"
git log --oneline -5

# Optional: Open repository in browser
if command -v xdg-open &> /dev/null; then
    echo -n "Open repository in browser? (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        xdg-open "$REPO_URL"
    fi
fi
