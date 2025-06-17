#!/usr/bin/env python3
################################################################################
# FILE: app_gh_init_v6.py
# DESC: PRF-hardened GH bootstrapper with identity trace, README/LICENSE, protection
# SPEC: PRF‑COMPOSITE‑2025‑06‑17‑A (P01–P25)
################################################################################

import os
import subprocess
import sys
import shutil
import json
import argparse
from datetime import datetime

# ─── [BLOCK: UI HELPERS] ──────────────────────────────────────────────────────
# WHAT: Color-coded echo helpers for terminal output
# WHY: Improve human and CI readability of script events
# FAIL: N/A
# UX: Clear status separation for INFO/SUCCESS/WARN/ERROR
# DEBUG: Print to stdout/stderr
def echo_info(msg): print(f"\033[1;34m[INFO]\033[0m    {msg}")
def echo_ok(msg):   print(f"\033[1;32m[SUCCESS]\033[0m {msg}")
def echo_warn(msg): print(f"\033[1;33m[WARN]\033[0m   {msg}")
def echo_err(msg):  print(f"\033[1;31m[ERROR]\033[0m   {msg}")

# ─── [BLOCK: ARGUMENT PARSER] ──────────────────────────────────────────────────
# WHAT: Parses flags like --dry-run and visibility toggles
# WHY: Allows CI and scripting flexibility
# FAIL: Defaults to dry-run=False, private=True
# UX: Optional flags to control execution
# DEBUG: argparse input parsing
def parse_args():
    parser = argparse.ArgumentParser(description="PRF GitHub Repo Bootstrapper")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, do not run")
    parser.add_argument("--public", action="store_true", help="Make repo public (default is private)")
    return parser.parse_args()

# ─── [BLOCK: VALIDATION — ENVIRONMENT] ─────────────────────────────────────────
# WHAT: Validates prerequisites and login
# WHY: Prevents error from missing tools
# FAIL: Exits early if gh is not present or authenticated
# UX: Shows clear setup instructions
# DEBUG: Captures subprocess failures
def validate_environment():
    if not shutil.which("gh"):
        echo_err("Missing GitHub CLI. Run .install/install_gh_cli_v3.sh first.")
        sys.exit(1)
    echo_ok("GitHub CLI is present.")

    try:
        subprocess.run(["gh", "auth", "status"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        echo_ok("GitHub authentication valid.")
    except subprocess.CalledProcessError:
        echo_info("Authenticating via gh...")
        subprocess.run(["gh", "auth", "login"], check=True)

# ─── [BLOCK: VERIFY PROJECT ROOT] ──────────────────────────────────────────────
# WHAT: Ensures we're inside postcard-lister repo
# WHY: Avoids mis-targeting unrelated folders
# FAIL: Aborts if .install or README.md is missing
# UX: Prevents repo pollution
# DEBUG: Prints missing files
def require_project_root():
    expected = [".install", "README.md"]
    missing = [f for f in expected if not os.path.exists(f)]
    if missing:
        echo_err(f"Missing: {missing}. Must run from project root.")
        sys.exit(2)
    echo_ok("Confirmed: Running from postcard-lister/ root.")

# ─── [BLOCK: GIT INIT AND IDENTITY] ────────────────────────────────────────────
# WHAT: Initialize .git if needed, configure GitHub identity
# WHY: Enables commits and push under user profile
# FAIL: Uses fallback noreply email if public unavailable
# UX: Never prompts; always auto-sets
# DEBUG: Reads/writes .gitconfig.local
def setup_git_identity():
    if not os.path.isdir(".git"):
        subprocess.run(["git", "init"], check=True)
        echo_ok("Initialized local Git repo.")
    try:
        subprocess.check_output(["git", "config", "user.email"])
        subprocess.check_output(["git", "config", "user.name"])
        echo_ok("Git identity already set.")
    except subprocess.CalledProcessError:
        echo_info("Fetching Git identity from GitHub...")
        user = json.loads(subprocess.check_output(["gh", "api", "user"]).decode())
        name = user["login"]
        email = user.get("email") or f"{name}@users.noreply.github.com"
        subprocess.run(["git", "config", "user.name", name], check=True)
        subprocess.run(["git", "config", "user.email", email], check=True)
        with open(".gitconfig.local", "w") as f:
            f.write(f"[user]\n\tname = {name}\n\temail = {email}\n")
        echo_ok(f"Git identity set: {name} <{email}>")

# ─── [BLOCK: LICENSE + README] ─────────────────────────────────────────────────
# WHAT: Create README.md and LICENSE if missing
# WHY: GitHub visibility, repo metadata, open source compliance
# FAIL: N/A
# UX: Uses MIT by default
# DEBUG: Writes files only if missing
def ensure_readme_and_license():
    if not os.path.exists("README.md"):
        with open("README.md", "w") as f:
            f.write("# postcard-lister\n\n> Describe your postcard listing tool here.\n")
        echo_ok("Created README.md.")
    if not os.path.exists("LICENSE"):
        with open("LICENSE", "w") as f:
            f.write("MIT License\n\nCopyright (c) " +
                    str(datetime.now().year) + " swipswaps\n\nPermission is hereby granted...")
        echo_ok("Created LICENSE.")

# ─── [BLOCK: GH CREATE OR PUSH] ────────────────────────────────────────────────
# WHAT: Either create new repo or push to existing one
# WHY: Automates setup logic for both cases
# FAIL: Handles remote add errors gracefully
# UX: All messages visible in real-time
# DEBUG: Runs dry-run if flagged
def create_or_push(private=True, dry_run=False):
    reponame = os.path.basename(os.getcwd())
    exists = subprocess.run(["gh", "api", f"/repos/swipswaps/{reponame}"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if not exists:
        echo_info("Creating repo on GitHub...")
        cmd = ["gh", "repo", "create", f"swipswaps/{reponame}", "--source=.", "--remote=origin", "--push"]
        cmd.append("--private" if private else "--public")
        if not dry_run:
            subprocess.run(cmd, check=True)
        echo_ok(f"Repo created and pushed: https://github.com/swipswaps/{reponame}")
    else:
        echo_info("Pushing to existing remote...")
        if not dry_run:
            subprocess.run(["git", "remote", "remove", "origin"], check=False)
            subprocess.run(["git", "remote", "add", "origin", f"https://github.com/swipswaps/{reponame}.git"], check=True)
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], check=False)
            subprocess.run(["git", "branch", "-M", "main"], check=True)
            subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
        echo_ok("Pushed updates to: " + f"https://github.com/swipswaps/{reponame}")

# ─── [BLOCK: BRANCH PROTECTION] ────────────────────────────────────────────────
# WHAT: Protects main branch via GitHub API
# WHY: Prevents force-push and enforces PR-based workflows
# FAIL: Warns if protection fails
# UX: Safety enforcement
# DEBUG: Uses gh api to PATCH branch protection
def protect_main_branch(dry_run=False):
    repo = os.path.basename(os.getcwd())
    if dry_run:
        echo_info("[DRY-RUN] Skipping branch protection.")
        return
    echo_info("Applying branch protection to 'main'...")
    try:
        subprocess.run([
            "gh", "api", "--method", "PUT",
            f"/repos/swipswaps/{repo}/branches/main/protection",
            "-H", "Accept: application/vnd.github+json",
            "-f", "required_status_checks='{}'",
            "-f", "enforce_admins=true",
            "-f", "required_pull_request_reviews='{}'",
            "-f", "restrictions='{}'"
        ], check=True)
        echo_ok("Branch protection enabled.")
    except subprocess.CalledProcessError:
        echo_warn("Failed to apply branch protection.")

# ─── [BLOCK: MAIN] ─────────────────────────────────────────────────────────────
# WHAT: Entry point with enforced step-by-step ordering
# WHY: Centralizes top-level workflow
# FAIL: Full error trace via sys.exit
# UX: Controlled start-to-finish with recovery points
# DEBUG: All stages logged in stdout
def main():
    args = parse_args()
    echo_info("🔧 Starting app_gh_init_v6.py")
    validate_environment()
    require_project_root()
    setup_git_identity()
    ensure_readme_and_license()
    create_or_push(private=not args.public, dry_run=args.dry_run)
    protect_main_branch(dry_run=args.dry_run)
    echo_ok("🎯 GH bootstrap complete.")

if __name__ == "__main__":
    main()
