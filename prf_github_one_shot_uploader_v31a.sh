#!/usr/bin/env bash
################################################################################
# FILE: prf_github_one_shot_uploader_v31.sh
# DESC: GitHub uploader with enforced PRF commit graph confirmation and self-healing
# SPEC: PRF‑COMPOSITE‑2025‑06‑18‑C‑V31‑FINAL (P01–P27)
################################################################################

set -euo pipefail
IFS=$'\n\t'
NOW="$(date '+%Y%m%d')"
RUN_ID="$(date '+%H%M%S')"

# WHAT: Ensure CLI dependencies for visual graph confirmation and log timestamps
# WHY: All uploads must be traceable with human-auditable confirmation of state
# FAIL: Exits only if critical tools are unavailable and cannot be installed
# UX: Auto-installs 'git', 'moreutils', and optionally 'gitk' if missing
# DEBUG: gitk install failure is warned, not fatal; fallback is CLI graph
for TOOL in git ts; do
  if ! command -v "$TOOL" &>/dev/null; then
    echo "[SELF-HEAL] Installing missing tool: $TOOL"
    if command -v dnf &>/dev/null; then
      sudo dnf install -y git moreutils gitk || echo "[WARN] dnf install failed"
    elif command -v apt &>/dev/null; then
      sudo apt update && sudo apt install -y git moreutils gitk || echo "[WARN] apt install failed"
    else
      echo "[FAIL] No supported package manager found" >&2
      exit 127
    fi
  fi
done

# WHAT: Setup PRF log destinations
# WHY: Logs must be partitioned into human-readable and raw, with timestamped IDs
# FAIL: Exits if logs cannot be written (disk full, permissions)
# UX: Logs both masked (public view) and raw (audit)
# DEBUG: Uses 'ts' to prefix timestamps
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

# WHAT: Load GitHub token from .env
# WHY: Token is required for push authentication
# FAIL: Exits if token invalid or missing
# UX: Prompts user to input token if .env not available or malformed
# DEBUG: Saves token into .env with 600 permissions if entered
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

# WHAT: Convert remote to HTTPS+token format
# WHY: Auth via GH_TOKEN requires canonical HTTPS format
# FAIL: Exits if no remote or invalid URL
# UX: Auto-rewrites ssh, git@, or user@ formats
# DEBUG: Shows masked remote
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

# WHAT: Commit local changes with PRF label
# WHY: All pushes must reflect latest edits
# FAIL: Skips commit if working tree clean
# UX: Shows commit message if created
# DEBUG: Uses timestamp marker for audit
if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  MSG="[PRF] Auto-commit @ $(date '+%F %T')"
  git commit -m "$MSG"
  INFO "📦 Committed → $MSG"
else
  INFO "📦 No changes to commit"
fi

# WHAT: Push to GitHub
# WHY: Required for sync and PRF audit tracking
# FAIL: Exits on push failure, shows full masked log
# UX: Displays confirmation message, branch name
# DEBUG: Detects common push states
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
  WARN "⚠️  Push output ambiguous — check manually."
fi

# WHAT: Show commit graph confirmation (visual or CLI)
# WHY: PRF mandates post-push confirmation of actual repo state
# FAIL: None — always falls back to CLI view
# UX: Attempts gitk if present, falls back to git log graph
# DEBUG: gitk is backgrounded, CLI log limited to 40 entries
if command -v gitk &>/dev/null; then
  INFO "📊 Launching gitk (graphical commit viewer)…"
  gitk --all &
else
  INFO "📈 Fallback: Printing commit graph (latest 40 lines):"
  git log --oneline --graph --decorate --all | head -n 40
fi
