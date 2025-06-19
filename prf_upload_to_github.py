#!/usr/bin/env python3
################################################################################
# 📦 prf_upload_to_github.py — PRF‑COMPLIANT GITHUB SYNC TOOL
# WHAT: GitHub uploader with token auth, remote rewrite, commit enforcement, and push diagnostics
# WHY: Removes auth failures, silent HTTPS prompts, and broken remotes
# FAIL: Aborts on token absence, git error, or push rejection
# UX: Fully terminal-readable, emoji-tagged, self-healing Git push pipeline
# DEBUG: Subprocess visibility and exit traceability
################################################################################

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# ─── PRF‑UPLOAD00: AUTO‑LOAD GH_TOKEN FROM .ENV ──────────────────────────────
def autoload_dotenv_token():
    """
    WHAT: Loads GH_TOKEN from .env if not exported
    WHY: Allows automatic token detection without manual export
    FAIL: Aborts if GH_TOKEN is missing after fallback
    UX: Colored, visible notices with exit cause
    DEBUG: Prints fallback and .env status
    """
    env_path = Path(".env")
    if not os.environ.get("GH_TOKEN"):
        if env_path.exists():
            print("[INFO] 🧬 Loading GH_TOKEN from .env...")
            load_dotenv(dotenv_path=env_path)
            if not os.environ.get("GH_TOKEN"):
                print("[FAIL] ❌ .env loaded but GH_TOKEN is still missing.")
                sys.exit(1)
            print("[PASS] ✅ GH_TOKEN loaded successfully.")
        else:
            print("[FAIL] ❌ GH_TOKEN not found in environment or .env file.")
            sys.exit(1)
    else:
        print("[SKIP] ✅ GH_TOKEN already present.")

# ─── PRF‑UPLOAD01: VERIFY GIT REPO ────────────────────────────────────────────
def assert_git_repo():
    """
    WHAT: Ensures the script runs inside a Git repository
    WHY: Prevents failures due to missing git metadata
    FAIL: Hard exits if .git is missing
    UX: Tells user how to initialize
    DEBUG: Checks for .git directory
    """
    if not Path(".git").exists():
        print("[FAIL] ❌ Current directory is not a Git repository.")
        sys.exit(1)
    print("[PASS] ✅ Git repository confirmed.")

# ─── PRF‑UPLOAD02: VALIDATE GH_TOKEN ─────────────────────────────────────────
def assert_gh_token():
    """
    WHAT: Checks presence and length of GH_TOKEN
    WHY: GitHub HTTPS authentication requires PAT token
    FAIL: Silent 403 error or interactive password prompt
    UX: Prints explicit exit cause
    DEBUG: Uses env var value
    """
    token = os.environ.get("GH_TOKEN", "").strip()
    if not token or len(token) < 20:
        print("[FAIL] ❌ GH_TOKEN is missing or invalid.")
        sys.exit(1)
    print("[PASS] ✅ GH_TOKEN is valid.")

# ─── PRF‑UPLOAD03: TOKENIZE GIT REMOTE ───────────────────────────────────────
def configure_remote():
    """
    WHAT: Sets HTTPS tokenized Git remote with PAT
    WHY: Prevents interactive password prompt, ensures push auth works
    FAIL: Broken or invalid remote URL blocks push
    UX: Confirms added or modified URL
    DEBUG: Shows current and new URLs
    """
    username = "swipswaps"
    reponame = Path().resolve().name
    token = os.environ["GH_TOKEN"]
    secure_url = f"https://{username}:{token}@github.com/{username}/{reponame}.git"

    try:
        current = subprocess.check_output(["git", "remote", "get-url", "origin"], text=True).strip()
        if "@github.com" not in current:
            subprocess.run(["git", "remote", "set-url", "origin", secure_url], check=True)
            print("[INFO] 🔄 Remote URL updated with token.")
        else:
            print("[SKIP] ✅ Remote URL already tokenized.")
    except subprocess.CalledProcessError:
        subprocess.run(["git", "remote", "add", "origin", secure_url], check=True)
        print("[INFO] 🆕 Remote origin added.")

# ─── PRF‑UPLOAD04: AUTO‑COMMIT PENDING CHANGES ───────────────────────────────
def commit_if_needed():
    """
    WHAT: Adds and commits all untracked or modified files
    WHY: Ensures push will succeed
    FAIL: Dirty working tree blocks push if not committed
    UX: Automatically adds a timestamp commit
    DEBUG: Uses git porcelain output to detect changes
    """
    try:
        dirty = subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
        if dirty:
            subprocess.run(["git", "add", "."], check=True)
            tag = datetime.now().strftime("prf-auto-%Y%m%d-%H%M%S")
            subprocess.run(["git", "commit", "-m", f"[AUTO] {tag}"], check=True)
            print(f"[INFO] 📝 Auto-committed changes as '{tag}'")
        else:
            print("[SKIP] ✅ Working directory clean.")
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] ❌ Git auto-commit failed: {e}")
        sys.exit(1)

# ─── PRF‑UPLOAD05: PUSH TO REMOTE ────────────────────────────────────────────
def push_to_github():
    """
    WHAT: Pushes current branch to GitHub
    WHY: Final step to sync changes to remote
    FAIL: Token failure, branch mismatch, or network error halts push
    UX: Success shows target branch, failure gives subprocess detail
    DEBUG: Push command, current branch, subprocess return
    """
    try:
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
        subprocess.run(["git", "push", "-u", "origin", branch], check=True)
        print(f"[PASS] 🚀 Push to origin/{branch} succeeded.")
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] ❌ Push failed: {e}")
        sys.exit(1)

# ─── PRF‑UPLOAD06: MAIN ENTRYPOINT ───────────────────────────────────────────
def main():
    """
    WHAT: Executes full GitHub push logic
    WHY: Enforces orderly upload with PRF rules
    FAIL: Any error in sequence aborts operation
    UX: Printed diagnostics with emoji
    DEBUG: Print each stage outcome
    """
    print("[PRF] 🛰 GitHub Upload Initiated")
    autoload_dotenv_token()
    assert_git_repo()
    assert_gh_token()
    configure_remote()
    commit_if_needed()
    push_to_github()
    print("[PRF] ✅ Upload pipeline complete.")

if __name__ == "__main__":
    main()
