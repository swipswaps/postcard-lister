#!/usr/bin/env python3
################################################################################
# FILE: app_gh_init_v2.py
# DESC: GitHub CLI-integrated bootstrapper with self-auth fallback
# SPEC: PRF‑COMPOSITE‑2025‑04‑22‑A (P01–P25)
################################################################################

import os
import subprocess
import sys
import shutil

# ─── [BLOCK: UI HELPERS] ──────────────────────────────────────────────────────
# WHAT: CLI print helpers with ANSI styling
# WHY: UX-friendly output formatting
# FAIL: n/a
# UX: Clear distinction between INFO / SUCCESS / ERROR
# DEBUG: stdout only, color-coded
def echo_info(msg): print(f"\033[1;34m[INFO]\033[0m    {msg}")
def echo_ok(msg):   print(f"\033[1;32m[SUCCESS]\033[0m {msg}")
def echo_warn(msg): print(f"\033[1;33m[WARN]\033[0m   {msg}")
def echo_err(msg):  print(f"\033[1;31m[ERROR]\033[0m   {msg}")

# ─── [BLOCK: REQUIRE GH CLI] ──────────────────────────────────────────────────
# WHAT: Ensure `gh` is installed
# WHY: Required for all GitHub CLI operations
# FAIL: Exit with install suggestion
# UX: Points to script location if missing
# DEBUG: shutil.which
def require_gh():
    if not shutil.which("gh"):
        echo_err("GitHub CLI (gh) not found in PATH. Please run .install/install_gh_cli_v3.sh.")
        sys.exit(1)
    echo_ok("Verified: GitHub CLI (gh) is available.")

# ─── [BLOCK: REQUIRE AUTHENTICATION] ──────────────────────────────────────────
# WHAT: Ensure `gh` is authenticated to GitHub
# WHY: Repo creation fails without auth
# FAIL: Attempt interactive login or exit on failure
# UX: Prompts user for `gh auth login` only if needed
# DEBUG: `gh auth status` check
def require_gh_auth():
    try:
        subprocess.run(["gh", "auth", "status"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        echo_ok("Verified: GitHub CLI is authenticated.")
    except subprocess.CalledProcessError:
        echo_warn("GitHub authentication missing — attempting interactive login...")
        login = subprocess.run(["gh", "auth", "login"], check=False)
        if login.returncode != 0:
            echo_err("Authentication failed or cancelled. Aborting.")
            sys.exit(2)
        echo_ok("GitHub CLI authenticated successfully.")

# ─── [BLOCK: REQUIRE POSTCARD-LISTER CONTEXT] ─────────────────────────────────
# WHAT: Ensure script is run inside correct project folder
# WHY: Prevent path errors or incorrect repo naming
# FAIL: Exit if critical files/folders are missing
# UX: Shows current dir and missing elements
# DEBUG: os.path.exists check
def require_postcard_lister_root():
    expected = ['.install', 'README.md']
    missing = [f for f in expected if not os.path.exists(f)]
    if missing:
        echo_err(f"Run this script from the root of 'postcard-lister/'. Missing: {missing}")
        sys.exit(3)
    echo_ok("Verified: Running inside 'postcard-lister/' root.")

# ─── [BLOCK: INIT LOCAL GIT REPO] ─────────────────────────────────────────────
# WHAT: Runs `git init` if needed
# WHY: Required for `gh repo create --source`
# FAIL: Fails early if init fails
# UX: Confirms init or skips with message
# DEBUG: Checks `.git/` dir
def init_local_repo():
    if not os.path.isdir(".git"):
        echo_info("Initializing local Git repository...")
        subprocess.run(["git", "init"], check=True)
        echo_ok("Local Git repository initialized.")
    else:
        echo_info("Local Git repo already exists — skipping init.")

# ─── [BLOCK: CREATE REMOTE GH REPO] ───────────────────────────────────────────
# WHAT: Use `gh repo create` with local push
# WHY: Simplifies remote setup and upload
# FAIL: Exit on any CLI error (nonzero return)
# UX: Clear messaging, defensive naming
# DEBUG: Uses folder name as repo name
def create_remote_repo():
    reponame = os.path.basename(os.getcwd())
    echo_info(f"Creating GitHub repo for: {reponame}")
    cmd = [
        "gh", "repo", "create", f"swipswaps/{reponame}",
        "--source=.", "--remote=origin", "--push", "--public"
    ]
    try:
        subprocess.run(cmd, check=True)
        echo_ok(f"GitHub repo created and pushed to: https://github.com/swipswaps/{reponame}")
    except subprocess.CalledProcessError as e:
        echo_err("Failed to create or push to GitHub repo via gh.")
        sys.exit(4)

# ─── [BLOCK: MAIN ORCHESTRATOR] ───────────────────────────────────────────────
# WHAT: Executes the full logic chain
# WHY: Enforces linear, auditable setup
# FAIL: Controlled at each step with sys.exit()
# UX: Friendly final output
# DEBUG: All stdout logged
def main():
    echo_info("🔍 PRF‑GH-INIT v2 starting...")
    require_gh()
    require_gh_auth()
    require_postcard_lister_root()
    init_local_repo()
    create_remote_repo()
    echo_ok("🎉 GitHub repo setup completed successfully.")

if __name__ == "__main__":
    main()
