#!/usr/bin/env bash
################################################################################
# FILE: github_upload_simple.sh
# DESC: Simple, reliable GitHub upload script
# USAGE: ./github_upload_simple.sh [commit_message]
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

# Load GitHub token from .env file
if [[ -f .env ]]; then
    source .env
    log_info "Loaded environment from .env"
else
    log_error ".env file not found. Please create it with GH_TOKEN=your_token"
    exit 1
fi

# Validate token
if [[ -z "${GH_TOKEN:-}" ]]; then
    log_error "GH_TOKEN not found in .env file"
    exit 1
fi

# Get commit message from argument or use default
COMMIT_MSG="${1:-Auto-commit $(date '+%Y-%m-%d %H:%M:%S')}"

# Clean up remote URL (remove any existing tokens)
REMOTE_URL=$(git remote get-url origin)
CLEAN_URL=$(echo "$REMOTE_URL" | sed -E 's#https://[^@]+@#https://#')

# Set remote with token
AUTHENTICATED_URL="https://${GH_TOKEN}@${CLEAN_URL#https://}"
git remote set-url origin "$AUTHENTICATED_URL"

log_info "Repository: $(echo "$CLEAN_URL" | sed 's#https://github.com/##')"

# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
log_info "Current branch: $CURRENT_BRANCH"

# If we're not on main, ask user if they want to switch
if [[ "$CURRENT_BRANCH" != "main" ]]; then
    log_warn "You're on branch '$CURRENT_BRANCH', not 'main'"
    echo -n "Switch to main branch? (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        git checkout main 2>/dev/null || git checkout -b main
        CURRENT_BRANCH="main"
        log_info "Switched to main branch"
    fi
fi

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

# Push to remote
log_info "Pushing to GitHub..."
if git push origin "$CURRENT_BRANCH"; then
    log_success "Successfully pushed to GitHub!"
else
    log_error "Push failed"
    # Clean up remote URL
    git remote set-url origin "$CLEAN_URL"
    exit 1
fi

# Clean up remote URL (remove token for security)
git remote set-url origin "$CLEAN_URL"
log_info "Remote URL cleaned (token removed)"

# Show final status
log_success "Upload complete!"
log_info "Repository URL: $CLEAN_URL"
log_info "Branch: $CURRENT_BRANCH"

# Optional: Open repository in browser
if command -v xdg-open &> /dev/null; then
    echo -n "Open repository in browser? (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        xdg-open "$CLEAN_URL"
    fi
fi
