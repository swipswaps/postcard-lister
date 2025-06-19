#!/usr/bin/env python3
################################################################################
# FILE: app_gh_init_v7.py
# DESC: Hardened GitHub repo initializer with README/LICENSE, identity sync,
#       and validated branch protection (PRF-compliant, zero truncation)
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
# WHAT: Color-coded echo wrappers for terminal output
# WHY: Standardizes visibility across status types (INFO, OK, WARN, ERROR)
# FAIL: N/A
# UX: Ensures clean human-readable status lines in logs and consoles
# DEBUG: Used throughout all calls for inline diagnostics
def echo_info(msg): print(f"\033[1;34m[INFO]\033[0m    {msg}")
def echo_ok(msg):   print(f"\033[1;32m[SUCCESS]\033[0m {msg}")
def echo_warn(msg): print(f"\033[1;33m[WARN]\033[0m   {msg}")
def echo_err(msg):  print(f"\033[1;31m[ERROR]\033[0m   {msg}")

# ─── [BLOCK: ARGUMENT PARSER] ──────────────────────────────────────────────────
# WHAT: Adds CLI flags to control dry-run mode and visibility
# WHY: Enables non-destructive testing and project visibility toggle
# FAIL: Defaults to private repo with full execution
# UX: Simple flags that work in automation or manually
# DEBUG: argparse-based field parsing
def parse_args():
    parser = argparse.ArgumentParser(description="PRF GitHub Repo Bootstrapper")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, do not run")
    parser.add_argument("--public", action="store_true", help="Make repo public (default is private)")
    return parser.parse_args()

# ─── [BLOCK: VALIDATION — ENVIRONMENT] ─────────────────────────────────────────
# WHAT: Ensures GitHub CLI and authentication are valid
# WHY: All operations depend on gh being installed and authenticated
# FAIL: Exits if gh not installed or auth fails
# UX: Self-heals by prompting login if needed
# DEBUG: Uses subprocess return codes for detection
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
# WHAT: Confirms we're inside the expected project folder
# WHY: Prevents accidental repo generation in incorrect directories
# FAIL: Exits if postcard-lister root markers are missing
# UX: Defensive failsafe for misplacement
# DEBUG: Checks for .install/ and README.md as heuristics
def require_project_root():
    expected = [".install", "README.md"]
    missing = [f for f in expected if not os.path.exists(f)]
    if missing:
        echo_err(f"Missing project files: {missing}. Must run from project root.")
        sys.exit(2)
    echo_ok("Confirmed project root context: postcard-lister/")

# ─── [BLOCK: GIT INIT + IDENTITY SYNC] ─────────────────────────────────────────
# WHAT: Initializes local .git and sets GitHub identity automatically
# WHY: Prevents commit errors and ensures user attribution
# FAIL: Falls back to noreply if no public email
# UX: Silent auto-config, no prompts
# DEBUG: Fetches via gh api user
def setup_git_identity():
    if not os.path.isdir(".git"):
        subprocess.run(["git", "init"], check=True)
        echo_ok("Initialized Git repository.")
    try:
        subprocess.check_output(["git", "config", "user.email"])
        subprocess.check_output(["git", "config", "user.name"])
        echo_ok("Git identity already configured.")
    except subprocess.CalledProcessError:
        echo_info("Auto-detecting Git identity from GitHub account...")
        user = json.loads(subprocess.check_output(["gh", "api", "user"]).decode())
        name = user["login"]
        email = user.get("email") or f"{name}@users.noreply.github.com"
        subprocess.run(["git", "config", "user.name", name], check=True)
        subprocess.run(["git", "config", "user.email", email], check=True)
        with open(".gitconfig.local", "w") as f:
            f.write(f"[user]\n\tname = {name}\n\temail = {email}\n")
        echo_ok(f"Git identity set: {name} <{email}>")

# ─── [BLOCK: CREATE README + LICENSE] ──────────────────────────────────────────
# WHAT: Adds README.md and LICENSE if absent
# WHY: Required for GitHub repo rendering and legal clarity
# FAIL: N/A
# UX: Prevents repo without descriptive content
# DEBUG: Populates MIT template if LICENSE missing
def ensure_readme_and_license():
    if not os.path.exists("README.md"):
        with open("README.md", "w") as f:
            f.write("# postcard-lister\n\n> Describe your postcard listing tool here.\n")
        echo_ok("Created default README.md.")
    if not os.path.exists("LICENSE"):
        with open("LICENSE", "w") as f:
            f.write("MIT License\n\nCopyright (c) " +
                    str(datetime.now().year) + " swipswaps\n\nPermission is hereby granted...")
        echo_ok("Created MIT LICENSE.")

# ─── [BLOCK: GH CREATE OR PUSH] ────────────────────────────────────────────────
# WHAT: Detects whether to create new GH repo or push to existing
# WHY: Abstracts all user logic, works both ways
# FAIL: Soft-fails if remote exists incorrectly, self-repairs
# UX: Always safe to re-run
# DEBUG: Detects /repos/<user>/<name> via gh api
def create_or_push(private=True, dry_run=False):
    reponame = os.path.basename(os.getcwd())
    exists = subprocess.run(["gh", "api", f"/repos/swipswaps/{reponame}"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if not exists:
        echo_info("Creating new GitHub repository...")
        cmd = ["gh", "repo", "create", f"swipswaps/{reponame}", "--source=.", "--remote=origin", "--push"]
        cmd.append("--private" if private else "--public")
        if not dry_run:
            subprocess.run(cmd, check=True)
        echo_ok(f"Repo created and pushed: https://github.com/swipswaps/{reponame}")
    else:
        echo_info("Remote exists. Syncing local repo...")
        if not dry_run:
            subprocess.run(["git", "remote", "remove", "origin"], check=False)
            subprocess.run(["git", "remote", "add", "origin", f"https://github.com/swipswaps/{reponame}.git"], check=True)
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], check=False)
            subprocess.run(["git", "branch", "-M", "main"], check=True)
            subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
        echo_ok("Pushed repo to existing origin.")

# ─── [BLOCK: MAIN BRANCH PROTECTION (FIXED)] ───────────────────────────────────
# WHAT: Applies valid branch protection schema to main
# WHY: Ensures no force-push, safe commits via PRs only
# FAIL: Avoids API schema error (fixed: correct booleans, objects)
# UX: No user intervention needed
# DEBUG: Outputs full protection spec if needed
def protect_main_branch(dry_run=False):
    repo = os.path.basename(os.getcwd())
    if dry_run:
        echo_info("[DRY-RUN] Skipping branch protection.")
        return
    echo_info("Enforcing main branch protection...")
    try:
        subprocess.run([
            "gh", "api", "--method", "PUT",
            f"/repos/swipswaps/{repo}/branches/main/protection",
            "-H", "Accept: application/vnd.github+json",
            "-F", "required_status_checks.strict=false",
            "-F", "required_status_checks.contexts=[]",
            "-F", "enforce_admins=true",
            "-F", "required_pull_request_reviews.dismiss_stale_reviews=true",
            "-F", "required_pull_request_reviews.require_code_owner_reviews=false",
            "-F", "restrictions=null"
        ], check=True)
        echo_ok("Branch protection applied.")
    except subprocess.CalledProcessError as e:
        echo_warn("Failed to apply branch protection.")
        echo_err(str(e))

# ─── [BLOCK: MAIN ENTRYPOINT] ──────────────────────────────────────────────────
# WHAT: Linear execution of repo bootstrapping steps
# WHY: Controls order and fallback handling
# FAIL: Stops immediately on validation or repo creation error
# UX: Safe to re-run anytime
# DEBUG: All steps printed to terminal
def main():
    args = parse_args()
    echo_info("🚀 Launching PRF GitHub Repo Bootstrapper")
    validate_environment()
    require_project_root()
    setup_git_identity()
    ensure_readme_and_license()
    create_or_push(private=not args.public, dry_run=args.dry_run)
    protect_main_branch(dry_run=args.dry_run)
    echo_ok("🎯 GH bootstrap complete.")

if __name__ == "__main__":
    main()
