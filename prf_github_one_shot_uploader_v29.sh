#!/usr/bin/env bash
################################################################################
# FILE: prf_github_one_shot_uploader_v29.sh
# DESC: GitHub uploader with enforced PRF visual commit graph confirmation
# SPEC: PRF‑COMPOSITE‑2025‑06‑18‑C (P01–P27)
################################################################################

set -euo pipefail
IFS=$'\n\t'
NOW="$(date '+%Y%m%d')"
RUN_ID="$(date '+%H%M%S')"

# WHAT: Ensure CLI dependencies required for upload/log/graph are available
# WHY: 'ts' needed for log timestamps, 'gitk' optional for visual commit graph
# FAIL: ts missing => auto-install; gitk missing => fallback to git log
# UX: Self-heals with user feedback, always allows commit confirmation
# DEBUG: Uses dnf or apt for installation; logs warnings if unsupported
for TOOL in ts; do
  if ! command -v "$TOOL" &>/dev/null; then
    echo "[SELF-HEAL] Installing $TOOL via package manager"
    if command -v dnf &>/dev/null; then
      sudo dnf install -y moreutils || echo "[WARN] dnf install failed for $TOOL"
    elif command -v apt &>/dev/null; then
      sudo apt update && sudo apt install -y moreutils || echo "[WARN] apt install failed for $TOOL"
    else
      echo "[FAIL] No supported package manager found" >&2
      exit 127
    fi
  fi
done

# WHAT: Setup and announce audit logging locations
# WHY: Logs must support rollback, tracing, and audit compliance
# FAIL: Exits if mkdir fails or disk is full
# UX: Prints paths clearly and masks secrets in view
# DEBUG: Separate masked and raw logs
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

# WHAT: Load and validate GitHub token from .env/.env.local
# WHY: Secure token required for authenticated Git push
# FAIL: Prompts on missing/invalid tokens; stores sanitized
# UX: Warns if token invalid, re-prompts with masking
# DEBUG: Accepts any 40+ char alphanumeric + symbols token
GH_TOKEN=""
for ENV_FILE in .env .env.local; do
  if [[ -f "$ENV_FILE" ]]; then
    set -o allexport; source "$ENV_FILE"; set +o allexport
    INFO "🔎 Reading token from $ENV_FILE"
    break
  fi
done

GH_TOKEN="${GH_TOKEN:-}"
GH_TOKEN="${GH_TOKEN//\"/}"
LEN=${#GH_TOKEN}
TOKEN_PATTERN='^[A-Za-z0-9_-]{40,}$'

if (( LEN < 40 )) || ! [[ "$GH_TOKEN" =~ $TOKEN_PATTERN ]]; then
  WARN "❌ Invalid token (len=$LEN), prompting for re-entry"
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
  PASS "✅ Token validated and stored in .env"
else
  PASS "✅ GH_TOKEN valid (len=$LEN)"
fi

# WHAT: Convert all git remote variants to HTTPS + token format
# WHY: Avoids SSH issues and ensures token-push works
# FAIL: Aborts if no remote or bad URL
# UX: Shows updated remote URL with token masked
# DEBUG: Handles ssh, git@, https+user, cleans up
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

# WHAT: Auto-stage and commit dirty changes
# WHY: Ensure nothing is lost, upload is meaningful
# FAIL: Continues if no changes
# UX: Timestamp commit message, shows it
# DEBUG: Ensures history is linear and audit-safe
if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  MSG="[PRF] Auto-commit @ $(date '+%F %T')"
  git commit -m "$MSG"
  INFO "📦 Committed → $MSG"
else
  INFO "📦 No changes to commit"
fi

# WHAT: Push to current branch using updated remote
# WHY: Upload changes via token auth
# FAIL: Abort with masked log on error
# UX: Mask token from logs
# DEBUG: Uses Git verbose trace mode
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

# WHAT: Confirm via commit graph (visual or terminal)
# WHY: PRF compliance requires user-visible trace of activity
# FAIL: gitk fallback to graph; fallback always succeeds
# UX: Graph shows commit ancestry, proof of upload
# DEBUG: Fallback always shows at least 20
if command -v gitk &>/dev/null; then
  INFO "📊 Launching gitk for visual graph confirmation…"
  gitk --all &
else
  INFO "📈 gitk not found, showing last 20 commit graph lines:"
  git log --oneline --graph --decorate --all | head -n 20
fi
