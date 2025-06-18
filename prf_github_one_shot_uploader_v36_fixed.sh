#!/usr/bin/env bash
################################################################################
# FILE: prf_github_one_shot_uploader_v36_fixed.sh
# DESC: PRF‑compliant GitHub uploader with foregrounded gitk, no '&' issue
# SPEC: PRF‑COMPOSITE‑2025‑06‑18‑D-V36-FINAL
################################################################################

set -euo pipefail
IFS=$'\n\t'
NOW="$(date '+%Y%m%d')"
RUN_ID="$(date '+%H%M%S')"

# WHAT: Ensure all required tools are installed
# WHY: PRF requires deterministic setup and GUI validation via gitk
# FAIL: Exit if tools or installer fail
# UX: Auto-installs missing tools silently, logs progress
# DEBUG: Explicit tool install visibility

for TOOL in git gitk xdotool moreutils; do
  if ! command -v "$TOOL" &>/dev/null; then
    echo "[SELF-HEAL] Installing missing tool: $TOOL"
    if command -v dnf &>/dev/null; then
      sudo dnf install -y "$TOOL" || { echo "[FAIL] dnf failed for $TOOL"; exit 127; }
    elif command -v apt &>/dev/null; then
      sudo apt update && sudo apt install -y "$TOOL" || { echo "[FAIL] apt failed for $TOOL"; exit 127; }
    else
      echo "[FAIL] No package manager found"
      exit 127
    fi
  fi
done

# WHAT: Setup real-time and raw logs
# WHY: Human-readable output required by PRF audit standards
# FAIL: Exit if logs cannot be created
# UX: Logs displayed and saved visibly
# DEBUG: Uses tee and stdbuf for streaming logs

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

# WHAT: Load GitHub token from .env or prompt user
# WHY: Required to authenticate over HTTPS
# FAIL: Exit if no valid token
# UX: Prompts securely, saves to .env
# DEBUG: Token regex-validated

GH_TOKEN=""
for ENV_FILE in .env .env.local; do
  if [[ -f "$ENV_FILE" ]]; then
    set -o allexport; source "$ENV_FILE"; set +o allexport
    echo "[INFO]  🔎 Loaded token from $ENV_FILE"
    break
  fi
done

GH_TOKEN="${GH_TOKEN//\"/}"
LEN=${#GH_TOKEN}
TOKEN_PATTERN='^[A-Za-z0-9_-]{40,}$'

if (( LEN < 40 )) || ! [[ "$GH_TOKEN" =~ $TOKEN_PATTERN ]]; then
  echo "[WARN]  ❌ Token invalid, prompting..."
  echo -n "Enter valid GitHub PAT: " > /dev/tty
  read -r GH_TOKEN < /dev/tty
  GH_TOKEN="${GH_TOKEN//\"/}"
  LEN=${#GH_TOKEN}
  if (( LEN < 40 )) || ! [[ "$GH_TOKEN" =~ $TOKEN_PATTERN ]]; then
    echo "[FAIL]  ❌ Token failed validation again"
    exit 1
  fi
  echo "GH_TOKEN=\"$GH_TOKEN\"" > .env
  chmod 600 .env
  echo "[PASS]  ✅ Token saved"
else
  echo "[PASS]  ✅ GH_TOKEN validated (len=$LEN)"
fi

# WHAT: Normalize remote URL to HTTPS
# WHY: Required for token-based push
# FAIL: Exit if no remote
# UX: Auto-fixes SSH remotes
# DEBUG: Masked URL in logs

REMOTE_URL="$(git remote get-url origin 2>/dev/null || true)"
[[ -z "$REMOTE_URL" ]] && { echo "[FAIL]  ❌ No git remote found"; exit 1; }

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

# WHAT: Commit staged files if necessary
# WHY: Pushes must be meaningful
# FAIL: Continues if no changes
# UX: Auto-message shown
# DEBUG: git status used to detect changes

if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  MSG="[PRF] Auto-commit @ $(date '+%F %T')"
  git commit -m "$MSG"
  echo "[INFO]  📦 Commit → $MSG"
else
  echo "[INFO]  📦 No changes to commit"
fi

# WHAT: Push current branch
# WHY: Central goal — push to GitHub
# FAIL: Exits if push fails
# UX: Shows masked output
# DEBUG: Echoes masked push result

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
echo "[INFO]  🚀 Pushing branch '$BRANCH'"
PUSH_OUTPUT="$(git push origin "$BRANCH" 2>&1)"
PUSH_EXIT=$?
echo "${PUSH_OUTPUT//$GH_TOKEN/********}"

if (( PUSH_EXIT != 0 )); then
  echo "[FAIL]  ❌ Push failed (code $PUSH_EXIT)"
  exit $PUSH_EXIT
fi

if echo "$PUSH_OUTPUT" | grep -q "Everything up-to-date"; then
  echo "[PASS]  ✅ No changes to push"
elif echo "$PUSH_OUTPUT" | grep -q "To https://"; then
  echo "[PASS]  ✅ Push successful"
else
  echo "[WARN]  ⚠ Push status unclear"
fi

# WHAT: Show git commit graph using gitk
# WHY: GUI must be user-visible and deterministic
# FAIL: Fallback to CLI if no GUI or failure
# UX: Blocks script until user closes gitk
# DEBUG: Foregrounds gitk using xdotool

if command -v gitk &>/dev/null && [[ -n "${DISPLAY:-}" ]]; then
  echo "[INFO]  📊 Launching gitk GUI..."
  GITK_PID=""
  gitk --all &
  sleep 2
  GITK_PID=$(xdotool search --onlyvisible --class gitk | head -n1 || true)
  if [[ -n "$GITK_PID" ]]; then
    xdotool windowactivate "$GITK_PID"
    xdotool windowraise "$GITK_PID"
    echo "[PASS]  ✅ gitk shown"
    wait %1
    echo "[INFO]  🛑 gitk closed"
  else
    echo "[WARN]  ⚠ gitk not detected, fallback to CLI graph"
    git log --oneline --graph --decorate --all | head -n 40
  fi
else
  echo "[INFO]  📈 No DISPLAY detected, fallback to CLI graph"
  git log --oneline --graph --decorate --all | head -n 40
fi
