#!/usr/bin/env python3
################################################################################
# 📦 prf_upload_to_github.py — PRF-COMPLIANT SELF-HEALING GITHUB UPLOADER
# WHAT: Full GitHub uploader with .env fallback, token-safe remote rewriting, and auto-commit
# WHY: Automates GitHub sync without requiring manual token export, preventing authentication errors
# FAIL: Push failure from invalid token, missing remote, dirty working tree, or misconfigured branch
# UX: All output is human-readable, context-specific, and failsafe
# DEBUG: Subprocess return codes and token state explicitly traced
################################################################################

import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

# ─── PRF‑UPLOAD00: AUTO‑LOAD .ENV ─────────────────────────────────────────────
# WHAT: Loads .env to ensure GH_TOKEN is present in the environment
# WHY: Prevents authentication failures if user forgets to export manually
# FAIL: Git push fails silently or with vague error
# UX: Auto-fixes missing export, explains fallback method
# DEBUG: Checks environment before and after .env load
def autoload_dotenv_token():
    env_path = Path(".env")
    if not os.environ.get("GH_TOKEN") and env_path.exists():
        print("[INFO] 🧬 Attempting to load GH_TOKEN from .env...")
        load_dotenv(dotenv_path=env_path)
        if os.environ.get("GH_TOKEN"):
            print("[PASS] ✅ GH_TOKEN successfully loaded from .env.")
        else:
            print("[FAIL] ❌ .env loaded but GH_TOKEN missing.")
            sys.exit(1)
    elif os.environ.get("GH_TOKEN"):
        print("[SKIP] ✅ GH_TOKEN already in environment.")
    else:
        print("[WARN] ⚠ No .env file found and GH_TOKEN not exported.")
        sys.exit(1)

# ─── PRF‑UPLOAD01: VERIFY GIT REPO ────────────────────────────────────────────
# WHAT: Confirms working directory is a git repo
# WHY: Prevents push attempts in invalid contexts
# FAIL: Cannot push without valid .git repo
# UX: Fails early with clear fix
# DEBUG: Path existence check
def assert_git_repo():
    if not Path(".git").exists():
        print("[FAIL] ❌ This is not a git repository (missing .git).")
        sys.exit(1)
    print("[PASS] ✅ Git repository detected.")

# ─── PRF‑UPLOAD02: VALIDATE GH_TOKEN ─────────────────────────────────────────
# WHAT: Ensures token is present and non-empty
# WHY: GitHub removed password auth; token is mandatory
# FAIL: Push returns HTTP 403 or authentication prompt
# UX: Explicit export instructions shown
# DEBUG: Environment variable check
def assert_gh_token():
    token = os.environ.get("GH_TOKEN", "").strip()
    if not token:
        print("[FAIL] ❌ GH_TOKEN not set.")
        print("👉 Add GH_TOKEN to .env or export manually before running.")
        sys.exit(1)
    print("[PASS] ✅ GH_TOKEN verified.")

# ─── PRF‑UPLOAD03: AUTO-CONFIGURE TOKENIZED REMOTE ───────────────────────────
# WHAT: Ensures origin remote uses token-based URL
# WHY: Avoids prompt-based auth failures or 403s
# FAIL: Remote misconfigured or missing leads to push failure
# UX: Rewrites safely with visible status
# DEBUG: Checks for `@` in URL to detect credential embedding
def configure_remote():
    username = "swipswaps"
    reponame = Path(".").resolve().name
    token = os.environ["GH_TOKEN"]
    token_url = f"https://{username}:{token}@github.com/{username}/{reponame}.git"
    try:
        current = subprocess.check_output(["git", "remote", "get-url", "origin"], text=True).strip()
        if "@" not in current:
            subprocess.run(["git", "remote", "set-url", "origin", token_url], check=True)
            print("[INFO] 🔁 Updated remote 'origin' with token-auth URL.")
        else:
            print("[SKIP] ✅ Remote already tokenized.")
    except subprocess.CalledProcessError:
        subprocess.run(["git", "remote", "add", "origin", token_url], check=True)
        print("[INFO] 🆕 Remote 'origin' added using token-auth.")

# ─── PRF‑UPLOAD04: AUTO-COMMIT UNSTAGED CHANGES ──────────────────────────────
# WHAT: Commits changes before push to prevent rejection
# WHY: Git does not allow empty pushes
# FAIL: Skipped commit leads to dirty state mismatch
# UX: Auto-message used, no user interaction
# DEBUG: Uses porcelain for clean status parsing
def commit_if_needed():
    try:
        status = subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
        if status:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "[AUTO] PRF: GitHub sync commit"], check=True)
            print("[INFO] 📝 Changes committed.")
        else:
            print("[SKIP] ✅ Working tree clean. No commit needed.")
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] ❌ Git commit failed: {e}")
        sys.exit(1)

# ─── PRF‑UPLOAD05: PUSH TO CURRENT BRANCH ─────────────────────────────────────
# WHAT: Pushes committed changes to remote
# WHY: Syncs current repo to GitHub
# FAIL: Errors if branch not tracked or remote inaccessible
# UX: Always reports exact branch and push status
# DEBUG: Reads current HEAD name and confirms push
def push_to_github():
    try:
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
        subprocess.run(["git", "push", "-u", "origin", branch], check=True)
        print(f"[PASS] 🚀 Push to GitHub successful: origin/{branch}")
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] ❌ Push to GitHub failed: {e}")
        sys.exit(1)

# ─── PRF‑UPLOAD06: MAIN ──────────────────────────────────────────────────────
# WHAT: Executes full upload lifecycle
# WHY: Deterministically enforces all PRF rules
# FAIL: Halts at first failure with full reason
# UX: Begins and ends with standardized messages
# DEBUG: Step-by-step trace visible
def main():
    print("[PRF] 🛰 GitHub Upload Start")
    autoload_dotenv_token()
    assert_git_repo()
    assert_gh_token()
    configure_remote()
    commit_if_needed()
    push_to_github()
    print("[PRF] ✅ GitHub Upload Completed Cleanly")

if __name__ == "__main__":
    main()
