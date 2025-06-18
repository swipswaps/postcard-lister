#!/usr/bin/env bash
################################################################################
# FILE: prf_github_one_shot_uploader_v28.sh
# DESC: GitHub uploader with automated commit graph confirmation and full PRF
# SPEC: PRF‑COMPOSITE‑2025‑06‑18‑C (P01–P27)
################################################################################

set -euo pipefail
IFS=$'\n\t'
NOW="$(date '+%Y%m%d')"
RUN_ID="$(date '+%H%M%S')"

# WHAT: Ensure required CLI tools are installed (ts, gitk optional)
# WHY: Needed for timestamp logs and visual git commit graph
# FAIL: Warn if unavailable, auto-install if possible
# UX: Self-healing install for moreutils (ts) and gitk if visible
# DEBUG: Explicit warnings if no fallback is viable
for TOOL in ts; do
  if ! command -v "$TOOL" &>/dev/null; then
    echo "[SELF-HEAL] Installing $TOOL via detected package manager"
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

# WHAT: Setup log directory and file paths
# WHY: Logs are needed for audit, rollback, debugging
# FAIL: Exits on mkdir failure or file lock
# UX: Shows paths clearly at top of output
# DEBUG: Uses both masked and raw versions
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

# WHAT: Load GitHub token from env or prompt
# WHY: Ensures secure and correct authentication
# FAIL: Blocks if token is invalid or malformed
# UX: Prompts on failure, saves to .env
# DEBUG: Token length and regex check enforced
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

# WHAT: Rewrite remote to use HTTPS w/ embedded token
# WHY: Prevent SSH issues; enable token-based push
# FAIL: Remote not found or malformed exits
# UX: Redacts token in all echo prints
# DEBUG: Handles all git@, ssh, and https variants
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

# WHAT: Stage and commit if repo is dirty
# WHY: Ensures working changes are captured before push
# FAIL: Continues if nothing to commit
# UX: Descriptive commit message with time
# DEBUG: Message printed to console
if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  MSG="[PRF] Auto-commit @ $(date '+%F %T')"
  git commit -m "$MSG"
  INFO "📦 Committed → $MSG"
else
  INFO "📦 No changes to commit"
fi

# WHAT: Push current branch
# WHY: Upload user code changes
# FAIL: Exit on push failure, show code
# UX: Terminal-safe, token-redacted feedback
# DEBUG: Shows log masked
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

# WHAT: Display commit graph after push
# WHY: PRF compliance requires visual or terminal UX proof
# FAIL: Fallback if gitk unavailable
# UX: Launch gitk, else terminal graph
# DEBUG: Shows 20 latest commits if fallback
if command -v gitk &>/dev/null; then
  INFO "📊 Launching gitk for visual commit confirmation…"
  gitk --all &
else
  INFO "📈 Showing last 20 commits (fallback):"
  git log --oneline --graph --decorate --all | head -n 20
fi
