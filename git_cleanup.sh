#!/usr/bin/env bash
################################################################################
# FILE: git_cleanup.sh
# DESC: Clean up git repository and switch to main branch
# USAGE: ./git_cleanup.sh
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

log_info "Starting Git repository cleanup..."

# Show current status
log_info "Current status:"
git status --short
echo

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
log_info "Current branch: $CURRENT_BRANCH"

# Clean up remote URL first
REMOTE_URL=$(git remote get-url origin)
CLEAN_URL=$(echo "$REMOTE_URL" | sed -E 's#https://[^@]+@#https://#')
git remote set-url origin "$CLEAN_URL"
log_info "Cleaned remote URL"

# Stash any uncommitted changes
if ! git diff --quiet || ! git diff --cached --quiet; then
    log_info "Stashing uncommitted changes..."
    git stash push -m "Cleanup stash $(date '+%Y-%m-%d %H:%M:%S')"
    log_success "Changes stashed"
fi

# Switch to main branch (create if it doesn't exist)
if git show-ref --verify --quiet refs/heads/main; then
    log_info "Switching to existing main branch..."
    git checkout main
else
    log_info "Creating and switching to main branch..."
    git checkout -b main
fi

# If we were on a different branch, ask about merging changes
if [[ "$CURRENT_BRANCH" != "main" ]]; then
    log_warn "You were on branch '$CURRENT_BRANCH'"
    echo -n "Do you want to merge changes from '$CURRENT_BRANCH' into main? (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        log_info "Merging $CURRENT_BRANCH into main..."
        if git merge "$CURRENT_BRANCH" --no-edit; then
            log_success "Successfully merged $CURRENT_BRANCH into main"
            
            echo -n "Delete the old branch '$CURRENT_BRANCH'? (y/N): "
            read -r delete_response
            if [[ "$delete_response" =~ ^[Yy]$ ]]; then
                git branch -d "$CURRENT_BRANCH" 2>/dev/null || git branch -D "$CURRENT_BRANCH"
                log_success "Deleted branch $CURRENT_BRANCH"
            fi
        else
            log_error "Merge failed. You may need to resolve conflicts manually."
            exit 1
        fi
    fi
fi

# Apply stashed changes if any
if git stash list | grep -q "Cleanup stash"; then
    echo -n "Apply stashed changes? (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        git stash pop
        log_success "Applied stashed changes"
    fi
fi

# Show final status
log_success "Cleanup complete!"
log_info "Current branch: $(git rev-parse --abbrev-ref HEAD)"
log_info "Repository URL: $CLEAN_URL"
echo
log_info "Final status:"
git status --short

echo
log_info "You can now use './github_upload_simple.sh' to upload to GitHub"
