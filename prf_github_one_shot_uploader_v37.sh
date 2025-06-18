#!/usr/bin/env bash
################################################################################
# FILE: prf_github_one_shot_uploader_v37.sh
# DESC: PRF‑compliant GitHub uploader with deterministic gitk GUI display
# SPEC: PRF‑COMPOSITE‑2025‑06‑18‑D-V37-FINAL
################################################################################

set -euo pipefail
IFS=$'\n\t'
NOW="$(date '+%Y%m%d')"
RUN_ID="$(date '+%H%M%S')"

# WHAT: Ensure all required tools are installed (git, gitk, xdotool, moreutils)
# WHY: PRF mandates full UX automation, visibility, and tool availability
# FAIL: Exit immediately if package manager or installation fails
# UX: Auto-heals silently, announces successful installations
# DEBUG: Each tool install attempt is logged explicitly

for TOOL in git gitk xdotool moreutils; do
  if ! command -v "$TOOL" &>/dev/null; then
    echo "[SELF-HEAL] Installing missing tool: $TOOL"
    if command -v dnf &>/dev/null; then
      sudo dnf install -y "$TOOL" || { echo "[FAIL] dnf failed for $TOOL"; exit 127; }
    elif command -v apt &>/dev/null; then
      sudo apt update && sudo apt install -y "$TOOL" || { echo "[FAIL] apt failed for $TOOL"; exit 127; }
    else
      echo "[FAIL] No supported package manager available"
      exit 127
    fi
  fi
done

# WHAT: Set up real-time logs for stdout and masked persistence
# WHY: PRF requires human-readable and auditable logs
# FAIL: Abort if logs cannot be written
# UX: Log paths announced immediately
# DEBUG: Uses stdbuf and tee for real-time transparency

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

echo "[INFO]  📂 Masked log → $LOG_MASKED"
echo "[INFO]  🗃  Raw log    → $LOG_RAW"

# WHAT: Load GitHub token from .env or prompt user securely
# WHY: Required for HTTPS-based push authentication
# FAIL: Exit if token is invalid or missing
# UX: Saves valid token to .env; avoids repeated prompts
# DEBUG: Validates with regex and length enforcement

GH_TOKEN=""
for ENV_FILE in .env .env.local; do
  if [[ -f "$ENV_FILE" ]]; then
    set -o allexport; source "$ENV_FILE"; set +o allexport
    echo "[INFO]  🔎 Reading token from $ENV_FILE"
    break
  fi
done

GH_TOKEN="${GH_TOKEN//\"/}"
LEN=${#GH_TOKEN}
TOKEN_PATTERN='^[A-Za-z0-9_-]{40,}$'

if (( LEN < 40 )) || ! [[ "$GH_TOKEN" =~ $TOKEN_PATTERN ]]; then
  echo "[WARN]  ❌ Invalid token (len=$LEN), prompting for re-entry"
  echo -n "Enter valid GitHub PAT: " > /dev/tty
  read -r GH_TOKEN < /dev/tty
  GH_TOKEN="${GH_TOKEN//\"/}"
  LEN=${#GH_TOKEN}
  if (( LEN < 40 )) || ! [[ "$GH_TOKEN" =~ $TOKEN_PATTERN ]]; then
    echo "[FAIL]  ❌ Token still invalid after prompt"
    exit 1
  fi
  echo "GH_TOKEN=\"$GH_TOKEN\"" > .env
  chmod 600 .env
  echo "[PASS]  ✅ Token validated and saved"
else
  echo "[PASS]  ✅ GH_TOKEN valid (len=$LEN)"
fi

# WHAT: Rewrite remote URL with token if needed
# WHY: Ensures push over HTTPS with PAT auth
# FAIL: Exit if no remote exists
# UX: Safely masks token in logs
# DEBUG: Converts git@ or ssh:// to https:// form

REMOTE_URL="$(git remote get-url origin 2>/dev/null || true)"
[[ -z "$REMOTE_URL" ]] && { echo "[FAIL]  ❌ No git origin remote found"; exit 1; }

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
echo "[INFO]  🔧 Remote updated → $SAFE_REMOTE"

# WHAT: Commit all changes if present
# WHY: Required before push; ensures traceable state
# FAIL: Does not exit on no changes
# UX: Emits status clearly
# DEBUG: Uses --porcelain to detect changes safely

if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  MSG="[PRF] Auto-commit @ $(date '+%F %T')"
  git commit -m "$MSG"
  echo "[INFO]  📦 Committed → $MSG"
else
  echo "[INFO]  📦 No changes to commit"
fi

# WHAT: Push to GitHub
# WHY: Central operation of uploader
# FAIL: Exit if push fails
# UX: Result is visibly echoed and masked
# DEBUG: Return code and message interpreted

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
echo "[INFO]  🚀 Pushing '$BRANCH' to GitHub…"
PUSH_OUTPUT="$(git push origin "$BRANCH" 2>&1)"
PUSH_EXIT=$?
echo "${PUSH_OUTPUT//$GH_TOKEN/********}"

if (( PUSH_EXIT != 0 )); then
  echo "[FAIL]  ❌ Push failed (code $PUSH_EXIT)"
  exit $PUSH_EXIT
fi

if echo "$PUSH_OUTPUT" | grep -q "Everything up-to-date"; then
  echo "[PASS]  ✅ No changes to push."
elif echo "$PUSH_OUTPUT" | grep -q "To https://"; then
  echo "[PASS]  ✅ Push successful → $BRANCH"
else
  echo "[WARN]  ⚠ Push result unclear — check manually."
fi

# WHAT: Show git commit graph using gitk
# WHY: PRF requires GUI output, human-verifiable audit trail
# FAIL: Fallback to CLI graph if gitk or xdotool not detected
# UX: Blocks script until user closes gitk
# DEBUG: Foregrounds gitk using xdotool

if command -v gitk &>/dev/null && [[ -n "${DISPLAY:-}" ]]; then
  echo "[INFO]  📊 Launching gitk GUI..."
  (gitk --all &)  # Subshell prevents blocking but allows us to detect
  sleep 2
  GITK_WIN_ID=$(xdotool search --onlyvisible --class gitk | head -n1 || true)
  if [[ -n "$GITK_WIN_ID" ]]; then
    xdotool windowactivate "$GITK_WIN_ID"
    xdotool windowraise "$GITK_WIN_ID"
    echo "[PASS]  ✅ gitk GUI raised to foreground"
    while xdotool search --onlyvisible --class gitk | grep -q .; do
      sleep 1
    done
    echo "[INFO]  🛑 gitk closed"
  else
    echo "[WARN]  ⚠ gitk not detected; fallback to CLI"
    git log --oneline --graph --decorate --all | head -n 40
  fi
else
  echo "[INFO]  📈 No DISPLAY or gitk; fallback to CLI graph"
  git log --oneline --graph --decorate --all | head -n 40
fi
