#!/usr/bin/env bash
################################################################################
# FILE: .install/install_gh_cli.sh
# DESC: Install GitHub CLI (gh) on Fedora with PRF-composite compliance
# SPEC: PRF‑COMPOSITE‑2025‑04‑22‑A (P01–P25)
################################################################################

set -euo pipefail
IFS=$'\n\t'

echo_info() { echo -e "\033[1;34m[INFO]\033[0m  $1"; }
echo_ok()   { echo -e "\033[1;32m[SUCCESS]\033[0m  $1"; }
echo_err()  { echo -e "\033[1;31m[ERROR]\033[0m  $1"; }

# ─── [BLOCK: FEDORA CHECK] ─────────────────────────────────────────────────────
# WHAT: Ensure script is only run on Fedora
# WHY: Script uses Fedora-specific package manager `dnf`
# FAIL: Exit if not Fedora
# UX: Clear explanation
# DEBUG: Checks /etc/os-release content
if ! grep -q '^ID=fedora' /etc/os-release; then
  echo_err "This installer supports Fedora-based systems only."
  exit 1
fi

# ─── [BLOCK: ALREADY INSTALLED CHECK] ─────────────────────────────────────────
# WHAT: Skip installation if `gh` is already available
# WHY: Avoid redundant installs
# FAIL: Not applicable
# UX: Reports existing version
# DEBUG: Uses `command -v`
if command -v gh >/dev/null; then
  echo_ok "GitHub CLI (gh) already installed: $(gh --version | head -n1)"
  exit 0
fi

# ─── [BLOCK: INSTALL DEPENDENCIES] ─────────────────────────────────────────────
# WHAT: Install dnf plugin to allow adding GitHub repository
# WHY: `dnf-plugins-core` provides config-manager
# FAIL: Abort on failure to install plugin
# UX: Logs visible
# DEBUG: Checks for plugin presence after install
echo_info "Installing dnf-plugins-core for repository management..."
sudo dnf install -y dnf-plugins-core

if ! command -v dnf config-manager >/dev/null; then
  echo_err "dnf config-manager not available even after installing plugin."
  exit 1
fi

# ─── [BLOCK: ADD GH REPO] ──────────────────────────────────────────────────────
# WHAT: Add GitHub CLI official repository
# WHY: To install latest gh via dnf
# FAIL: Abort on failure
# UX: Logs repo add operation
# DEBUG: Checks /etc/yum.repos.d/gh-cli.repo file existence
echo_info "Adding GitHub CLI repo..."
sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo

if [[ ! -f /etc/yum.repos.d/gh-cli.repo ]]; then
  echo_err "Failed to create gh-cli.repo in /etc/yum.repos.d/"
  exit 1
fi

# ─── [BLOCK: INSTALL GH CLI] ───────────────────────────────────────────────────
# WHAT: Install latest gh package from repo
# WHY: Provide GitHub CLI
# FAIL: Abort on install failure
# UX: Logs install command
# DEBUG: Verifies installation success
echo_info "Installing GitHub CLI (gh)..."
sudo dnf install -y gh

if command -v gh >/dev/null; then
  echo_ok "GitHub CLI installed: $(gh --version | head -n1)"
else
  echo_err "gh installation failed."
  exit 1
fi

exit 0
