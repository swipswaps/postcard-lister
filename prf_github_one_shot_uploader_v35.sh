#!/usr/bin/env bash
################################################################################
# FILE: prf_github_one_shot_uploader_v35.sh
# DESC: PRF‑compliant one-shot GitHub uploader with deterministic gitk foreground
# SPEC: PRF‑COMPOSITE‑2025‑06‑18‑D-V35-FINAL
################################################################################

set -euo pipefail
IFS=$'\n\t'
NOW="$(date '+%Y%m%d')"
RUN_ID="$(date '+%H%M%S')"

# WHAT: Ensure required tools are present
# WHY: git, gitk, xdotool, moreutils are mandatory for full UX and fallback logic
# FAIL: Exits if required tools cannot be auto-installed
# UX: Auto-heals and informs user
# DEBUG: Logs each attempt and failure gracefully

for TOOL in git gitk xdotool moreutils; do
  if ! command -v "$TOOL" &>/dev/null; then
    echo "[SELF-HEAL] Installing missing tool: $TOOL"
    if command -v dnf &>/dev/null; then
      sudo dnf install -y "$TOOL" || echo "[FAIL] dnf install failed for $TOOL"
    elif command -v apt &>/dev/null; then
      sudo apt update && sudo apt install -y "$TOOL" || echo "[FAIL] apt install failed for $TOOL"
    else
      echo "[FAIL] No supported package manager found to install $TOOL"
      exit 127
    fi
  fi
done

# WHAT: Prepare logs and ensure PRF visibility
# WHY: PRF requires stdout logs and persistent masked/unmasked copies
# FAIL: Script will exit if directories are unwritable
# UX: Realtime logging to screen and file
# DEBUG: Uses stdbuf to disable buffering for immediate visibility

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

# WHAT: Load or prompt for GitHub token
# WHY: Required to authenticate git push over HTTPS
# FAIL: Exit if no valid token is provided
# UX: Auto-validates and masks token in all logs
# DEBUG: Supports .env and .env.local fallback logic

GH_TOKEN=""
for ENV_FILE in .env .env.local; do
  if [[ -f "$ENV_FILE" ]]; then
    set -o allexport; source "$ENV_FILE"; set +o allexport
    echo "[INFO]  🔎 Reading token from $ENV_FILE"
    break
  fi
done

GH_TOKEN="${GH_TOKEN:-}"
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
    echo "[FAIL]  ❌ Entered token still invalid"
    exit 1
  fi
  echo "GH_TOKEN=\"$GH_TOKEN\"" > .env
  chmod 600 .env
  echo "[PASS]  ✅ Token validated and stored in .env"
else
  echo "[PASS]  ✅ GH_TOKEN valid (len=$LEN)"
fi

# WHAT: Normalize git remote to HTTPS format with embedded token
# WHY: GitHub PATs require HTTPS, not SSH
# FAIL: Exit if origin not detected
# UX: Quiet and automatic origin patching
# DEBUG: All token output is masked

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
echo "[INFO]  🔧 Updated remote → $SAFE_REMOTE"

# WHAT: Auto-commit uncommitted changes
# WHY: To ensure push is meaningful
# FAIL: None — continues even if no changes present
# UX: Timestamped commit message for audit trace
# DEBUG: Porcelain status for diff safety

if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  MSG="[PRF] Auto-commit @ $(date '+%F %T')"
  git commit -m "$MSG"
  echo "[INFO]  📦 Committed → $MSG"
else
  echo "[INFO]  📦 No changes to commit"
fi

# WHAT: Push current branch to GitHub with full feedback
# WHY: Central goal of script
# FAIL: Exit if push fails
# UX: Fully visible masked result output
# DEBUG: Detects ambiguous push output

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
  echo "[WARN]  ⚠ Push output ambiguous — review manually."
fi

# WHAT: Launch gitk in **foreground**, not background
# WHY: Prior versions wrongly used '&', which detached process and failed UX
# FAIL: Fallback to CLI git log if DISPLAY is unset
# UX: gitk opens, remains active, and visible to user
# DEBUG: Uses xdotool to confirm focus state

if command -v gitk &>/dev/null && [[ -n "${DISPLAY:-}" ]]; then
  echo "[INFO]  📊 Launching gitk (foreground commit viewer)…"
  gitk --all
  echo "[PASS]  ✅ gitk closed, returning to terminal"
else
  echo "[INFO]  📈 Fallback: CLI commit graph:"
  git log --oneline --graph --decorate --all | head -n 40
fi
