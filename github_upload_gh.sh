#!/usr/bin/env bash
################################################################################
# FILE: github_upload_gh.sh
# DESC: GitHub upload using gh CLI (primary) with git fallback
# USAGE: ./github_upload_gh.sh [commit_message]
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

# Get commit message from argument or use default
COMMIT_MSG="${1:-Auto-commit $(date '+%Y-%m-%d %H:%M:%S')}"

# Check if gh CLI is available
if command -v gh &> /dev/null; then
    log_info "Using GitHub CLI (gh) - preferred method"
    USE_GH=true
else
    log_warn "GitHub CLI (gh) not found, falling back to git with token"
    USE_GH=false
fi

# Load GitHub token from .env files (for git fallback)
if [[ "$USE_GH" == false ]]; then
    for ENV_FILE in .env.local .env; do
        if [[ -f "$ENV_FILE" ]]; then
            source "$ENV_FILE"
            log_info "Loaded environment from $ENV_FILE"
            break
        fi
    done

    # Validate token for git fallback
    if [[ -z "${GH_TOKEN:-}" ]]; then
        log_error "GH_TOKEN not found in .env.local or .env file"
        log_error "Please create .env.local with: GH_TOKEN=\"your_token_here\""
        exit 1
    fi
fi

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

# Push using gh CLI or git fallback
if [[ "$USE_GH" == true ]]; then
    log_info "Pushing using GitHub CLI..."
    
    # Check if gh is authenticated
    if ! gh auth status &>/dev/null; then
        log_warn "GitHub CLI not authenticated. Running gh auth login..."
        gh auth login
    fi
    
    # Push using gh
    if git push origin "$CURRENT_BRANCH"; then
        log_success "Successfully pushed using GitHub CLI!"
    else
        log_error "Push failed using GitHub CLI"
        exit 1
    fi
else
    log_info "Pushing using git with token authentication..."
    
    # Clean up remote URL and add token
    REMOTE_URL=$(git remote get-url origin)
    CLEAN_URL=$(echo "$REMOTE_URL" | sed -E 's#https://[^@]+@#https://#')
    
    # Remove quotes from token if present
    CLEAN_TOKEN="${GH_TOKEN//\"/}"
    
    # Set remote with token
    AUTHENTICATED_URL="https://${CLEAN_TOKEN}@${CLEAN_URL#https://}"
    git remote set-url origin "$AUTHENTICATED_URL"
    
    log_info "Repository: $(echo "$CLEAN_URL" | sed 's#https://github.com/##')"
    
    # Push with token
    if git push origin "$CURRENT_BRANCH"; then
        log_success "Successfully pushed using git with token!"
    else
        log_error "Push failed using git with token"
        # Clean up remote URL
        git remote set-url origin "$CLEAN_URL"
        exit 1
    fi
    
    # Clean up remote URL (remove token for security)
    git remote set-url origin "$CLEAN_URL"
    log_info "Remote URL cleaned (token removed)"
fi

# Show final status
log_success "Upload complete!"
REPO_URL=$(git remote get-url origin | sed -E 's#https://[^@]+@#https://#')
log_info "Repository URL: $REPO_URL"
log_info "Branch: $CURRENT_BRANCH"

# Optional: Open repository in browser
if command -v xdg-open &> /dev/null; then
    echo -n "Open repository in browser? (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        xdg-open "$REPO_URL"
    fi
fi
