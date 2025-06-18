#!/usr/bin/env bash
################################################################################
# FILE: create_fresh_repo.sh
# DESC: Create a completely fresh repository without secret history
# USAGE: ./create_fresh_repo.sh
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

log_info "🆕 Creating Fresh Repository Without Secret History"
echo

# Get current directory name for new repo
CURRENT_DIR=$(basename "$PWD")
NEW_REPO_DIR="${CURRENT_DIR}-clean"

log_info "Current directory: $CURRENT_DIR"
log_info "New clean directory: $NEW_REPO_DIR"
echo

log_warn "This will create a completely new repository without any git history."
log_warn "All your code will be preserved, but git history will be fresh."
echo -n "Continue? (y/N): "
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    log_info "Aborted."
    exit 0
fi

# Create new directory
cd ..
if [[ -d "$NEW_REPO_DIR" ]]; then
    log_warn "Directory $NEW_REPO_DIR already exists."
    echo -n "Remove it and continue? (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        rm -rf "$NEW_REPO_DIR"
    else
        log_error "Cannot continue with existing directory."
        exit 1
    fi
fi

mkdir "$NEW_REPO_DIR"
cd "$NEW_REPO_DIR"

log_info "Created new directory: $NEW_REPO_DIR"

# Copy all files except git history and problematic files
log_info "Copying clean files..."
rsync -av --exclude='.git' \
          --exclude='68507cb0-f268-8008-898e-60359398f149*' \
          --exclude='*token*' \
          --exclude='*.log' \
          --exclude='logs/' \
          --exclude='prf_github_one_shot_uploader*.sh' \
          "../$CURRENT_DIR/" ./

log_success "Files copied successfully"

# Initialize new git repository
log_info "Initializing fresh git repository..."
git init
git branch -M main

# Create comprehensive .gitignore
log_info "Creating comprehensive .gitignore..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Secrets and credentials
.env*
*token*
*key*
*secret*
*password*
*credentials*
*api*key*

# Chat logs and temporary files
68507cb0-f268-8008-898e-60359398f149*
*chat*
*.log
logs/

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# Output directories
output/
temp/
tmp/

# Old upload scripts
prf_github_one_shot_uploader*.sh
EOF

# Add and commit all files
log_info "Adding all files to git..."
git add -A
git commit -m "Initial commit - clean repository without secrets"

log_success "🎉 Fresh repository created!"
echo
log_info "📁 Location: $(pwd)"
log_info "🌟 Clean git history with no secrets"
log_info "🔒 Comprehensive .gitignore in place"
echo
log_info "Next steps:"
log_info "1. cd $NEW_REPO_DIR"
log_info "2. Create new GitHub repository or update remote"
log_info "3. git remote add origin https://github.com/swipswaps/postcard-lister-clean.git"
log_info "4. git push -u origin main"
echo
log_warn "⚠️  Remember to:"
log_warn "  - Update any documentation with new repo location"
log_warn "  - Archive or delete the old repository if desired"
log_warn "  - Update any CI/CD or deployment scripts"
