#!/usr/bin/env bash
################################################################################
# FILE: prf_github_one_shot_uploader_v40.sh
# DESC: PRF-compliant GitHub uploader with verified `gitk` foreground blocking
# SPEC: PRF‑COMPOSITE‑2025‑06‑18‑D‑V40‑FINAL
################################################################################

set -euo pipefail
IFS=$'\n\t'
NOW="$(date '+%Y%m%d')"
RUN_ID="$(date '+%H%M%S')"

# WHAT: Ensure required tools are installed
# WHY: Required for GitHub upload and GUI confirmation
# FAIL: If any are missing and cannot be installed, aborts
# UX: Announces install steps and auto-heals environment
# DEBUG: Uses dnf or apt depending on distro availability

for TOOL in git gitk xdotool moreutils; do
  if ! command -v "$TOOL" &>/dev/null; then
    echo "[SELF-HEAL] Installing missing tool: $TOOL"
    if command -v dnf &>/dev/null; then
      sudo dnf install -y "$TOOL" || { echo "[FAIL] dnf failed for $TOOL"; exit 127; }
    elif command -v apt &>/dev/null; then
      sudo apt update && sudo apt install -y "$TOOL" || { echo "[FAIL] apt failed for $TOOL"; exit 127; }
    else
      echo "[FAIL] No supported package manager"
      exit 127
    fi
  fi
done

# WHAT: Initialize log output for real-time and persistent auditing
# WHY: PRF requires logs for postmortem review
# FAIL: Aborts if logs cannot be created or written
# UX: Logs shown and persisted with timestamps
# DEBUG: Uses stdbuf and awk to preserve interactivity

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

# WHAT: Load and validate GitHub token
# WHY: Required for PAT-based push to origin
# FAIL: Aborts if invalid token is provided twice
# UX: Prompted and saved automatically if not present
# DEBUG: Validates length and character class

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
  echo "[WARN]  ❌ Invalid token; prompting"
  echo -n "Enter GitHub PAT: " > /dev/tty
  read -r GH_TOKEN < /dev/tty
  GH_TOKEN="${GH_TOKEN//\"/}"
  LEN=${#GH_TOKEN}
  if (( LEN < 40 )) || ! [[ "$GH_TOKEN" =~ $TOKEN_PATTERN ]]; then
    echo "[FAIL] Token invalid after re-entry"
    exit 1
  fi
  echo "GH_TOKEN=\"$GH_TOKEN\"" > .env
  chmod 600 .env
  echo "[PASS] ✅ Token saved"
else
  echo "[PASS] ✅ GH_TOKEN valid"
fi

# WHAT: Rewrite Git remote to token-based HTTPS
# WHY: Required for non-interactive push
# FAIL: Aborts if no remote origin
# UX: Redacts token from visible URL
# DEBUG: Handles git@, ssh://, and https:// with embedded token

REMOTE_URL="$(git remote get-url origin 2>/dev/null || true)"
[[ -z "$REMOTE_URL" ]] && { echo "[FAIL]  ❌ No origin remote"; exit 1; }

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

# WHAT: Commit any local changes if needed
# WHY: Ensures pushable state
# FAIL: Continues if no changes are staged
# UX: Auto-commits with PRF timestamp
# DEBUG: Uses --porcelain for safe parsing

if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  MSG="[PRF] Auto-commit @ $(date '+%F %T')"
  git commit -m "$MSG"
  echo "[INFO]  📦 Committed → $MSG"
else
  echo "[INFO]  📦 No changes to commit"
fi

# WHAT: Push committed changes to origin
# WHY: Core GitHub sync
# FAIL: Aborts on any push error
# UX: Displays masked push logs
# DEBUG: Interprets success/failure based on output

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
echo "[INFO]  🚀 Pushing '$BRANCH' to GitHub…"
PUSH_OUTPUT="$(git push origin "$BRANCH" 2>&1)"
PUSH_EXIT=$?
echo "${PUSH_OUTPUT//$GH_TOKEN/********}"

if (( PUSH_EXIT != 0 )); then
  echo "[FAIL]  ❌ Push failed"
  exit $PUSH_EXIT
fi

if echo "$PUSH_OUTPUT" | grep -q "Everything up-to-date"; then
  echo "[PASS] ✅ No changes to push"
elif echo "$PUSH_OUTPUT" | grep -q "To https://"; then
  echo "[PASS] ✅ Push success → $BRANCH"
else
  echo "[WARN] ⚠ Push ambiguous"
fi

# WHAT: Show `gitk` GUI in true blocking mode
# WHY: Required by PRF visual UX audit
# FAIL: Fallbacks to CLI if gitk not detected
# UX: Script waits until gitk is closed
# DEBUG: Uses xdotool to raise window, no backgrounding used

if command -v gitk &>/dev/null && [[ -n "${DISPLAY:-}" ]]; then
  echo "[INFO]  📊 Launching gitk GUI (blocking)"
  gitk --all  # NO backgrounding
  echo "[PASS] ✅ gitk closed by user"
else
  echo "[INFO] 📈 No gitk or DISPLAY; using CLI fallback"
  git log --oneline --graph --decorate --all | head -n 40
fi

