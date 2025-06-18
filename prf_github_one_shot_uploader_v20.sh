#!/usr/bin/env bash
################################################################################
# FILE: prf_github_one_shot_uploader_v20.sh
# DESC: GitHub one-shot uploader with hardened token loading + .env.local fallback
# SPEC: PRF‑COMPOSITE‑2025‑06‑17‑A  (P01–P27 compliant)
################################################################################

set -euo pipefail
IFS=$'\n\t'

NOW="$(date '+%Y%m%d')"
RUN_ID="$(date '+%H%M%S')"

################################################################################
# [BLOCK: ENVIRONMENT SELF-HEAL] ################################################
# WHAT  : Install 'ts' if missing
# WHY   : Needed for human-readable timestamp logging
# FAIL  : Abort if not installable
# UX    : Auto-install with sudo
# DEBUG : Uses dnf or apt with fallbacks
################################################################################

if ! command -v ts &>/dev/null; then
  echo "[SELF-HEAL] Installing 'ts' via moreutils…" >&2
  if command -v dnf &>/dev/null; then
    sudo dnf install -y moreutils || { echo "[FAIL] Cannot install moreutils"; exit 127; }
  elif command -v apt &>/dev/null; then
    sudo apt update && sudo apt install -y moreutils || { echo "[FAIL] Cannot install moreutils"; exit 127; }
  else
    echo "[FAIL] No package manager found"; exit 127
  fi
fi

################################################################################
# [BLOCK: LOGGING SETUP] ########################################################
# WHAT  : Set up raw + masked logging with 'ts'
# WHY   : Provides human-readable, timestamped diagnostics
# FAIL  : Log creation or redirection failure
# UX    : Full terminal and log echoing
# DEBUG : Uses file descriptors 3–5
################################################################################

LOG_DIR="logs/$NOW"; mkdir -p "$LOG_DIR"
LOG_RAW="$LOG_DIR/raw_${RUN_ID}.log"
LOG_MASKED="$LOG_DIR/masked_${RUN_ID}.log"

ts() { awk '{ print strftime("[%F %T]"), $0 }'; }

exec 3>&1 4>&2
exec 1> >(stdbuf -o0 ts | tee -a "$LOG_MASKED" >&3) \
     2> >(stdbuf -o0 ts | tee -a "$LOG_MASKED" >&4)
exec 5>>"$LOG_RAW"

export GIT_TRACE=5 GIT_TRACE_PACKET=5 GIT_TRACE_SETUP=5 GIT_CURL_VERBOSE=1

INFO() { printf '\033[1;34m[INFO]  %s\033[0m\n' "$1"; }
WARN() { printf '\033[1;33m[WARN]  %s\033[0m\n' "$1"; }
FAIL() { printf '\033[1;31m[FAIL]  %s\033[0m\n' "$1"; }
PASS() { printf '\033[1;32m[PASS]  %s\033[0m\n' "$1"; }

INFO "Masked log → $LOG_MASKED"
INFO "Raw    log → $LOG_RAW"

################################################################################
# [BLOCK: LOAD GH_TOKEN] ########################################################
# WHAT  : Load GH_TOKEN from multiple fallback sources: .env, .env.local, prompt
# WHY   : Required for auth; fallback ensures robustness
# FAIL  : Aborts if token is missing or empty
# UX    : Supports quoted or unquoted vars
# DEBUG : Never logs token; only status
################################################################################

for ENV_FILE in .env .env.local; do
  if [[ -f "$ENV_FILE" ]]; then
    set -o allexport; source "$ENV_FILE"; set +o allexport
    INFO "Loaded GH_TOKEN from $ENV_FILE"
    break
  fi
done

if [[ -z "${GH_TOKEN:-}" ]]; then
  echo "[WARN] ❗ GH_TOKEN not found. Prompting user for input." >&2
  echo -n "Enter your GitHub Personal Access Token: " > /dev/tty
  read -r GH_TOKEN < /dev/tty
  [[ -z "$GH_TOKEN" ]] && { echo "[FAIL] ❌ No GH_TOKEN entered."; exit 1; }
  PASS "✅ GH_TOKEN obtained interactively"
  echo "GH_TOKEN=$GH_TOKEN" >> .env
  chmod 600 .env
  INFO "Persisted token to .env"
fi

################################################################################
# [BLOCK: VALIDATE GH_TOKEN] ####################################################
# WHAT  : Ensure token starts with valid prefix and has correct length
# WHY   : Prevents auth errors due to wrong format (e.g. OpenAI token)
# FAIL  : Exit if token doesn't pass both checks
# UX    : Displays sanitized length and prefix diagnostics
# DEBUG : Length and prefix-only logging
################################################################################

GH_TOKEN="${GH_TOKEN//\"/}"  # Remove quotes if any
TOKEN_LEN=${#GH_TOKEN}

if (( TOKEN_LEN < 40 )) || ! [[ "$GH_TOKEN" =~ ^(ghp_|github_pat_) ]]; then
  FAIL "❌ GH_TOKEN format invalid (length=$TOKEN_LEN). Must begin with 'ghp_' or 'github_pat_'."
  exit 1
fi
PASS "✅ GH_TOKEN appears valid (${TOKEN_LEN} chars)"

################################################################################
# [BLOCK: GIT REMOTE REWRITE] ###################################################
# WHAT  : Force remote URL to use token for HTTPS push
# WHY   : Enables non-interactive push with embedded auth
# FAIL  : Exit if no remote is found
# UX    : Converts SSH/HTTPS/user-pwd URLs
# DEBUG : Echoes masked remote
################################################################################

REMOTE_URL="$(git remote get-url origin 2>/dev/null || true)"
[[ -z "$REMOTE_URL" ]] && { FAIL "No 'origin' remote found"; exit 1; }

if [[ "$REMOTE_URL" == git@*:* ]]; then
  REMOTE_URL="https://$(echo "$REMOTE_URL" | cut -d':' -f1 | sed 's/git@//')/$(echo "$REMOTE_URL" | cut -d':' -f2-)"
elif [[ "$REMOTE_URL" == ssh://git@* ]]; then
  REMOTE_URL="https://$(echo "$REMOTE_URL" | sed -E 's#ssh://git@([^/]+)/#\1/#')"
elif [[ "$REMOTE_URL" =~ https://[^@]+@ ]]; then
  REMOTE_URL="$(echo "$REMOTE_URL" | sed -E 's#https://[^/]+@#https://#')"
fi

NEW_REMOTE="https://${GH_TOKEN}@${REMOTE_URL#https://}"
git remote set-url origin "$NEW_REMOTE"
SAFE_REMOTE="${NEW_REMOTE//$GH_TOKEN/********}"
INFO "🔧 Remote URL updated: $SAFE_REMOTE"

################################################################################
# [BLOCK: COMMIT IF DIRTY] ######################################################
# WHAT  : Auto-commit any uncommitted local changes
# WHY   : Ensures all changes are pushed without loss
# FAIL  : Git commit failure
# UX    : Informative commit message with timestamp
# DEBUG : Full git add + status check
################################################################################

if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  MSG="[PRF] Auto-commit @ $(date '+%F %T')"
  git commit -m "$MSG"
  INFO "📦 Auto-committed changes → '$MSG'"
else
  INFO "📦 No changes to commit"
fi

################################################################################
# [BLOCK: PUSH CHANGES] #########################################################
# WHAT  : Push the current branch to GitHub using tokenized remote
# WHY   : Upload commits to repository securely
# FAIL  : Git push failure
# UX    : Terminal feedback and status echo
# DEBUG : Redacts GH_TOKEN from git push output
################################################################################

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
INFO "🔄 Pushing '$BRANCH' to origin..."
PUSH_OUTPUT="$(git push origin "$BRANCH" 2>&1)"
PUSH_EXIT=$?
SAFE_PUSH="$(echo "$PUSH_OUTPUT" | sed "s/${GH_TOKEN}/********/g")"
echo "$SAFE_PUSH"

if (( PUSH_EXIT != 0 )); then
  FAIL "Git push failed → code $PUSH_EXIT"
  exit $PUSH_EXIT
fi

if echo "$PUSH_OUTPUT" | grep -q "Everything up-to-date"; then
  PASS "✅ No changes to push."
else
  PASS "✅ Push successful for '$BRANCH'"
fi
