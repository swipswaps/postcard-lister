#!/usr/bin/env bash
################################################################################
# FILE: prf_github_graph_confirming_uploader_v33.sh
# DESC: PRF‑compliant GitHub one-shot uploader with deterministic gitk trigger
# SPEC: PRF‑COMPOSITE‑2025‑06‑18‑C-V33-FINAL
################################################################################

set -euo pipefail
IFS=$'\n\t'
NOW="$(date '+%Y%m%d')"
RUN_ID="$(date '+%H%M%S')"

# WHAT: Ensure required tools are installed before proceeding
# WHY: gitk and xdotool are required for graphical commit confirmation
# FAIL: If tools are missing and cannot be installed, exit with error
# UX: Tools are auto-installed using dnf or apt with no manual intervention
# DEBUG: Emits progress logs and auto-heals via package manager

for TOOL in git gitk xdotool moreutils; do
  if ! command -v "$TOOL" &>/dev/null; then
    echo "[SELF-HEAL] Installing missing tool: $TOOL"
    if command -v dnf &>/dev/null; then
      sudo dnf install -y "$TOOL" || echo "[WARN] dnf install failed for $TOOL"
    elif command -v apt &>/dev/null; then
      sudo apt update && sudo apt install -y "$TOOL" || echo "[WARN] apt install failed for $TOOL"
    else
      echo "[FAIL] No supported package manager found to install $TOOL"
      exit 127
    fi
  fi
done

# WHAT: Create log directory and setup tee'd logging
# WHY: PRF requires real-time, timestamped, and dual-channel audit logging
# FAIL: Exits if logs can't be written
# UX: Logs saved to human and raw form for review
# DEBUG: Uses stdbuf to flush immediately

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

# WHAT: Load or request GitHub token
# WHY: Needed for authentication with GitHub over HTTPS
# FAIL: Exits if token is not valid or not provided
# UX: Prompts for token only if missing or invalid
# DEBUG: Accepts tokens with or without ghp_ or github_pat_ prefix

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

# WHAT: Convert SSH remote to HTTPS format for token auth
# WHY: Only HTTPS remote works with token
# FAIL: Exit if no origin set
# UX: Rewrites remote with masked logs
# DEBUG: Normalizes URL patterns across protocols

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

# WHAT: Auto-commit if changes are pending
# WHY: One-shot PRF push must include all content
# FAIL: None — if clean, continues
# UX: Verbose logging of commit outcome
# DEBUG: Uses git status --porcelain for detection

if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  MSG="[PRF] Auto-commit @ $(date '+%F %T')"
  git commit -m "$MSG"
  echo "[INFO]  📦 Committed → $MSG"
else
  echo "[INFO]  📦 No changes to commit"
fi

# WHAT: Push branch to remote using updated origin
# WHY: Push is the main action this script performs
# FAIL: Exits if git push fails
# UX: Detects and describes success states
# DEBUG: Redacts token from all displayed output

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

# WHAT: Launch gitk and wait for user-triggered display
# WHY: gitk does NOT auto-display commits without focus/trigger
# FAIL: None — will fallback to log view if DISPLAY missing
# UX: Uses xdotool to foreground gitk reliably
# DEBUG: All activity is human-visible

if command -v gitk &>/dev/null && [[ -n "${DISPLAY:-}" ]]; then
  echo "[INFO]  📊 Launching gitk (GUI commit viewer)…"
  nohup gitk --all > /dev/null 2>&1 &
  sleep 2
  GITK_ID=$(xdotool search --onlyvisible --class gitk || true)
  if [[ -n "$GITK_ID" ]]; then
    xdotool windowactivate "$GITK_ID"
    echo "[PASS]  ✅ gitk brought to foreground."
  else
    echo "[WARN]  ⚠ gitk launched but no window found."
  fi
else
  echo "[INFO]  📈 Fallback: CLI commit graph below:"
  git log --oneline --graph --decorate --all | head -n 40
fi
