#!/usr/bin/env bash
################################################################################
# FILE: .install/install_gh_cli.sh
# DESC: Install GitHub CLI (gh) on Fedora 42+ with dnf5 compatibility
# SPEC: PRF‑COMPOSITE‑2025‑04‑22‑A (P01–P25)
################################################################################

set -euo pipefail
IFS=$'\n\t'

# ─── [BLOCK: UI MESSAGE HELPERS] ──────────────────────────────────────────────
# WHAT: Defines stylized echo helpers for UX
# WHY: Ensure messages are visible, colorized, and user-comprehensible
# FAIL: n/a
# UX: Consistent output styles
# DEBUG: n/a
echo_info() { echo -e "\033[1;34m[INFO]\033[0m  $1"; }
echo_ok()   { echo -e "\033[1;32m[SUCCESS]\033[0m  $1"; }
echo_warn() { echo -e "\033[1;33m[WARN]\033[0m  $1"; }
echo_err()  { echo -e "\033[1;31m[ERROR]\033[0m  $1"; }

# ─── [BLOCK: FEDORA DETECTION] ────────────────────────────────────────────────
# WHAT: Ensure script is run only on Fedora-based systems
# WHY: Prevent misuse on unsupported distros
# FAIL: Exit if not Fedora
# UX: Clear error message with explanation
# DEBUG: Reads /etc/os-release
if ! grep -q '^ID=fedora' /etc/os-release; then
  echo_err "This script is only supported on Fedora systems."
  exit 1
fi

# ─── [BLOCK: PRECHECK GH EXISTENCE] ───────────────────────────────────────────
# WHAT: Skip install if gh is already present
# WHY: Avoid redundant work
# FAIL: n/a
# UX: Confirm version installed
# DEBUG: Uses PATH check and `gh --version`
if command -v gh >/dev/null 2>&1; then
  echo_ok "GitHub CLI is already installed: $(gh --version | head -n1)"
  exit 0
fi

# ─── [BLOCK: INSTALL GH REPO MANUALLY] ────────────────────────────────────────
# WHAT: Adds GitHub CLI repo manually due to dnf5 dropping --add-repo
# WHY: `dnf config-manager` is no longer valid under dnf5 in Fedora 42+
# FAIL: Exit if repo file write fails
# UX: Verbose info on each step
# DEBUG: Writes .repo to /etc/yum.repos.d directly

REPO_FILE="/etc/yum.repos.d/gh-cli.repo"
TEMP_REPO="/tmp/gh-cli.repo"

echo_info "Downloading GitHub CLI repo file..."
curl -fsSL https://cli.github.com/packages/rpm/gh-cli.repo -o "$TEMP_REPO"

if [[ ! -s "$TEMP_REPO" ]]; then
  echo_err "Failed to download gh-cli.repo or file is empty."
  exit 1
fi

echo_info "Installing GitHub CLI repo to $REPO_FILE"
sudo cp "$TEMP_REPO" "$REPO_FILE"
sudo chmod 644 "$REPO_FILE"

if [[ -f "$REPO_FILE" ]]; then
  echo_ok "GitHub CLI repo registered successfully."
else
  echo_err "Failed to move gh-cli.repo into /etc/yum.repos.d/"
  exit 1
fi

# ─── [BLOCK: INSTALL GH PACKAGE] ──────────────────────────────────────────────
# WHAT: Installs GitHub CLI from registered repo
# WHY: Required for GitHub operations in PRF scripts
# FAIL: Exit on install failure
# UX: Shows progress
# DEBUG: Final `gh` binary validation
echo_info "Installing GitHub CLI using dnf..."
sudo dnf install -y gh

if command -v gh >/dev/null 2>&1; then
  echo_ok "GitHub CLI installed: $(gh --version | head -n1)"
else
  echo_err "GitHub CLI install failed. Check repo or network."
  exit 1
fi

# ─── [BLOCK: CLEANUP] ─────────────────────────────────────────────────────────
# WHAT: Remove temporary repo file
# WHY: Prevent clutter
# FAIL: Silent fail OK
# UX: Silent unless debug mode needed
rm -f "$TEMP_REPO"

echo_ok "✅ GitHub CLI installation completed successfully."
exit 0
