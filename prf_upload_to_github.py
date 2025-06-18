#!/usr/bin/env python3
################################################################################
# 📦 prf_upload_to_github.py — MIL‑STD/PRF Enforced GitHub Uploader
# WHAT: Uploads current project to GitHub with full self-healing token and remote setup
# WHY: Avoids failures due to unset environment, missing remotes, and token push issues
# FAIL: Aborts with full error trace if any mandatory condition fails
# UX: Every step outputs clear, human-readable status or corrective action
# DEBUG: All subprocesses and environment checks are captured, verified, and logged
################################################################################

import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

# ─── PRF‑UPLOAD00: AUTO‑LOAD .ENV ─────────────────────────────────────────────
# WHAT: Automatically loads GH_TOKEN from .env if not exported
# WHY: Prevents user from having to manually export the token before each run
# FAIL: If token is not present after loading, script halts
# UX: Transparent load with fallback and confirmation output
# DEBUG: Uses python-dotenv
def autoload_dotenv_token():
    env_path = Path(".env")
    if env_path.exists():
        print("[INFO] 🧬 Loading .env file...")
        load_dotenv(dotenv_path=env_path)
        if os.environ.get("GH_TOKEN"):
            print("[PASS] ✅ GH_TOKEN loaded from .env.")
        else:
            print("[WARN] ⚠️ .env loaded, but GH_TOKEN not found.")
    else:
        print("[WARN] ⚠️ .env file not found. Continuing...")

# ─── PRF‑UPLOAD01: VERIFY GIT REPO ────────────────────────────────────────────
# WHAT: Confirms .git is present
# WHY: Prevents non-repo uploads
# FAIL: Exits if not a Git repo
# UX: Pass/fail message
# DEBUG: Filesystem path check
def assert_git_repo():
    if not Path(".git").exists():
        print("[FAIL] ❌ This is not a git repository.")
        sys.exit(1)
    print("[PASS] ✅ Git repository confirmed.")

# ─── PRF‑UPLOAD02: VERIFY GH_TOKEN ────────────────────────────────────────────
# WHAT: Ensures GH_TOKEN is set in environment
# WHY: Token authentication for GitHub HTTPS push
# FAIL: Script halts if token not found
# UX: Friendly instruction with visual
# DEBUG: os.environ access
def assert_gh_token():
    token = os.environ.get("GH_TOKEN", "").strip()
    if not token:
        print("[FAIL] ❌ GH_TOKEN is missing from environment.")
        print("👉 Export manually or add to .env as:")
        print("   GH_TOKEN=ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXX")
        sys.exit(1)
    print("[PASS] ✅ GH_TOKEN found in environment.")

# ─── PRF‑UPLOAD03: CONFIGURE REMOTE ───────────────────────────────────────────
# WHAT: Adds or rewrites 'origin' remote to use token
# WHY: Pushes require embedded token when using HTTPS
# FAIL: Push fails or access denied
# UX: Token URL masked, status shown
# DEBUG: subprocess call and string replacement
def configure_remote():
    username = "swipswaps"
    reponame = Path(".").resolve().name
    token = os.environ["GH_TOKEN"]
    token_url = f"https://{username}:{token}@github.com/{username}/{reponame}.git"
    try:
        current = subprocess.check_output(["git", "remote", "get-url", "origin"], text=True).strip()
        if "@" not in current:
            subprocess.run(["git", "remote", "set-url", "origin", token_url], check=True)
            print("[INFO] 🔁 Updated 'origin' remote with token.")
        else:
            print("[SKIP] ✅ Remote already tokenized.")
    except subprocess.CalledProcessError:
        subprocess.run(["git", "remote", "add", "origin", token_url], check=True)
        print("[INFO] 🆕 Added 'origin' remote with token.")

# ─── PRF‑UPLOAD04: COMMIT CHANGES IF ANY ──────────────────────────────────────
# WHAT: Commits staged or new files
# WHY: Push is blocked without commits
# FAIL: Uncommitted work = unsynced repo
# UX: Friendly commit message, dry status output
# DEBUG: git status used
def commit_if_needed():
    try:
        status = subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
        if status:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "[AUTO] PRF: GitHub sync commit"], check=True)
            print("[INFO] 📝 Changes committed.")
        else:
            print("[SKIP] ✅ No uncommitted changes.")
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] ❌ Commit step failed: {e}")
        sys.exit(1)

# ─── PRF‑UPLOAD05: PUSH TO ORIGIN BRANCH ──────────────────────────────────────
# WHAT: Pushes to tracked remote branch
# WHY: Synchronizes local state to GitHub
# FAIL: Authentication or connectivity issues block push
# UX: Confirms target branch
# DEBUG: git rev-parse used
def push_changes():
    try:
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
        subprocess.run(["git", "push", "-u", "origin", branch], check=True)
        print(f"[PASS] 🚀 Pushed to GitHub: origin/{branch}")
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] ❌ Push failed: {e}")
        sys.exit(1)

# ─── PRF‑UPLOAD06: MAIN EXECUTION ─────────────────────────────────────────────
# WHAT: Controls upload lifecycle
# WHY: Ensure PRF compliance through deterministic call chain
# FAIL: Any subprocess failure is logged and script exits
# UX: Standardized output trace
# DEBUG: All branches and remotes visible
def main():
    print("[PRF] 🛰 Beginning GitHub Upload Sequence")
    autoload_dotenv_token()
    assert_git_repo()
    assert_gh_token()
    configure_remote()
    commit_if_needed()
    push_changes()
    print("[PRF] ✅ Upload completed cleanly.")

if __name__ == "__main__":
    main()
