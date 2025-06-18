#!/usr/bin/env python3
################################################################################
# 📦 prf_upload_to_github.py — PRF‑COMPLIANT GITHUB SYNC TOOL
# WHAT: Full GitHub automation script with .env fallback, token verification, auto-remote correction, and commit+push enforcement
# WHY: Prevents GitHub push failure due to missing tokens, dirty states, or unconfigured remotes
# FAIL: Fails cleanly with readable diagnostics if token, repo, or network is broken
# UX: All steps output clear emoji-annotated feedback for traceability
# DEBUG: Verbose subprocess error handling with visible exit codes
################################################################################

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# ─── PRF‑UPLOAD00: AUTO‑LOAD GH_TOKEN FROM .ENV ──────────────────────────────
def autoload_dotenv_token():
    """
    WHAT: Loads GH_TOKEN from .env if not present
    WHY: Prevents failures caused by unset environment variables
    FAIL: Aborts if GH_TOKEN is not loaded successfully
    UX: Prints token source, exit if missing
    DEBUG: Checks env var state after .env load
    """
    env_path = Path(".env")
    if not os.environ.get("GH_TOKEN"):
        if env_path.exists():
            print("[INFO] 🧬 Loading GH_TOKEN from .env...")
            load_dotenv(dotenv_path=env_path)
            if not os.environ.get("GH_TOKEN"):
                print("[FAIL] ❌ .env loaded, but GH_TOKEN still missing.")
                sys.exit(1)
            print("[PASS] ✅ GH_TOKEN loaded successfully from .env.")
        else:
            print("[FAIL] ❌ .env file not found, and GH_TOKEN not exported.")
            sys.exit(1)
    else:
        print("[SKIP] ✅ GH_TOKEN already present in environment.")

# ─── PRF‑UPLOAD01: VERIFY GIT REPO ────────────────────────────────────────────
def assert_git_repo():
    """
    WHAT: Ensures current directory is a Git repository
    WHY: Git operations require .git metadata
    FAIL: Aborts if .git not present
    UX: Prints helpful message if invalid
    DEBUG: Checks for .git folder
    """
    if not Path(".git").exists():
        print("[FAIL] ❌ Current directory is not a Git repo.")
        sys.exit(1)
    print("[PASS] ✅ Git repository verified.")

# ─── PRF‑UPLOAD02: VERIFY GH_TOKEN ────────────────────────────────────────────
def assert_gh_token():
    """
    WHAT: Checks that GH_TOKEN is set and not empty
    WHY: GitHub requires PAT (token) authentication for HTTPS
    FAIL: Push attempts silently fail or prompt unexpectedly
    UX: Visible exit path and export hints
    DEBUG: Pulls value from environment
    """
    token = os.environ.get("GH_TOKEN", "").strip()
    if not token:
        print("[FAIL] ❌ GH_TOKEN not set.")
        print("👉 Add to .env or export GH_TOKEN before running.")
        sys.exit(1)
    print("[PASS] ✅ GH_TOKEN is present and non-empty.")

# ─── PRF‑UPLOAD03: TOKENIZE ORIGIN REMOTE ─────────────────────────────────────
def configure_remote():
    """
    WHAT: Configures Git remote with token-based URL
    WHY: Prevents push prompt and 403 errors
    FAIL: Fails if repo name or token missing
    UX: Prints remote status
    DEBUG: Shows changed or skipped remote config
    """
    username = "swipswaps"
    reponame = Path(".").resolve().name
    token = os.environ["GH_TOKEN"]
    secure_url = f"https://{username}:{token}@github.com/{username}/{reponame}.git"

    try:
        current_url = subprocess.check_output(["git", "remote", "get-url", "origin"], text=True).strip()
        if "@" not in current_url:
            subprocess.run(["git", "remote", "set-url", "origin", secure_url], check=True)
            print("[INFO] 🔁 Remote URL updated with token auth.")
        else:
            print("[SKIP] ✅ Remote already tokenized.")
    except subprocess.CalledProcessError:
        subprocess.run(["git", "remote", "add", "origin", secure_url], check=True)
        print("[INFO] 🆕 Added tokenized 'origin' remote.")

# ─── PRF‑UPLOAD04: AUTO-COMMIT IF DIRTY ───────────────────────────────────────
def commit_if_needed():
    """
    WHAT: Auto-commits changes before push
    WHY: Prevents push failures due to uncommitted work
    FAIL: Git rejects push if repo is dirty
    UX: Uses standard auto-message
    DEBUG: Git status used for decision
    """
    try:
        status = subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
        if status:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "[AUTO] PRF sync commit"], check=True)
            print("[INFO] 📝 Auto-committed local changes.")
        else:
            print("[SKIP] ✅ No changes to commit.")
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] ❌ Auto-commit failed: {e}")
        sys.exit(1)

# ─── PRF‑UPLOAD05: PUSH TO CURRENT BRANCH ─────────────────────────────────────
def push_to_github():
    """
    WHAT: Pushes committed changes to GitHub
    WHY: Uploads local repo state to remote
    FAIL: Push fails with auth, net, or tracking errors
    UX: Branch shown in success or failure
    DEBUG: Full subprocess error logged
    """
    try:
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
        subprocess.run(["git", "push", "-u", "origin", branch], check=True)
        print(f"[PASS] 🚀 Push successful: origin/{branch}")
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] ❌ Push failed with error: {e}")
        sys.exit(1)

# ─── PRF‑UPLOAD06: MAIN ENTRYPOINT ────────────────────────────────────────────
def main():
    """
    WHAT: Orchestrates full upload process
    WHY: Ensures all prerequisites validated and fixable
    FAIL: Exits early if any step fails
    UX: Consistent entry/exit messages
    DEBUG: Steps are visibly sequenced
    """
    print("[PRF] 🛰 GitHub Upload Initiated")
    autoload_dotenv_token()
    assert_git_repo()
    assert_gh_token()
    configure_remote()
    commit_if_needed()
    push_to_github()
    print("[PRF] ✅ GitHub Upload Completed")

if __name__ == "__main__":
    main()
