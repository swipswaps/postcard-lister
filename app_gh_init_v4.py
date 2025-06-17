#!/usr/bin/env python3
################################################################################
# FILE: app_gh_init_v4.py
# DESC: GitHub CLI bootstrapper with full auto-config for Git identity fallback
# SPEC: PRF‑COMPOSITE‑2025‑06‑16‑A (P01–P25)
################################################################################

import os
import subprocess
import sys
import shutil
import json

# ─── [BLOCK: UI HELPERS] ──────────────────────────────────────────────────────
# WHAT: Colored print helpers
# WHY: Improves terminal UX for status tracking
# FAIL: N/A
# UX: Ensures readability of important steps
# DEBUG: All visible via stdout
def echo_info(msg): print(f"\033[1;34m[INFO]\033[0m    {msg}")
def echo_ok(msg):   print(f"\033[1;32m[SUCCESS]\033[0m {msg}")
def echo_warn(msg): print(f"\033[1;33m[WARN]\033[0m   {msg}")
def echo_err(msg):  print(f"\033[1;31m[ERROR]\033[0m   {msg}")

# ─── [BLOCK: REQUIRE GH CLI] ───────────────────────────────────────────────────
# WHAT: Validates that `gh` is installed
# WHY: Required for GitHub integration
# FAIL: Exits if missing
# UX: Direct user to installer script
# DEBUG: Uses shutil.which for detection
def require_gh():
    if not shutil.which("gh"):
        echo_err("GitHub CLI (gh) not found. Run .install/install_gh_cli_v3.sh.")
        sys.exit(1)
    echo_ok("GitHub CLI (gh) detected.")

# ─── [BLOCK: GH AUTHENTICATION] ───────────────────────────────────────────────
# WHAT: Verifies `gh auth` status
# WHY: Necessary for API interaction
# FAIL: Prompts login if needed
# UX: Full automation with no manual config
# DEBUG: Uses subprocess return codes
def require_gh_auth():
    try:
        subprocess.run(["gh", "auth", "status"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        echo_ok("GitHub CLI is authenticated.")
    except subprocess.CalledProcessError:
        echo_warn("Not authenticated. Attempting gh auth login...")
        if subprocess.run(["gh", "auth", "login"]).returncode != 0:
            echo_err("GitHub authentication failed.")
            sys.exit(2)
        echo_ok("Authentication completed.")

# ─── [BLOCK: CONFIRM PROJECT ROOT] ────────────────────────────────────────────
# WHAT: Ensures execution from correct path
# WHY: Prevents corruption or failure
# FAIL: Exits on missing key files
# UX: Explicit message on failure
# DEBUG: Uses os.path.exists
def require_postcard_lister_root():
    expected = ['.install', 'README.md']
    missing = [f for f in expected if not os.path.exists(f)]
    if missing:
        echo_err(f"Missing files: {missing}. Must run from 'postcard-lister/' root.")
        sys.exit(3)
    echo_ok("Confirmed: Inside 'postcard-lister/' root.")

# ─── [BLOCK: INIT LOCAL GIT] ───────────────────────────────────────────────────
# WHAT: Ensures `.git` exists
# WHY: Required before pushing or creating repo
# FAIL: Exits on init error
# UX: Clear step output
# DEBUG: subprocess.run with check=True
def init_local_git():
    if not os.path.isdir(".git"):
        echo_info("Initializing local Git repo...")
        subprocess.run(["git", "init"], check=True)
        echo_ok("Git repo initialized.")
    else:
        echo_info("Git repo already exists.")

# ─── [BLOCK: DETECT AND SET GIT IDENTITY] ──────────────────────────────────────
# WHAT: Auto-configure `user.name` and `user.email`
# WHY: Required for committing to Git
# FAIL: Exits if email/username cannot be fetched
# UX: Fully silent and automatic; no user typing
# DEBUG: Uses `gh api user` to fetch identity
def ensure_git_identity():
    try:
        name = subprocess.check_output(["git", "config", "user.name"]).decode().strip()
        email = subprocess.check_output(["git", "config", "user.email"]).decode().strip()
        if name and email:
            echo_ok(f"Git identity already set: {name} <{email}>")
            return
    except subprocess.CalledProcessError:
        echo_info("Git identity not set — fetching from GitHub...")

    try:
        raw = subprocess.check_output(["gh", "api", "user"]).decode()
        profile = json.loads(raw)
        username = profile.get("login")
        email = profile.get("email") or f"{username}@users.noreply.github.com"
        subprocess.run(["git", "config", "user.name", username], check=True)
        subprocess.run(["git", "config", "user.email", email], check=True)
        echo_ok(f"Git identity configured: {username} <{email}>")
    except Exception as e:
        echo_err(f"Failed to set Git identity: {e}")
        sys.exit(4)

# ─── [BLOCK: CHECK REMOTE] ─────────────────────────────────────────────────────
# WHAT: Determines if repo already exists
# WHY: Decides between `gh repo create` vs `git push`
# FAIL: Returns False on 404 or error
# UX: Transparent fallback
# DEBUG: Uses gh api /repos/<user>/<repo>
def remote_repo_exists(reponame):
    try:
        subprocess.run(
            ["gh", "api", f"/repos/swipswaps/{reponame}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        echo_info(f"GitHub repo already exists: swipswaps/{reponame}")
        return True
    except subprocess.CalledProcessError:
        echo_info("No GitHub repo found — proceeding to create new.")
        return False

# ─── [BLOCK: CREATE OR PUSH REPO] ──────────────────────────────────────────────
# WHAT: Pushes to GitHub depending on repo state
# WHY: Enables full reuse of existing or creation of new
# FAIL: Aborts on Git errors
# UX: Verbose output for each operation
# DEBUG: All subprocess outputs handled
def create_or_push_repo():
    reponame = os.path.basename(os.getcwd())
    if remote_repo_exists(reponame):
        echo_info("Remote exists. Re-linking and pushing...")
        subprocess.run(["git", "remote", "remove", "origin"], check=False)
        subprocess.run(["git", "remote", "add", "origin", f"https://github.com/swipswaps/{reponame}.git"], check=True)
    else:
        echo_info("Creating new GitHub repo via gh CLI...")
        subprocess.run([
            "gh", "repo", "create", f"swipswaps/{reponame}",
            "--source=.", "--remote=origin", "--push", "--public"
        ], check=True)
        echo_ok(f"Created and pushed: https://github.com/swipswaps/{reponame}")
        return

    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], check=False)
    subprocess.run(["git", "branch", "-M", "main"], check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
    echo_ok(f"Pushed to existing: https://github.com/swipswaps/{reponame}")

# ─── [BLOCK: MAIN] ─────────────────────────────────────────────────────────────
# WHAT: Orchestrates entire setup
# WHY: No user input required; safe to run as-is
# FAIL: Stops on any failure
# UX: Structured log with ANSI formatting
# DEBUG: All subprocesses visible via stdout/stderr
def main():
    echo_info("🔧 Starting PRF‑GH-INIT v4...")
    require_gh()
    require_gh_auth()
    require_postcard_lister_root()
    init_local_git()
    ensure_git_identity()
    create_or_push_repo()
    echo_ok("🎉 Repo is live and ready.")

if __name__ == "__main__":
    main()
