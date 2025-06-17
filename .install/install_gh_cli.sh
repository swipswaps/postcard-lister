#!/usr/bin/env bash
################################################################################
# FILE: .install/install_gh_cli.sh
# DESC: Install GitHub CLI (gh) on Fedora
# SPEC: PRF‑COMPOSITE‑2025‑04‑22‑A (P01–P25)
################################################################################

set -euo pipefail
IFS=$'\n\t'

echo_info() { echo -e "\033[1;34m[INFO]\033[0m  $1"; }
echo_ok()   { echo -e "\033[1;32m[SUCCESS]\033[0m $1"; }
echo_err()  { echo -e "\033[1;31m[ERROR]\033[0m $1"; }

if ! grep -q '^ID=fedora' /etc/os-release; then
  echo_err "This script is for Fedora-based systems only."
  exit 1
fi

if command -v gh >/dev/null; then
  echo_ok "gh is already installed: $(gh --version | head -n 1)"
  exit 0
fi

echo_info "Installing GitHub CLI via dnf..."
sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
sudo dnf install -y gh

if command -v gh >/dev/null; then
  echo_ok "GitHub CLI successfully installed."
else
  echo_err "gh installation failed."
  exit 1
fi
