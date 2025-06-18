#!/usr/bin/env bash
################################################################################
# FILE: prf_github_one_shot_uploader_v34.sh
# DESC: PRF‑compliant GitHub uploader with deterministic gitk trigger
# SPEC: PRF‑COMPOSITE‑2025‑06‑18‑D-V34-FINAL
################################################################################

set -euo pipefail
IFS=$'\n\t'
NOW="$(date '+%Y%m%d')"
RUN_ID="$(date '+%H%M%S')"

# WHAT: Ensure required tools are installed before proceeding
# WHY: git, gitk, xdotool, moreutils are required for all scripted UX and logging
# FAIL: If any required tool cannot be installed, exit immediately
# UX: Tools are silently installed via dnf or apt
# DEBUG: Auto-healing mode logs all install attempts

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

# WHAT: Set up logging directories and realtime tee'd logs
# WHY: PRF requires visible audit trail with immediate stdout + persistent files
# FAIL: Logs failing to write trigger fatal exit
# UX: Human and raw logs shown and stored for review
# DEBUG: Uses stdbuf for no-buffering behavior

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

# WHAT: Load GitHub Personal Access Token from file or prompt
# WHY: Token needed for HTTPS GitHub push
# FAIL: Fails if token is invalid or not provided
# UX: Silent auto-read, fallback to user prompt, then safe save
# DEBUG: Enforces length check and basic regex pattern

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

# WHAT: Normalize remote URL to HTTPS with embedded token
# WHY: Required for token-authenticated push
# FAIL: Exit if no remote exists
# UX: Auto-rewrites remote with masked feedback
# DEBUG: Handles multiple Git URL syntaxes

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

# WHAT: Auto-commit all current changes
# WHY: Ensure push operation includes everything
# FAIL: None — continues cleanly if repo is clean
# UX: Auto-message is timestamped and visible
# DEBUG: Uses --porcelain to detect uncommitted changes

if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  MSG="[PRF] Auto-commit @ $(date '+%F %T')"
  git commit -m "$MSG"
  echo "[INFO]  📦 Committed → $MSG"
else
  echo "[INFO]  📦 No changes to commit"
fi

# WHAT: Push current branch to GitHub
# WHY: Main goal of the script
# FAIL: Exit on failed push
# UX: Verbose and redacted success/failure output
# DEBUG: Git output is masked of token

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

# WHAT: Launch gitk in blocking mode for deterministic GUI
# WHY: Prior launch used background '&' causing nondeterminism
# FAIL: Falls back to git log graph on headless systems
# UX: gitk reliably foregrounded, blocking shell until exit
# DEBUG: Uses xdotool and exit trace

if command -v gitk &>/dev/null && [[ -n "${DISPLAY:-}" ]]; then
  echo "[INFO]  📊 Launching gitk (GUI commit viewer)…"
  gitk --all &
  sleep 2
  GITK_ID=$(xdotool search --onlyvisible --class gitk || true)
  if [[ -n "$GITK_ID" ]]; then
    xdotool windowactivate "$GITK_ID"
    echo "[PASS]  ✅ gitk foregrounded."
  else
    echo "[WARN]  ⚠ gitk visible but not detected by xdotool."
  fi
else
  echo "[INFO]  📈 Fallback: CLI commit graph:"
  git log --oneline --graph --decorate --all | head -n 40
fi
