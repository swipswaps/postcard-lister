#!/usr/bin/env bash
################################################################################
# FILE: prf_github_one_shot_uploader_v22.sh
# DESC: Hardened GitHub uploader with real-time logs, token validation, and PRF logs
# SPEC: PRF‑COMPOSITE‑2025‑06‑18‑A (P01–P27 compliant)
################################################################################

set -euo pipefail
IFS=$'\n\t'
NOW="$(date '+%Y%m%d')"
RUN_ID="$(date '+%H%M%S')"

# WHAT: Ensure required CLI tools are installed (ts from moreutils)
# WHY: We require `ts` for timestamping logs.
# FAIL: Exits if package manager or install fails
# UX: User sees [SELF-HEAL] and [FAIL] messages
# DEBUG: Diagnoses package manager presence
if ! command -v ts &>/dev/null; then
  echo "[SELF-HEAL] Installing 'ts' from moreutils…" >&2
  if command -v dnf &>/dev/null; then
    sudo dnf install -y moreutils || { echo "[FAIL] dnf could not install moreutils"; exit 127; }
  elif command -v apt &>/dev/null; then
    sudo apt update && sudo apt install -y moreutils || { echo "[FAIL] apt could not install moreutils"; exit 127; }
  else
    echo "[FAIL] No known package manager detected."; exit 127
  fi
fi

# WHAT: Prepare structured logging
# WHY: We need both masked and raw logs to satisfy PRF-P12 and PRF-P21
# FAIL: Logging setup must never silently fail
# UX: Output visible log path and log to disk
# DEBUG: LOG_MASKED captures user-facing data, LOG_RAW captures full internal events
LOG_DIR="logs/$NOW"
mkdir -p "$LOG_DIR"
LOG_RAW="$LOG_DIR/raw_${RUN_ID}.log"
LOG_MASKED="$LOG_DIR/masked_${RUN_ID}.log"

ts() { awk '{ print strftime("[%F %T]"), $0 }'; }

exec 3>&1 4>&2
exec 1> >(stdbuf -o0 ts | tee -a "$LOG_MASKED" >&3) \
     2> >(stdbuf -o0 ts | tee -a "$LOG_MASKED" >&4)
exec 5>>"$LOG_RAW"

# WHAT: Enable full diagnostic output from git
# WHY: Critical for diagnosing GitHub push/auth failures
# DEBUG: GIT_TRACE shows internal git logic, GIT_CURL_VERBOSE shows HTTP headers
export GIT_TRACE=5 GIT_TRACE_PACKET=5 GIT_TRACE_SETUP=5 GIT_CURL_VERBOSE=1

INFO() { printf '\033[1;34m[INFO]  %s\033[0m\n' "$1"; }
WARN() { printf '\033[1;33m[WARN]  %s\033[0m\n' "$1"; }
FAIL() { printf '\033[1;31m[FAIL]  %s\033[0m\n' "$1"; }
PASS() { printf '\033[1;32m[PASS]  %s\033[0m\n' "$1"; }

INFO "📂 Masked log → $LOG_MASKED"
INFO "🗃️  Raw log    → $LOG_RAW"

# WHAT: Load existing GH_TOKEN from .env or .env.local
# WHY: Enables reuse of previously stored PATs
# UX: Clean reuse of credentials without re-prompt
# DEBUG: Show source of token if found
for ENV_FILE in .env .env.local; do
  if [[ -f "$ENV_FILE" ]]; then
    set -o allexport; source "$ENV_FILE"; set +o allexport
    INFO "🔑 Loaded GH_TOKEN from $ENV_FILE"
    break
  fi
done

# WHAT: Validate token format, and if invalid, force re-entry
# WHY: Prevent invalid or malformed GH_TOKEN from being used
# UX: Prompts user with clear re-entry and stores valid token
# DEBUG: Length and prefix checking ensures token integrity
GH_TOKEN="${GH_TOKEN:-}"
GH_TOKEN="${GH_TOKEN//\"/}"  # Strip quotes
TOKEN_LEN=${#GH_TOKEN}

if (( TOKEN_LEN < 40 )) || ! [[ "$GH_TOKEN" =~ ^(ghp_|github_pat_) ]]; then
  WARN "❌ GH_TOKEN invalid or too short (len=$TOKEN_LEN), prompt follows"
  echo -n "Enter valid GitHub PAT: " > /dev/tty
  read -r GH_TOKEN < /dev/tty
  GH_TOKEN="${GH_TOKEN//\"/}"
  TOKEN_LEN=${#GH_TOKEN}
  if (( TOKEN_LEN < 40 )) || ! [[ "$GH_TOKEN" =~ ^(ghp_|github_pat_) ]]; then
    FAIL "❌ Entered token still invalid. Exiting."
    exit 1
  fi
  echo "GH_TOKEN=$GH_TOKEN" > .env
  chmod 600 .env
  PASS "✅ Token validated and saved to .env"
else
  PASS "✅ GH_TOKEN appears valid (len=$TOKEN_LEN)"
fi

# WHAT: Rewrite origin URL to embed GH_TOKEN
# WHY: Avoid SSH issues or auth failures
# UX: Mask token before displaying new remote URL
# DEBUG: Supports SSH, HTTPS, or embedded-cred URLs
REMOTE_URL="$(git remote get-url origin 2>/dev/null || true)"
[[ -z "$REMOTE_URL" ]] && { FAIL "❌ No 'origin' remote found"; exit 1; }

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
INFO "🔧 Updated remote → $SAFE_REMOTE"

# WHAT: Commit staged changes (if any)
# WHY: Ensure all working changes are committed before push
# UX: Message includes timestamp
# DEBUG: Uses --porcelain to detect changes
if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  MSG="[PRF] Auto-commit @ $(date '+%F %T')"
  git commit -m "$MSG"
  INFO "📦 Auto-committed changes → $MSG"
else
  INFO "📦 No staged changes to commit"
fi

# WHAT: Push to origin
# WHY: Complete upload using validated remote/token
# UX: Clearly informs user of success/failure
# DEBUG: Captures git push response, masks token
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
INFO "🚀 Pushing '$BRANCH' to origin..."
PUSH_OUTPUT="$(git push origin "$BRANCH" 2>&1)"
PUSH_EXIT=$?
SAFE_PUSH="$(echo "$PUSH_OUTPUT" | sed "s/${GH_TOKEN}/********/g")"
echo "$SAFE_PUSH"

if (( PUSH_EXIT != 0 )); then
  FAIL "❌ Git push failed (code $PUSH_EXIT)"
  exit $PUSH_EXIT
fi

if echo "$PUSH_OUTPUT" | grep -q "Everything up-to-date"; then
  PASS "✅ No changes to push."
else
  PASS "✅ Push successful to '$BRANCH'"
fi
