#!/usr/bin/env bash
################################################################################
# FILE: prf_github_one_shot_uploader_v24.sh
# DESC: Hardened GitHub uploader with modern token entropy logic (no prefix required)
# SPEC: PRF‑COMPOSITE‑2025‑06‑18‑B (P01–P27 FULLY COMPLIANT)
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

# WHAT: Setup log directory and dual log streams
# WHY: We need both user-facing and raw logs (PRF-P12, P21)
# FAIL: Must not fail silently or without path messages
# UX: Inform user of masked + raw logs
# DEBUG: Creates ts() fallback and dual output pipes
LOG_DIR="logs/$NOW"
mkdir -p "$LOG_DIR"
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

INFO "📂 Masked log → $LOG_MASKED"
INFO "🗃  Raw log    → $LOG_RAW"

# WHAT: Attempt to load GH_TOKEN from local env files
# WHY: Token reuse prevents unnecessary prompts
# FAIL: Skips silently if missing
# UX: Indicates source file used
# DEBUG: Tracks source
for ENV_FILE in .env .env.local; do
  if [[ -f "$ENV_FILE" ]]; then
    set -o allexport; source "$ENV_FILE"; set +o allexport
    INFO "🔎 Reading token from $ENV_FILE"
    break
  fi
done

# WHAT: Validate token with entropy check only (no prefix required)
# WHY: Modern GitHub PATs may omit ghp_ or github_pat_
# FAIL: Prompts user for corrected value if token fails
# UX: Prompts visibly with retry
# DEBUG: Accepts 40+ character alphanumeric tokens
GH_TOKEN="${GH_TOKEN:-}"
GH_TOKEN="${GH_TOKEN//\"/}"
LEN=${#GH_TOKEN}
TOKEN_PATTERN='^[A-Za-z0-9_-]{40,}$'

if (( LEN < 40 )) || ! [[ "$GH_TOKEN" =~ $TOKEN_PATTERN ]]; then
  WARN "❌ Invalid token (len=$LEN), prompting for re-entry (no manual .env edits)"
  echo -n "Enter valid GitHub PAT: " > /dev/tty
  read -r GH_TOKEN < /dev/tty
  GH_TOKEN="${GH_TOKEN//\"/}"
  LEN=${#GH_TOKEN}
  if (( LEN < 40 )) || ! [[ "$GH_TOKEN" =~ $TOKEN_PATTERN ]]; then
    FAIL "❌ Entered token still invalid"
    exit 1
  fi
  echo "GH_TOKEN=\"$GH_TOKEN\"" > .env
  chmod 600 .env
  PASS "✅ Token validated and stored in .env (len=$LEN)"
else
  PASS "✅ GH_TOKEN valid (len=$LEN)"
fi

# WHAT: Rewrite git remote URL with embedded GH_TOKEN
# WHY: Avoids SSH or auth failure issues
# FAIL: Exits on missing remote
# UX: Displays masked URL
# DEBUG: Rewrites origin cleanly
REMOTE_URL="$(git remote get-url origin 2>/dev/null || true)"
[[ -z "$REMOTE_URL" ]] && { FAIL "❌ No git origin remote found"; exit 1; }

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
INFO "🔧 Updated remote to $SAFE_REMOTE"

# WHAT: Auto-commit if needed
# WHY: PRF requires push to reflect live state
# FAIL: No-op if no changes
# UX: Echoes commit message
# DEBUG: Commit message contains timestamp
if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  MSG="[PRF] Auto-commit @ $(date '+%F %T')"
  git commit -m "$MSG"
  INFO "📦 Committed → $MSG"
else
  INFO "📦 No changes to commit"
fi

# WHAT: Push to GitHub
# WHY: Complete GitHub upload
# FAIL: Detects error via exit code
# UX: Notifies of push status
# DEBUG: Output redacted and echoed
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
INFO "🚀 Pushing branch '$BRANCH' to GitHub…"
PUSH_OUTPUT="$(git push origin "$BRANCH" 2>&1)"
PUSH_EXIT=$?
echo "${PUSH_OUTPUT//$GH_TOKEN/********}"

if (( PUSH_EXIT != 0 )); then
  FAIL "❌ Git push failed (code $PUSH_EXIT)"
  exit $PUSH_EXIT
fi

if echo "$PUSH_OUTPUT" | grep -q "Everything up-to-date"; then
  PASS "✅ No changes to push."
else
  PASS "✅ Push successful → $BRANCH"
fi
