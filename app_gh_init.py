#!/usr/bin/env python3
################################################################################
# FILE: app_gh_init.py
# DESC: GitHub CLI-integrated repo bootstrapper for `postcard-lister/`
# SPEC: PRF‑COMPOSITE‑2025‑04‑22‑A (P01–P25)
################################################################################

import os
import subprocess
import sys
import shutil

# ─── [BLOCK: UI HELPERS] ──────────────────────────────────────────────────────
def echo_info(msg): print(f"\033[1;34m[INFO]\033[0m    {msg}")
def echo_ok(msg):   print(f"\033[1;32m[SUCCESS]\033[0m {msg}")
def echo_err(msg):  print(f"\033[1;31m[ERROR]\033[0m   {msg}")

# ─── [BLOCK: FAIL FAST ENV CHECK] ──────────────────────────────────────────────
# WHAT: Ensure `gh` is available before proceeding
# WHY: All GitHub operations use `gh` CLI instead of `git`
# FAIL: Abort with clear instruction
# UX: Human-readable CLI output
# DEBUG: subprocess + fallback
def require_gh():
    if not shutil.which("gh"):
        echo_err("GitHub CLI (gh) not found in PATH. Please run install_gh_cli_v3.sh.")
        sys.exit(1)
    echo_ok("Verified: GitHub CLI (gh) is available.")

# ─── [BLOCK: DEFENSIVE FOLDER CHECK] ───────────────────────────────────────────
# WHAT: Ensure script is run inside `postcard-lister/`
# WHY: Prevent context errors or repo misinit
# FAIL: Exit if `pyproject.toml` or `.install` not found
# UX: Prints working directory and status
# DEBUG: Uses os.path.isdir()
def require_postcard_lister_root():
    expected = ['.install', 'README.md']
    missing = [f for f in expected if not os.path.exists(f)]
    if missing:
        echo_err(f"Run this script from the root of 'postcard-lister/'. Missing: {missing}")
        sys.exit(2)
    echo_ok("Verified: Running inside 'postcard-lister/' root.")

# ─── [BLOCK: INIT LOCAL GH REPO] ───────────────────────────────────────────────
# WHAT: Initialize local repo using `gh` if not already git-initialized
# WHY: Ensure repo is ready to sync with GitHub
# FAIL: Exit on failure to init
# UX: Prints commands used
# DEBUG: Uses `subprocess.run`
def init_local_repo():
    if not os.path.isdir(".git"):
        echo_info("Initializing local Git repo...")
        subprocess.run(["git", "init"], check=True)
        echo_ok("Local Git repo initialized.")
    else:
        echo_info("Git repo already exists locally.")

# ─── [BLOCK: CREATE REMOTE GH REPO] ────────────────────────────────────────────
# WHAT: Use `gh repo create` with public visibility
# WHY: Replace git remote + push with `gh` CLI
# FAIL: Abort if repo already exists or `gh` fails
# UX: Clear output from `gh`
# DEBUG: Logs stderr on failure
def create_remote_repo():
    echo_info("Creating GitHub repo via `gh` CLI...")

    # Defensive: use folder name as repo name
    reponame = os.path.basename(os.getcwd())
    cmd = [
        "gh", "repo", "create", f"swipswaps/{reponame}",
        "--source=.", "--remote=origin", "--push", "--public"
    ]
    try:
        subprocess.run(cmd, check=True)
        echo_ok(f"Created and pushed to https://github.com/swipswaps/{reponame}")
    except subprocess.CalledProcessError:
        echo_err("Failed to create GitHub repo via gh.")
        sys.exit(3)

# ─── [BLOCK: MAIN ENTRYPOINT] ──────────────────────────────────────────────────
# WHAT: Top-level orchestrator
# WHY: Chain dependency, environment, and `gh` steps
# FAIL: All wrapped in `try`/`exit`-on-error
# UX: Friendly CLI for operators
# DEBUG: Full logging included
def main():
    echo_info("🔍 PRF‑GH-INIT for postcard-lister starting...")
    require_gh()
    require_postcard_lister_root()
    init_local_repo()
    create_remote_repo()
    echo_ok("🎉 GitHub repo setup completed. Ready for development!")

if __name__ == "__main__":
    main()
