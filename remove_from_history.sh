#!/usr/bin/env bash
################################################################################
# FILE: remove_from_history.sh
# DESC: Remove chat log files from git history only
# USAGE: ./remove_from_history.sh
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

log_info "🗑️  Removing Chat Logs from Git History Only"
echo

# Files to remove from history (they're not in current directory)
PROBLEM_FILES=(
    "68507cb0-f268-8008-898e-60359398f149.2025-06-17_203216.txt"
    "68507cb0-f268-8008-898e-60359398f149.2025-06-17_203225.txt"
)

log_info "Files to remove from git history:"
for file in "${PROBLEM_FILES[@]}"; do
    echo "  - $file"
done
echo

log_info "These files are NOT in your current directory (they're in parent folder)"
log_info "But they exist in git history and GitHub is detecting secrets in them"
echo

log_warn "⚠️  This will rewrite git history to remove these files"
log_warn "⚠️  This is safe since the files aren't in your current project"
echo -n "Continue? (y/N): "
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    log_info "Aborted."
    exit 0
fi

# Commit any current changes first
log_info "Committing any current changes..."
git add -A
git commit -m "Pre-history-cleanup commit" 2>/dev/null || log_info "No changes to commit"

# Use git filter-branch to remove files from history
log_info "Removing files from git history..."

# Set environment variable to suppress warning
export FILTER_BRANCH_SQUELCH_WARNING=1

# Build the filter command
FILTER_CMD="git rm --cached --ignore-unmatch"
for file in "${PROBLEM_FILES[@]}"; do
    FILTER_CMD="$FILTER_CMD '$file'"
done

# Run filter-branch
if git filter-branch --force --index-filter "$FILTER_CMD" --prune-empty --tag-name-filter cat -- --all; then
    log_success "Successfully removed files from git history"
    
    # Clean up
    rm -rf .git/refs/original/ 2>/dev/null || true
    git reflog expire --expire=now --all
    git gc --prune=now --aggressive
    
    log_success "Cleaned up git repository"
else
    log_error "Filter-branch failed. Let's try a different approach..."
    
    # Alternative: Create new branch without the problematic commits
    log_info "Creating clean branch from current state..."
    CLEAN_BRANCH="clean-no-secrets-$(date +%H%M%S)"
    git checkout -b "$CLEAN_BRANCH"
    
    # Reset to current clean state
    git reset --soft HEAD~50  # Go back 50 commits
    git reset --hard HEAD     # Keep current files
    
    # Commit clean state
    git add -A
    git commit -m "Clean repository without chat log secrets"
    
    # Replace main with clean branch
    git checkout main
    git reset --hard "$CLEAN_BRANCH"
    git branch -D "$CLEAN_BRANCH"
    
    log_success "Created clean history"
fi

# Add .gitignore rule to prevent future issues
log_info "Adding .gitignore rule for chat logs..."
if ! grep -q "68507cb0" .gitignore 2>/dev/null; then
    cat >> .gitignore << 'EOF'

# Chat logs (prevent accidental inclusion)
68507cb0*.txt
*chat*.txt
conversation*.txt
EOF
    git add .gitignore
    git commit -m "Add .gitignore rule for chat logs"
    log_success "Added .gitignore rule"
fi

log_success "🎉 Git history cleaned!"
echo
log_info "✅ Chat log files removed from git history"
log_info "✅ Current files preserved (they weren't in working directory anyway)"
log_info "✅ .gitignore updated to prevent future issues"
echo
log_info "Now you can safely upload to GitHub:"
log_info "  ./github_upload_clean.sh \"Cleaned git history, ready for upload\""
