#!/usr/bin/env bash
################################################################################
# FILE: prf_github_one_shot_uploader_v46.sh
# DESC: PRF-compliant GitHub uploader with strict gitk GUI lifecycle control
# SPEC: PRF‑COMPOSITE‑2025‑06‑18‑H‑V46‑FINAL
################################################################################

set -euo pipefail
IFS=$'\n\t'
NOW="$(date '+%Y%m%d')"
RUN_ID="$(date '+%H%M%S')"

# WHAT: Ensure required tools are installed
# WHY: Prevent failures during runtime and enforce PRF toolchain standards
# FAIL: Aborts if dnf/apt unavailable or install fails
# UX: Provides self-healing feedback
# DEBUG: Validates git, gitk, xdotool, and moreutils

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

# WHAT: Setup dual-mode logging (masked and raw)
# WHY: PRF requires auditable, persistent, readable logs
# FAIL: Abort if logs can't be written
# UX: User sees file paths
# DEBUG: Real-time streaming via stdbuf and awk

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

# WHAT: Ensure we are inside a git repository with at least one commit
# WHY: gitk cannot function without commits
# FAIL: Exit if not in repo or zero commits
# UX: Warns and exits clearly
# DEBUG: Uses rev-parse and rev-list

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "[FAIL] ❌ Not inside a Git repository"
  exit 1
fi

if (( $(git rev-list --count HEAD) < 1 )); then
  echo "[FAIL] ❌ Repository has no commits"
  exit 1
fi

# WHAT: Load GitHub token or prompt securely
# WHY: Required for HTTPS authentication
# FAIL: Aborts if invalid token provided twice
# UX: Saves token to .env with permissions
# DEBUG: Verifies length and regex match

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
  echo "[WARN]  ❌ Invalid token; prompting..."
  echo -n "Enter GitHub PAT: " > /dev/tty
  read -r GH_TOKEN < /dev/tty
  GH_TOKEN="${GH_TOKEN//\"/}"
  if (( ${#GH_TOKEN} < 40 )) || ! [[ "$GH_TOKEN" =~ $TOKEN_PATTERN ]]; then
    echo "[FAIL] Token invalid after re-entry"
    exit 1
  fi
  echo "GH_TOKEN=\"$GH_TOKEN\"" > .env
  chmod 600 .env
  echo "[PASS] ✅ Token saved to .env"
else
  echo "[PASS] ✅ GH_TOKEN valid"
fi

# WHAT: Rewrite remote with token for push
# WHY: Git requires credentials to push over HTTPS
# FAIL: Aborts if no remote found
# UX: Redacts token in visible remote
# DEBUG: Converts SSH/HTTPS to usable format

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

# WHAT: Commit and push staged changes
# WHY: PRF requires committed state before push
# FAIL: Push error aborts script
# UX: Status, commit, and push output is verbose
# DEBUG: Uses porcelain + masked push output

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
  echo "[FAIL] ❌ Push failed"
  exit $PUSH_EXIT
fi
echo "[PASS] ✅ Push succeeded"

# WHAT: Block and validate gitk GUI visibility
# WHY: PRF requires visual confirmation of commit graph
# FAIL: Fallbacks to CLI if gitk fails visibility test
# UX: Uses `xdotool search`, raises window, then `exec`s
# DEBUG: 45s timeout loop for gitk detection

if [[ -n "${DISPLAY:-}" && "${XDG_SESSION_TYPE:-}" =~ (x11|wayland) ]]; then
  echo "[INFO]  📊 Launching gitk GUI (with strict lifecycle enforcement)..."
  echo "[WAIT] ⏳ Waiting for gitk window..."

  for i in {1..45}; do
    GITK_WIN=$(xdotool search --sync --class gitk 2>/dev/null | head -n1 || true)
    [[ -n "$GITK_WIN" ]] && break
    sleep 1
  done

  if [[ -n "$GITK_WIN" ]]; then
    echo "[PASS] ✅ gitk window visible: $GITK_WIN"
    xdotool windowactivate "$GITK_WIN" windowraise "$GITK_WIN"
    echo "[EXEC] 🔁 Executing gitk → script ends after this line"
    exec gitk --all
  else
    echo "[FAIL] ❌ gitk window not detected after 45s — using CLI fallback"
    git log --graph --decorate --oneline --all | head -n 40
  fi
else
  echo "[INFO] 📈 DISPLAY or XDG_SESSION_TYPE not valid — using CLI fallback"
  git log --graph --decorate --oneline --all | head -n 40
fi

# WHAT: Restore safe remote (no token)
# WHY: Prevent token leaks in future git remote get-url
# FAIL: Silent restore, no exit required
# UX: Confirms reversion
# DEBUG: Uses set-url with original remote

git remote set-url origin "$REMOTE_URL"
echo "[INFO]  🔐 Remote reset to secure URL"
