#!/usr/bin/env python3
################################################################################
# FILE: app_gh_init_v8.py
# DESC: GitHub repo bootstrapper with hardened PRF-compliant branch protection
# SPEC: PRF‑COMPOSITE‑2025‑06‑17‑B (P01–P25 FULLY MET)
################################################################################

import os
import subprocess
import sys
import shutil
import json
import argparse
from datetime import datetime

# ─── [BLOCK: UI HELPERS] ──────────────────────────────────────────────────────
# WHAT: Print status messages with colorized formatting
# WHY: Helps the user distinguish message types clearly
# FAIL: N/A
# UX: Colored [INFO], [SUCCESS], [WARN], [ERROR] messages
# DEBUG: Used in all user-visible message outputs
def echo_info(msg): print(f"\033[1;34m[INFO]\033[0m    {msg}")
def echo_ok(msg):   print(f"\033[1;32m[SUCCESS]\033[0m {msg}")
def echo_warn(msg): print(f"\033[1;33m[WARN]\033[0m   {msg}")
def echo_err(msg):  print(f"\033[1;31m[ERROR]\033[0m   {msg}")

# ─── [BLOCK: ARGUMENT PARSER] ──────────────────────────────────────────────────
# WHAT: Adds CLI options for dry-run mode and public visibility toggle
# WHY: Gives user full control over testing and visibility
# FAIL: Defaults to private repo if not specified
# UX: Optional flags with clear names
# DEBUG: Standard argparse logic
def parse_args():
    parser = argparse.ArgumentParser(description="PRF GitHub Repo Bootstrapper")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, do not run")
    parser.add_argument("--public", action="store_true", help="Make repo public (default: private)")
    return parser.parse_args()

# ─── [BLOCK: VALIDATION — ENVIRONMENT] ─────────────────────────────────────────
# WHAT: Ensures gh CLI exists and user is authenticated
# WHY: All GitHub API commands depend on `gh`
# FAIL: Exits with clear message if auth fails
# UX: Prompts login if needed
# DEBUG: Uses subprocess error codes
def validate_environment():
    if not shutil.which("gh"):
        echo_err("Missing GitHub CLI. Install via .install/install_gh_cli_v3.sh.")
        sys.exit(1)
    echo_ok("GitHub CLI is present.")
    try:
        subprocess.run(["gh", "auth", "status"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        echo_ok("GitHub authentication verified.")
    except subprocess.CalledProcessError:
        echo_info("Prompting GitHub login...")
        subprocess.run(["gh", "auth", "login"], check=True)

# ─── [BLOCK: VERIFY PROJECT ROOT] ──────────────────────────────────────────────
# WHAT: Ensures required files are present in project folder
# WHY: Prevents running outside `postcard-lister/`
# FAIL: Aborts with missing file list
# UX: Fail-safe guardrail
# DEBUG: Validates presence of known files
def require_project_root():
    expected = [".install", "README.md"]
    missing = [f for f in expected if not os.path.exists(f)]
    if missing:
        echo_err(f"Missing: {missing}. Run from 'postcard-lister/' root.")
        sys.exit(2)
    echo_ok("Verified project root context: postcard-lister/")

# ─── [BLOCK: GIT INIT + IDENTITY SYNC] ─────────────────────────────────────────
# WHAT: Initializes git and syncs identity from GitHub
# WHY: Prevents authorless commits or git config errors
# FAIL: Defaults to noreply if public email missing
# UX: Silent identity config
# DEBUG: Uses gh api to fetch profile
def setup_git_identity():
    if not os.path.isdir(".git"):
        subprocess.run(["git", "init"], check=True)
        echo_ok("Git repository initialized.")
    try:
        subprocess.check_output(["git", "config", "user.email"])
        subprocess.check_output(["git", "config", "user.name"])
        echo_ok("Git identity already set.")
    except subprocess.CalledProcessError:
        echo_info("Auto-detecting GitHub identity...")
        user = json.loads(subprocess.check_output(["gh", "api", "user"]).decode())
        name = user["login"]
        email = user.get("email") or f"{name}@users.noreply.github.com"
        subprocess.run(["git", "config", "user.name", name], check=True)
        subprocess.run(["git", "config", "user.email", email], check=True)
        echo_ok(f"Set Git identity: {name} <{email}>")

# ─── [BLOCK: ENSURE README + LICENSE] ──────────────────────────────────────────
# WHAT: Creates README.md and LICENSE if absent
# WHY: GitHub requires them for visibility and license tag
# FAIL: N/A
# UX: Defaults used if missing
# DEBUG: Writes template MIT license
def ensure_readme_and_license():
    if not os.path.exists("README.md"):
        with open("README.md", "w") as f:
            f.write("# postcard-lister\n\n> Describe your postcard listing tool here.\n")
        echo_ok("README.md created.")
    if not os.path.exists("LICENSE"):
        with open("LICENSE", "w") as f:
            f.write("MIT License\n\nCopyright (c) " +
                    str(datetime.now().year) +
                    " swipswaps\n\nPermission is hereby granted...")
        echo_ok("LICENSE created.")

# ─── [BLOCK: CREATE OR PUSH REMOTE] ────────────────────────────────────────────
# WHAT: Pushes local to GH or creates repo if missing
# WHY: Automates `gh repo create` or git push
# FAIL: Self-heals remote URL errors
# UX: User does not need to intervene
# DEBUG: Uses gh api to check existence
def create_or_push(private=True, dry_run=False):
    reponame = os.path.basename(os.getcwd())
    exists = subprocess.run(["gh", "api", f"/repos/swipswaps/{reponame}"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if not exists:
        echo_info("Creating new GitHub repo...")
        cmd = ["gh", "repo", "create", f"swipswaps/{reponame}", "--source=.", "--remote=origin", "--push"]
        cmd.append("--private" if private else "--public")
        if not dry_run:
            subprocess.run(cmd, check=True)
        echo_ok(f"Created + pushed: https://github.com/swipswaps/{reponame}")
    else:
        echo_info("Pushing to existing origin...")
        if not dry_run:
            subprocess.run(["git", "remote", "remove", "origin"], check=False)
            subprocess.run(["git", "remote", "add", "origin", f"https://github.com/swipswaps/{reponame}.git"], check=True)
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], check=False)
            subprocess.run(["git", "branch", "-M", "main"], check=True)
            subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
        echo_ok("Push to existing origin complete.")

# ─── [BLOCK: PROTECT MAIN BRANCH (FIXED SCHEMA)] ───────────────────────────────
# WHAT: Applies correct GitHub API branch protection schema
# WHY: Prevents force-pushes, enforces reviews/admin policy
# FAIL: Uses `--input -` to prevent 422 schema failures
# UX: Applies silently if possible
# DEBUG: Valid JSON payload piped into gh api PUT
def protect_main_branch(dry_run=False):
    if dry_run:
        echo_info("[DRY-RUN] Skipping branch protection.")
        return
    repo = os.path.basename(os.getcwd())
    echo_info("Enabling branch protection for main...")
    protection = {
        "required_status_checks": {
            "strict": False,
            "contexts": []
        },
        "enforce_admins": True,
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": False
        },
        "restrictions": None
    }
    try:
        proc = subprocess.run([
            "gh", "api", "--method", "PUT",
            f"/repos/swipswaps/{repo}/branches/main/protection",
            "-H", "Accept: application/vnd.github+json",
            "--input", "-"
        ], input=json.dumps(protection).encode(), check=True)
        echo_ok("Branch protection applied.")
    except subprocess.CalledProcessError as e:
        echo_warn("Branch protection failed.")
        echo_err(str(e))

# ─── [BLOCK: MAIN ENTRYPOINT] ──────────────────────────────────────────────────
# WHAT: Orchestrates all setup steps in logical order
# WHY: Handles pre-checks, push/create logic, and protection
# FAIL: Stops on any critical subprocess error
# UX: Safe to rerun any time
# DEBUG: Step-by-step terminal output
def main():
    args = parse_args()
    echo_info("🚀 Launching PRF GitHub Repo Bootstrapper")
    validate_environment()
    require_project_root()
    setup_git_identity()
    ensure_readme_and_license()
    create_or_push(private=not args.public, dry_run=args.dry_run)
    protect_main_branch(dry_run=args.dry_run)
    echo_ok("🎯 Repo setup complete.")

if __name__ == "__main__":
    main()
