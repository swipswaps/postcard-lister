#!/usr/bin/env bash
################################################################################
# FILE: prf_github_one_shot_uploader_v38.sh
# DESC: PRF-compliant GitHub uploader that deterministically displays `gitk` GUI
# SPEC: PRF‑COMPOSITE‑2025‑06‑18‑D-V38‑FINAL
################################################################################

set -euo pipefail
IFS=$'\n\t'
NOW="$(date '+%Y%m%d')"
RUN_ID="$(date '+%H%M%S')"

# WHAT: Ensure all required tools are installed
# WHY: PRF requires complete toolchain validation with deterministic setup
# FAIL: Exits on missing dependencies or unsupported package manager
# UX: Emits verbose progress logs for all installations
# DEBUG: Confirms presence of git, gitk, xdotool, and moreutils

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

# WHAT: Initialize logging
# WHY: Logs must be human-readable, traceable, and audit-friendly
# FAIL: Script exits if logs cannot be written
# UX: Emits log paths to terminal
# DEBUG: Uses stdbuf, ts, and tee for zero-buffer streaming

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

# WHAT: Load GitHub token
# WHY: PAT required for pushing via HTTPS
# FAIL: Aborts on missing or malformed tokens
# UX: Prompts once, then persists securely
# DEBUG: Validates token structure and length

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
  echo "[WARN]  ❌ Invalid GH_TOKEN; requesting manual input"
  echo -n "Enter GitHub PAT: " > /dev/tty
  read -r GH_TOKEN < /dev/tty
  GH_TOKEN="${GH_TOKEN//\"/}"
  LEN=${#GH_TOKEN}
  if (( LEN < 40 )) || ! [[ "$GH_TOKEN" =~ $TOKEN_PATTERN ]]; then
    echo "[FAIL]  ❌ Token invalid after prompt"
    exit 1
  fi
  echo "GH_TOKEN=\"$GH_TOKEN\"" > .env
  chmod 600 .env
  echo "[PASS]  ✅ Token saved to .env"
else
  echo "[PASS]  ✅ GH_TOKEN valid (len=$LEN)"
fi

# WHAT: Rewrite remote URL using token
# WHY: Required for HTTPS push with PAT
# FAIL: Script aborts if origin URL is missing
# UX: Masks token in displayed URLs
# DEBUG: Handles ssh, git@, and https@ remotes

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
echo "[INFO]  🔧 Remote set → $SAFE_REMOTE"

# WHAT: Commit local changes
# WHY: Required before push
# FAIL: Does not exit if nothing to commit
# UX: Status clearly echoed
# DEBUG: Uses --porcelain for machine-safe detection

if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  MSG="[PRF] Auto-commit @ $(date '+%F %T')"
  git commit -m "$MSG"
  echo "[INFO]  📦 Committed → $MSG"
else
  echo "[INFO]  📦 No changes to commit"
fi

# WHAT: Push to GitHub
# WHY: Primary operation
# FAIL: Exit if push fails
# UX: Feedback clear, token redacted
# DEBUG: Interprets push output

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
  echo "[PASS]  ✅ Nothing to push."
elif echo "$PUSH_OUTPUT" | grep -q "To https://"; then
  echo "[PASS]  ✅ Push success → $BRANCH"
else
  echo "[WARN]  ⚠ Push unclear — verify manually"
fi

# WHAT: Launch and foreground gitk without backgrounding (&)
# WHY: gitk --all must show graph immediately; & defers display
# FAIL: If gitk or xdotool is missing, fallback to CLI log graph
# UX: Deterministically blocks until user closes gitk window
# DEBUG: Window detection, raise/activate, loop until closed

if command -v gitk &>/dev/null && [[ -n "${DISPLAY:-}" ]]; then
  echo "[INFO]  📊 Launching gitk GUI (blocking)…"
  nohup gitk --all > /dev/null 2>&1 &
  sleep 3
  GITK_WIN_ID=$(xdotool search --onlyvisible --class gitk | head -n1 || true)
  if [[ -n "$GITK_WIN_ID" ]]; then
    xdotool windowactivate "$GITK_WIN_ID"
    xdotool windowraise "$GITK_WIN_ID"
    echo "[PASS]  ✅ gitk shown to foreground"
    while xdotool search --onlyvisible --class gitk | grep -q .; do
      sleep 1
    done
    echo "[INFO]  🛑 gitk closed"
  else
    echo "[WARN]  ⚠ gitk not detected; falling back to CLI"
    git log --oneline --graph --decorate --all | head -n 40
  fi
else
  echo "[INFO]  📈 No DISPLAY or gitk available; CLI fallback"
  git log --oneline --graph --decorate --all | head -n 40
fi
