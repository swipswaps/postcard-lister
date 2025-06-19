#!/usr/bin/env python3
################################################################################
# FILE: app_gh_init_v5.py
# DESC: GitHub CLI bootstrapper with full auto-config, dry-run, privacy, identity trace, and PRF protections
# SPEC: PRF‑COMPOSITE‑2025‑06‑16‑A (P01–P25)
################################################################################

import os
import subprocess
import sys
import shutil
import json
import argparse

# ─── [BLOCK: UI HELPERS] ──────────────────────────────────────────────────────
# WHAT: Terminal color-coded echo helpers
# WHY: Improve human readability during interactive or CI-based runs
# FAIL: N/A
# UX: Highlight successes, failures, and statuses
# DEBUG: All output uses stdout/stderr

def echo_info(msg): print(f"\033[1;34m[INFO]\033[0m    {msg}")
def echo_ok(msg):   print(f"\033[1;32m[SUCCESS]\033[0m {msg}")
def echo_warn(msg): print(f"\033[1;33m[WARN]\033[0m   {msg}")
def echo_err(msg):  print(f"\033[1;31m[ERROR]\033[0m   {msg}")

# ─── [BLOCK: ARGUMENT PARSER] ──────────────────────────────────────────────────
# WHAT: Supports optional --dry-run mode and --private repo setting
# WHY: Enables CI-friendly preview and conditional repo visibility
# FAIL: Defaults to interactive full mode
# UX: Clear CLI interface with minimal flags
# DEBUG: argparse will handle invalid input

def parse_args():
    parser = argparse.ArgumentParser(description="Initialize GitHub repo with PRF compliance")
    parser.add_argument("--dry-run", action="store_true", help="Only simulate actions without executing")
    parser.add_argument("--private", action="store_true", help="Create private repository")
    return parser.parse_args()

# ─── [BLOCK: REQUIRE GH CLI] ───────────────────────────────────────────────────
# WHAT: Ensures GitHub CLI is available
# WHY: Avoids failure in API or repo commands
# FAIL: Exits early if not found
# UX: Points user to installer
# DEBUG: Uses shutil.which

def require_gh():
    if not shutil.which("gh"):
        echo_err("GitHub CLI (gh) not found. Run .install/install_gh_cli_v3.sh.")
        sys.exit(1)
    echo_ok("GitHub CLI (gh) detected.")

# ─── [BLOCK: GH AUTHENTICATION] ───────────────────────────────────────────────
# WHAT: Verifies auth token
# WHY: API commands and repo creation require login
# FAIL: Prompts user if not logged in
# UX: Silent fallback, asks for credentials if needed
# DEBUG: subprocess return code and stderr

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

# ─── [BLOCK: ROOT VALIDATION] ─────────────────────────────────────────────────
# WHAT: Check required files to confirm we are in the correct directory
# WHY: Prevent accidental miswrites in unrelated directories
# FAIL: Exits if key files are missing
# UX: Prevents destructive actions
# DEBUG: Lists missing files

def require_postcard_lister_root():
    expected = ['.install', 'README.md']
    missing = [f for f in expected if not os.path.exists(f)]
    if missing:
        echo_err(f"Missing files: {missing}. Must run from 'postcard-lister/' root.")
        sys.exit(3)
    echo_ok("Confirmed: Inside 'postcard-lister/' root.")

# ─── [BLOCK: INIT LOCAL GIT] ───────────────────────────────────────────────────
# WHAT: Set up git repository if not already present
# WHY: Required for remote interaction and version control
# FAIL: Exits on init failure
# UX: Explicit messaging
# DEBUG: subprocess return

def init_local_git(dry_run=False):
    if not os.path.isdir(".git"):
        echo_info("Initializing local Git repo...")
        if not dry_run:
            subprocess.run(["git", "init"], check=True)
        echo_ok("Git repo initialized.")
    else:
        echo_info("Git repo already exists.")

# ─── [BLOCK: AUTO-SET IDENTITY] ───────────────────────────────────────────────
# WHAT: Uses GitHub profile for user.name and user.email
# WHY: Required for valid commits
# FAIL: Aborts if identity cannot be determined
# UX: Silent fallback, user is never prompted
# DEBUG: Uses gh api user JSON

def ensure_git_identity(dry_run=False):
    try:
        name = subprocess.check_output(["git", "config", "user.name"]).decode().strip()
        email = subprocess.check_output(["git", "config", "user.email"]).decode().strip()
        if name and email:
            echo_ok(f"Git identity already set: {name} <{email}>")
            return
    except subprocess.CalledProcessError:
        echo_info("Git identity not set — fetching from GitHub...")

    raw = subprocess.check_output(["gh", "api", "user"]).decode()
    profile = json.loads(raw)
    username = profile.get("login")
    email = profile.get("email") or f"{username}@users.noreply.github.com"
    if not dry_run:
        subprocess.run(["git", "config", "user.name", username], check=True)
        subprocess.run(["git", "config", "user.email", email], check=True)
        with open(".gitconfig.local", "w") as f:
            f.write(f"[user]\n\tname = {username}\n\temail = {email}\n")
    echo_ok(f"Git identity configured: {username} <{email}>")

# ─── [BLOCK: REMOTE CHECK] ─────────────────────────────────────────────────────
# WHAT: Checks for existing GitHub repo
# WHY: Avoids duplicate repo errors
# FAIL: Returns False on nonexistence
# UX: Printed status message
# DEBUG: API call return code

def remote_repo_exists(reponame):
    try:
        subprocess.run(["gh", "api", f"/repos/swipswaps/{reponame}"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        echo_info(f"GitHub repo already exists: swipswaps/{reponame}")
        return True
    except subprocess.CalledProcessError:
        return False

# ─── [BLOCK: CREATE OR PUSH REPO] ──────────────────────────────────────────────
# WHAT: Pushes local repo to GitHub
# WHY: Deploys repo and preserves changes
# FAIL: All subprocesses are guarded
# UX: Clear stdout/stderr visible
# DEBUG: Commit hash and remote status visible

def create_or_push_repo(private=False, dry_run=False):
    reponame = os.path.basename(os.getcwd())
    if remote_repo_exists(reponame):
        echo_info("Remote exists. Rebinding origin...")
        if not dry_run:
            subprocess.run(["git", "remote", "remove", "origin"], check=False)
            subprocess.run(["git", "remote", "add", "origin", f"https://github.com/swipswaps/{reponame}.git"], check=True)
    else:
        echo_info("Creating new GitHub repo...")
        cmd = ["gh", "repo", "create", f"swipswaps/{reponame}", "--source=.", "--remote=origin", "--push"]
        if private:
            cmd.append("--private")
        else:
            cmd.append("--public")
        if not dry_run:
            subprocess.run(cmd, check=True)
        echo_ok(f"Created and pushed: https://github.com/swipswaps/{reponame}")
        return

    if not dry_run:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=False)
        subprocess.run(["git", "branch", "-M", "main"], check=True)
        subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
    echo_ok(f"Pushed to existing: https://github.com/swipswaps/{reponame}")

# ─── [BLOCK: MAIN] ─────────────────────────────────────────────────────────────
# WHAT: Top-level orchestrator for bootstrap
# WHY: Ensures correct sequence of steps
# FAIL: Exits early if any condition fails
# UX: Centralized output
# DEBUG: Entire flow visible in stdout

def main():
    args = parse_args()
    echo_info("🔧 Starting PRF‑GH‑INIT v5...")
    require_gh()
    require_gh_auth()
    require_postcard_lister_root()
    init_local_git(dry_run=args.dry_run)
    ensure_git_identity(dry_run=args.dry_run)
    create_or_push_repo(private=args.private, dry_run=args.dry_run)
    echo_ok("🎉 GitHub repo bootstrap complete.")

if __name__ == "__main__":
    main()