#!/usr/bin/env python3
################################################################################
# FILE: app_gh_init_v3.py
# DESC: GitHub CLI bootstrapper with fallback for existing repos
# SPEC: PRF‑COMPOSITE‑2025‑04‑22‑A (P01–P25)
################################################################################

import os
import subprocess
import sys
import shutil
import json

# ─── [BLOCK: UI HELPERS] ──────────────────────────────────────────────────────
# WHAT: Print helpers for terminal output with ANSI formatting
# WHY: Distinguishes INFO/SUCCESS/WARN/ERROR messages clearly for UX clarity
# FAIL: Not applicable (pure output)
# UX: Improves scan-ability and debugging clarity
# DEBUG: All outputs logged to stdout
def echo_info(msg): print(f"\033[1;34m[INFO]\033[0m    {msg}")
def echo_ok(msg):   print(f"\033[1;32m[SUCCESS]\033[0m {msg}")
def echo_warn(msg): print(f"\033[1;33m[WARN]\033[0m   {msg}")
def echo_err(msg):  print(f"\033[1;31m[ERROR]\033[0m   {msg}")

# ─── [BLOCK: REQUIRE GH CLI] ───────────────────────────────────────────────────
# WHAT: Validates presence of `gh` CLI
# WHY: Required for interacting with GitHub via script
# FAIL: Exit with instruction to install `.install/install_gh_cli_v3.sh`
# UX: Human-friendly guidance for missing tool
# DEBUG: Uses shutil.which to avoid subprocess overhead
def require_gh():
    if not shutil.which("gh"):
        echo_err("GitHub CLI (gh) not found. Run .install/install_gh_cli_v3.sh.")
        sys.exit(1)
    echo_ok("GitHub CLI (gh) detected.")

# ─── [BLOCK: REQUIRE AUTHENTICATION] ──────────────────────────────────────────
# WHAT: Confirms `gh` has valid login
# WHY: GitHub API calls will fail without auth
# FAIL: Attempts interactive login; exits on failure
# UX: Offers web login when needed, confirms success
# DEBUG: Uses `gh auth status` and return code check
def require_gh_auth():
    try:
        subprocess.run(["gh", "auth", "status"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        echo_ok("GitHub CLI is authenticated.")
    except subprocess.CalledProcessError:
        echo_warn("Not authenticated. Attempting gh auth login...")
        if subprocess.run(["gh", "auth", "login"]).returncode != 0:
            echo_err("GitHub authentication failed or was cancelled.")
            sys.exit(2)
        echo_ok("Authentication completed.")

# ─── [BLOCK: REQUIRE PROJECT ROOT] ─────────────────────────────────────────────
# WHAT: Ensure we are in `postcard-lister/` root
# WHY: Prevent incorrect path or repo context
# FAIL: Exit if expected files are missing
# UX: Prints working directory and missing files
# DEBUG: Uses os.path.exists
def require_postcard_lister_root():
    expected = ['.install', 'README.md']
    missing = [f for f in expected if not os.path.exists(f)]
    if missing:
        echo_err(f"Missing project files: {missing}. Must be run from 'postcard-lister/' root.")
        sys.exit(3)
    echo_ok("Confirmed: Inside 'postcard-lister/' root.")

# ─── [BLOCK: INIT LOCAL GIT] ───────────────────────────────────────────────────
# WHAT: Runs `git init` if .git directory does not exist
# WHY: Required before `gh repo create` can work
# FAIL: Exits on subprocess error
# UX: Verbose confirmation of init
# DEBUG: Subprocess run with `check=True`
def init_local_git():
    if not os.path.isdir(".git"):
        echo_info("Initializing local Git repo...")
        subprocess.run(["git", "init"], check=True)
        echo_ok("Local Git repo initialized.")
    else:
        echo_info("Local Git repo already exists.")

# ─── [BLOCK: CHECK REMOTE EXISTS ON GITHUB] ────────────────────────────────────
# WHAT: Checks if the GitHub repo already exists
# WHY: Prevents failure when using `gh repo create`
# FAIL: Returns False if repo does not exist or API fails
# UX: Explains fallback to push
# DEBUG: Uses `gh api` with structured json response
def remote_repo_exists(reponame):
    try:
        result = subprocess.run(
            ["gh", "api", f"/repos/swipswaps/{reponame}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        echo_info(f"GitHub repo already exists: swipswaps/{reponame}")
        return True
    except subprocess.CalledProcessError:
        echo_info("No existing GitHub repo found — creating fresh.")
        return False

# ─── [BLOCK: CREATE OR PUSH TO REMOTE] ─────────────────────────────────────────
# WHAT: Conditionally creates or pushes to GitHub repo
# WHY: Ensures one-shot compatibility with existing or new remotes
# FAIL: Exits on push/create failure
# UX: Clear messaging at each stage
# DEBUG: Uses subprocess return codes and echo messages
def create_or_push_repo():
    reponame = os.path.basename(os.getcwd())
    if remote_repo_exists(reponame):
        echo_info("Adding remote origin and pushing to existing GitHub repo...")
        subprocess.run(["git", "remote", "remove", "origin"], check=False)
        subprocess.run(["git", "remote", "add", "origin", f"https://github.com/swipswaps/{reponame}.git"], check=True)
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=False)
        subprocess.run(["git", "branch", "-M", "main"], check=True)
        subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
        echo_ok(f"Pushed to existing: https://github.com/swipswaps/{reponame}")
    else:
        echo_info("Creating new GitHub repo via gh CLI...")
        subprocess.run([
            "gh", "repo", "create", f"swipswaps/{reponame}",
            "--source=.", "--remote=origin", "--push", "--public"
        ], check=True)
        echo_ok(f"Created and pushed: https://github.com/swipswaps/{reponame}")

# ─── [BLOCK: MAIN ORCHESTRATOR] ───────────────────────────────────────────────
# WHAT: Runs all setup tasks in order
# WHY: Fully automated, human-readable bootstrapping
# FAIL: Stops execution at any validation error
# UX: Clear CLI output for each step
# DEBUG: Full stdout control and subprocess visibility
def main():
    echo_info("🔧 Starting PRF‑GH-INIT v3...")
    require_gh()
    require_gh_auth()
    require_postcard_lister_root()
    init_local_git()
    create_or_push_repo()
    echo_ok("🎉 Repo ready for dev. All setup steps completed.")

if __name__ == "__main__":
    main()
