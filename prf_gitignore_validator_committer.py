#!/usr/bin/env python3
################################################################################
# 📜 prf_gitignore_validator_committer.py — PRF-COMPLIANT GITIGNORE PATCHER
# WHAT: Ensures `.gitignore` exists and contains full set of entries required
# WHY: Prevents accidental commits of sensitive, environment-specific, or temp files
# FAIL: Exits with descriptive failure if `.gitignore` is unwritable
# UX: Full autocompletion of missing rules; emits diff, counts, and result
# DEBUG: Emits patch log and total count patched
################################################################################

import os
import sys
from pathlib import Path

# ─── PRF-P01: DEFINE REQUIRED ENTRIES ─────────────────────────────────────────
REQUIRED_ENTRIES = [
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

# ─── PRF-P02: ENSURE .GITIGNORE FILE EXISTS ──────────────────────────────────
def ensure_gitignore_exists(path: Path):
    if not path.exists():
        print("[INFO] 🧱 No .gitignore found — creating new file.")
        try:
            path.write_text("")
        except Exception as e:
            print(f"[FAIL] ❌ Failed to create .gitignore: {e}")
            sys.exit(1)

# ─── PRF-P03: READ EXISTING ENTRIES SAFELY ────────────────────────────────────
def load_existing_entries(path: Path):
    try:
        lines = path.read_text().splitlines()
        return set(line.strip() for line in lines if line.strip())
    except Exception as e:
        print(f"[FAIL] ❌ Cannot read .gitignore: {e}")
        sys.exit(1)

# ─── PRF-P04: DETERMINE WHICH ENTRIES ARE MISSING ─────────────────────────────
def compute_missing(required, existing):
    return [entry for entry in required if entry not in existing]

# ─── PRF-P05: APPLY PATCH TO GITIGNORE ────────────────────────────────────────
def apply_patch(path: Path, missing_entries):
    if not missing_entries:
        print("[PASS] ✅ .gitignore already contains all required entries.")
        return

    print("[INFO] 📌 Patching .gitignore with missing entries:")
    try:
        with path.open("a") as f:
            f.write("\n# ─── PRF-AUTO-GENERATED ENTRIES ───\n")
            for entry in missing_entries:
                f.write(f"{entry}\n")
                print(f"[PATCHED] ➕ {entry}")
    except Exception as e:
        print(f"[FAIL] ❌ Unable to write to .gitignore: {e}")
        sys.exit(1)

    print(f"[PASS] ✅ .gitignore patched with {len(missing_entries)} entries.")

# ─── PRF-P06: MAIN ENTRYPOINT ─────────────────────────────────────────────────
def main():
    repo_root = Path.cwd()
    gitignore_path = repo_root / ".gitignore"

    ensure_gitignore_exists(gitignore_path)
    existing_entries = load_existing_entries(gitignore_path)
    missing_entries = compute_missing(REQUIRED_ENTRIES, existing_entries)
    apply_patch(gitignore_path, missing_entries)

if __name__ == "__main__":
    main()
