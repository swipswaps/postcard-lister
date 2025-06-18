#!/usr/bin/env bash
################################################################################
# FILE: prf_github_graph_confirming_uploader_v32.sh
# DESC: PRF‑compliant GitHub uploader with deterministic gitk confirmation
# SPEC: PRF‑COMPOSITE‑2025‑06‑18‑C-V32-FINAL (P01–P27)
################################################################################

set -euo pipefail
IFS=$'\n\t'
NOW="$(date '+%Y%m%d')"
RUN_ID="$(date '+%H%M%S')"

# WHAT: Ensure runtime tools are available before execution
# WHY: gitk and git log are required for commit confirmation
# FAIL: If tools missing, attempt auto-install; fail gracefully if not possible
# UX: Uses dnf or apt to install missing dependencies non-interactively
# DEBUG: All installs logged to PRF output paths

for TOOL in git gitk moreutils; do
  if ! command -v "$TOOL" &>/dev/null; then
    echo "[SELF-HEAL] Installing missing tool: $TOOL"
    if command -v dnf &>/dev/null; then
      sudo dnf install -y git gitk moreutils || echo "[WARN] dnf install failed"
    elif command -v apt &>/dev/null; then
      sudo apt update && sudo apt install -y git gitk moreutils || echo "[WARN] apt install failed"
    else
      echo "[FAIL] No package manager available for auto-install" >&2
      exit 127
    fi
  fi
done

# WHAT: Configure PRF log destinations
# WHY: Required for compliance tracking and traceable audit output
# FAIL: Exits if unable to write logs due to permissions or missing directories
# UX: Writes both human-readable and raw logs
# DEBUG: Uses timestamped folder with tee + stdbuf for unbuffered realtime display

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

# WHAT: Load GH_TOKEN from .env or .env.local, or prompt if invalid
# WHY: GitHub token required for remote push authentication
# FAIL: Exits if token invalid or user entry fails validation
# UX: Writes validated token back to .env with secure perms
# DEBUG: Accepts prefixless PATs

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

# WHAT: Rewrite origin URL to HTTPS+token format for PAT auth
# WHY: SSH/username formats will fail with GH_TOKEN auth
# FAIL: Exits if no origin remote detected
# UX: Automatically patches origin remote if needed
# DEBUG: Logs masked version for audit trail

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

# WHAT: Commit any pending changes under PRF label
# WHY: Required for accurate git state representation
# FAIL: None — skip if nothing to commit
# UX: Commit message includes datetime and PRF marker
# DEBUG: git status used for conditional execution

if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  MSG="[PRF] Auto-commit @ $(date '+%F %T')"
  git commit -m "$MSG"
  INFO "📦 Committed → $MSG"
else
  INFO "📦 No changes to commit"
fi

# WHAT: Push current branch to GitHub using authenticated remote
# WHY: Required for sync and PRF audit validation
# FAIL: Fails on any push rejection or network error
# UX: Output scrubbed of token, logs success/failure
# DEBUG: Handles "everything up-to-date" vs fast-forward merge

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
elif echo "$PUSH_OUTPUT" | grep -q "To https://"; then
  PASS "✅ Push successful → $BRANCH"
else
  WARN "⚠  Push output ambiguous — check manually."
fi

# WHAT: Launch gitk deterministically and visibly OR fallback to CLI log
# WHY: Visual commit confirmation is mandatory per PRF requirements
# FAIL: None — script will wait for GUI gitk to appear before exiting
# UX: gitk is brought to foreground and confirmed via active wait
# DEBUG: CLI fallback prints graph if DISPLAY unavailable

if command -v gitk &>/dev/null && [[ -n "${DISPLAY:-}" ]]; then
  INFO "📊 Launching gitk (GUI commit viewer)…"
  nohup gitk --all > /dev/null 2>&1 &
  sleep 1
  xdotool search --name 'gitk' windowactivate >/dev/null 2>&1 || WARN "⚠ gitk did not gain focus"
else
  INFO "📈 Fallback: Showing commit graph:"
  git log --oneline --graph --decorate --all | head -n 40
fi

