#!/usr/bin/env bash
################################################################################
# FILE: prf_github_one_shot_uploader_v45.sh
# DESC: PRF-compliant GitHub uploader with deterministic gitk lifecycle
# SPEC: PRF‑COMPOSITE‑2025‑06‑18‑G‑V45‑FINAL
################################################################################

set -euo pipefail
IFS=$'\n\t'
NOW="$(date '+%Y%m%d')"
RUN_ID="$(date '+%H%M%S')"

# WHAT: Ensure required tools are present
# WHY: Prevent runtime errors, support git and GUI validation
# FAIL: Script aborts if a tool is missing and cannot be installed
# UX: User sees real-time logs of tool checks
# DEBUG: All tools installed via dnf/apt automatically

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

# WHAT: Setup log files for raw and masked outputs
# WHY: Debugging, replay, traceability
# FAIL: Fails gracefully if log path cannot be created
# UX: Both human-readable and raw logs available
# DEBUG: Uses awk timestamps, stdbuf ensures flush

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

# WHAT: Validate Git repository context
# WHY: Prevent misuse outside of version control
# FAIL: Aborts if not in a Git repo or no commits
# UX: User gets explicit failure reasons
# DEBUG: Uses rev-parse and rev-list

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "[FAIL] ❌ Not inside a Git repository"
  exit 1
fi

COMMIT_COUNT=$(git rev-list --count HEAD)
if (( COMMIT_COUNT < 1 )); then
  echo "[FAIL] ❌ Repository has no commits; aborting"
  exit 1
fi

# WHAT: Load GitHub token from environment or prompt
# WHY: Needed for secure HTTPS-based remote operations
# FAIL: If token is invalid, it re-prompts and persists securely
# UX: Warns user of issues with token format
# DEBUG: Saves token with chmod 600

GH_TOKEN=""
for ENV_FILE in .env .env.local; do
  if [[ -f "$ENV_FILE" ]]; then
    set -o allexport; source "$ENV_FILE"; set +o allexport
    echo "[INFO]  🔎 Loaded token from $ENV_FILE"
    break
  fi
done

GH_TOKEN="${GH_TOKEN//\"/}"
TOKEN_PATTERN='^[A-Za-z0-9_-]{40,}$'
if (( ${#GH_TOKEN} < 40 )) || ! [[ "$GH_TOKEN" =~ $TOKEN_PATTERN ]]; then
  echo "[WARN]  ❌ Invalid token; prompting"
  echo -n "Enter GitHub PAT: " > /dev/tty
  read -r GH_TOKEN < /dev/tty
  if (( ${#GH_TOKEN} < 40 )) || ! [[ "$GH_TOKEN" =~ $TOKEN_PATTERN ]]; then
    echo "[FAIL] Token invalid after re-entry"
    exit 1
  fi
  echo "GH_TOKEN=\"$GH_TOKEN\"" > .env
  chmod 600 .env
  echo "[PASS] ✅ Token saved"
else
  echo "[PASS] ✅ GH_TOKEN valid"
fi

# WHAT: Rewrite remote URL with injected token
# WHY: Git push over HTTPS requires authentication
# FAIL: Exits if no origin URL or malformed remote
# UX: Shows masked remote for confirmation
# DEBUG: Uses sed and cut to clean SSH/HTTPS variants

REMOTE_URL="$(git remote get-url origin 2>/dev/null || true)"
[[ -z "$REMOTE_URL" ]] && { echo "[FAIL] ❌ No origin remote"; exit 1; }

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

# WHAT: Commit and push changes
# WHY: Upload latest work to GitHub
# FAIL: If push fails, prints output and exits
# UX: Status, commit, and push logs shown
# DEBUG: Tracks git status and uses push output capture

git status
git add -A
if [[ -n "$(git status --porcelain)" ]]; then
  MSG="[PRF] Auto-commit @ $(date '+%F %T')"
  git commit -m "$MSG"
  echo "[INFO]  📦 Committed → $MSG"
else
  echo "[INFO]  📦 No new changes"
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
echo "[INFO]  🚀 Pushing branch '$BRANCH'"
PUSH_OUTPUT="$(git push origin "$BRANCH" 2>&1)"
PUSH_EXIT=$?
echo "${PUSH_OUTPUT//$GH_TOKEN/********}"

if (( PUSH_EXIT != 0 )); then
  echo "[FAIL]  ❌ Push failed"
  exit $PUSH_EXIT
fi
echo "[PASS] ✅ Push succeeded"

# WHAT: Launch gitk, ensure it's visible, and wait for user close
# WHY: Validate commit visibility visually
# FAIL: If gitk fails to appear, fallback to CLI
# UX: Deterministic blocking until GUI closed or CLI fallback used
# DEBUG: Uses xdotool + PID wait

if [[ -n "${DISPLAY:-}" && "${XDG_SESSION_TYPE:-}" =~ (x11|wayland) ]]; then
  echo "[INFO]  📊 Launching gitk GUI in foreground..."

  gitk --all &
  GITK_PID=$!

  echo "[WAIT] ⏳ Waiting for gitk window (max 45s)..."
  for i in {1..45}; do
    GITK_WIN=$(xdotool search --name gitk 2>/dev/null | head -n1 || true)
    [[ -n "$GITK_WIN" ]] && break
    sleep 1
  done

  if [[ -n "$GITK_WIN" ]]; then
    echo "[PASS] ✅ gitk window detected ($GITK_WIN), raising..."
    xdotool windowactivate "$GITK_WIN" windowraise "$GITK_WIN"
    echo "[WAIT] 🔒 Waiting for gitk to exit (PID=$GITK_PID)..."
    wait $GITK_PID
    echo "[PASS] ✅ gitk closed normally"
  else
    echo "[FAIL] ❌ gitk window never appeared — CLI fallback"
    kill "$GITK_PID" 2>/dev/null || true
    git log --graph --decorate --oneline --all | head -n 40
  fi
else
  echo "[INFO] 📈 DISPLAY or XDG_SESSION_TYPE not valid — CLI fallback"
  git log --graph --decorate --oneline --all | head -n 40
fi

# WHAT: Restore remote to original without token
# WHY: Secure removal of embedded credentials
# FAIL: None; silently restores
# UX: User sees reset confirmation
# DEBUG: Uses set-url to revert token

git remote set-url origin "$REMOTE_URL"
echo "[INFO]  🔐 Remote reset to secure URL"
