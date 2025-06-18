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

# Check token format and provide guidance
if [[ "$GH_TOKEN" =~ ^ghp_ ]]; then
    log_info "Using Personal Access Token (classic)"
elif [[ "$GH_TOKEN" =~ ^github_pat_ ]]; then
    log_info "Using Fine-grained Personal Access Token"
elif [[ "$GH_TOKEN" =~ ^ghs_ ]]; then
    log_info "Using GitHub App token"
else
    log_warn "Token format not recognized. Expected format: ghp_... or github_pat_..."
    log_info "Token length: ${#GH_TOKEN} characters"
    log_info "Please ensure you're using a valid GitHub Personal Access Token"
    echo -n "Continue anyway? (y/N): "
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        log_info "Aborted. Please check your token in .env file"
        exit 1
    fi
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
log_info "Using token: ${GH_TOKEN:0:10}..."

# Try push with detailed error output
PUSH_OUTPUT=$(git push origin "$CURRENT_BRANCH" 2>&1)
PUSH_EXIT=$?

if [[ $PUSH_EXIT -eq 0 ]]; then
    log_success "Successfully pushed to GitHub!"
else
    log_error "Push failed with exit code: $PUSH_EXIT"
    log_error "Git output:"
    echo "$PUSH_OUTPUT"

    # Check for common issues
    if echo "$PUSH_OUTPUT" | grep -q "Authentication failed"; then
        log_error "Authentication failed. Possible issues:"
        log_error "1. Token is expired or invalid"
        log_error "2. Token doesn't have 'repo' permissions"
        log_error "3. Repository doesn't exist or you don't have access"
        log_info "Please check your token at: https://github.com/settings/tokens"
    elif echo "$PUSH_OUTPUT" | grep -q "remote: Repository not found"; then
        log_error "Repository not found. Please check:"
        log_error "1. Repository name is correct"
        log_error "2. You have access to the repository"
        log_error "3. Repository exists at: $CLEAN_URL"
    fi

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
