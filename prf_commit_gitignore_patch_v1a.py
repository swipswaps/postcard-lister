#!/usr/bin/env python3
################################################################################
# 📜 prf_commit_gitignore_patch_v1a.py — PRF-COMPLIANT GITIGNORE PATCHER
# WHAT: Ensures `.gitignore` exists and includes required entries
# WHY: Prevents committing sensitive, platform, or environment-specific files
# FAIL: Script exits with error if unable to write or patch `.gitignore`
# UX: Fully automated patching of missing entries, emits diff summary
# DEBUG: Logs all patch states and outcomes
################################################################################

import os
import sys
from pathlib import Path

# ─── ENVIRONMENT VALIDATION ───────────────────────────────────────────────────
repo_root = Path.cwd()
gitignore_path = repo_root / ".gitignore"

# ─── REQUIRED ENTRIES ─────────────────────────────────────────────────────────
required_entries = [
    ".env",
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".vscode/",
    ".idea/",
    ".DS_Store",
    "*.egg-info/",
    "dist/",
    "build/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".coverage",
    "htmlcov/",
    "coverage.xml",
    ".venv/",
    "*.log",
    "*.sqlite3",
    ".ipynb_checkpoints/",
    ".parcel-cache/",
    "node_modules/"
]

# ─── STEP 1: ENSURE FILE EXISTS ───────────────────────────────────────────────
if not gitignore_path.exists():
    print("[INFO] 🧱 No .gitignore found — creating.")
    gitignore_path.write_text("")  # create blank file

# ─── STEP 2: PARSE EXISTING CONTENT ───────────────────────────────────────────
existing_lines = set(
    line.strip() for line in gitignore_path.read_text().splitlines() if line.strip()
)

# ─── STEP 3: DETERMINE PATCHES ────────────────────────────────────────────────
missing = [entry for entry in required_entries if entry not in existing_lines]

if not missing:
    print("[PASS] ✅ .gitignore already contains all required entries.")
    sys.exit(0)

# ─── STEP 4: APPLY PATCHES ────────────────────────────────────────────────────
with open(gitignore_path, "a") as f:
    f.write("\n# ─── PRF-AUTO-GENERATED ENTRIES ───\n")
    for entry in missing:
        f.write(f"{entry}\n")
        print(f"[PATCHED] ➕ {entry}")

print(f"[PASS] ✅ .gitignore patched with {len(missing)} missing entries.")
