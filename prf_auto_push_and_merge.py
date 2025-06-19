#!/usr/bin/env python3
################################################################################
# 📜 prf_auto_push_and_merge.py — PRF-COMPLIANT AUTO PUSH & PR MERGE SCRIPT
# WHAT: Pushes all committed changes, creates a pull request, and attempts merge
# WHY: Prevents human error and enforces consistent GitHub workflow policy
# FAIL: Exits with descriptive error if GitHub CLI or required env is broken
# UX: Self-healing auto-push and PR merge; fallbacks to draft with comment
# DEBUG: Emits each subprocess and merge path state clearly
################################################################################

import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

# ─── PRF‑P01: ENVIRONMENT PRECHECK ────────────────────────────────────────────
def ensure_gh_installed():
    try:
        subprocess.run(["gh", "--version"], check=True, stdout=subprocess.DEVNULL)
    except Exception:
        print("[FAIL] ❌ GitHub CLI not found — install `gh` before proceeding.")
        sys.exit(1)

# ─── PRF‑P02: VALIDATE TOKEN ──────────────────────────────────────────────────
def ensure_token():
    dotenv_path = Path(".env")
    if not dotenv_path.exists():
        dotenv_path.write_text("GH_TOKEN=__REPLACE_ME__\n")
        print("[INFO] 🔑 .env created — add a valid GH_TOKEN and re-run.")
        sys.exit(1)
    with open(dotenv_path) as f:
        for line in f:
            if line.startswith("GH_TOKEN="):
                token = line.strip().split("=", 1)[-1]
                if token and "__REPLACE_ME__" not in token:
                    os.environ["GH_TOKEN"] = token
                    return
    print("[FAIL] ❌ Invalid or missing GH_TOKEN in .env.")
    sys.exit(1)

# ─── PRF‑P03: GIT PUSH AND BRANCH CREATION ────────────────────────────────────
def create_branch_and_push():
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    branch = f"prf-auto-{timestamp}"
    try:
        subprocess.run(["git", "checkout", "-b", branch], check=True)
        subprocess.run(["git", "push", "-u", "origin", branch], check=True)
        return branch
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] ❌ Git branch/push failed: {e}")
        sys.exit(1)

# ─── PRF‑P04: CREATE PR AND ATTEMPT MERGE ─────────────────────────────────────
def create_pr(branch):
    try:
        subprocess.run(["gh", "pr", "create", "--fill", "--head", branch], check=True)
        subprocess.run(["gh", "pr", "merge", "--auto", "--squash"], check=True)
        print("[PASS] ✅ PR merged automatically.")
    except subprocess.CalledProcessError as e:
        print("[WARN] ⚠️ Auto-merge failed. Attempting fallback.")
        fallback_draft(branch)

# ─── PRF‑P05: FALLBACK — DRAFT + COMMENT IF BLOCKED ───────────────────────────
def fallback_draft(branch):
    try:
        subprocess.run(["gh", "pr", "edit", "--add-label", "needs-review"], check=True)
        subprocess.run(["gh", "pr", "edit", "--title", f"📌 Draft: {branch}"], check=True)
        subprocess.run([
            "gh", "pr", "comment", "--body",
            "🔒 Auto-merge failed due to reviewer policy. Manual intervention required."
        ], check=True)
        subprocess.run(["gh", "pr", "edit", "--draft"], check=True)
        print("[INFO] 📝 PR marked as draft with fallback label/comment.")
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] ❌ Fallback failed: {e}")
        sys.exit(1)

# ─── PRF‑P06: MAIN ENTRYPOINT ─────────────────────────────────────────────────
def main():
    ensure_gh_installed()
    ensure_token()
    branch = create_branch_and_push()
    create_pr(branch)

if __name__ == "__main__":
    main()
