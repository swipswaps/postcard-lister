#!/usr/bin/env bash
################################################################################
# FILE: prf_github_one_shot_uploader_v44.sh
# DESC: PRF-compliant GitHub uploader with hardened gitk lifecycle validation
# SPEC: PRF‑COMPOSITE‑2025‑06‑18‑G‑V44‑FINAL
################################################################################

set -euo pipefail
IFS=$'\n\t'
NOW="$(date '+%Y%m%d')"
RUN_ID="$(date '+%H%M%S')"

# ──────────────────────────────────────────────────────────────────────────────
# [P01] TOOLCHAIN VERIFY & AUTO-INSTALL
# ──────────────────────────────────────────────────────────────────────────────
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

# ──────────────────────────────────────────────────────────────────────────────
# [P02] LOGGING SETUP
# ──────────────────────────────────────────────────────────────────────────────
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

# ──────────────────────────────────────────────────────────────────────────────
# [P03] VERIFY REPO CONTEXT & COMMIT BASELINE
# ──────────────────────────────────────────────────────────────────────────────
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "[FAIL] ❌ Not inside a Git repository"
  exit 1
fi

COMMIT_COUNT=$(git rev-list --count HEAD)
if (( COMMIT_COUNT < 1 )); then
  echo "[FAIL] ❌ Repository has no commits; aborting"
  exit 1
fi

# ──────────────────────────────────────────────────────────────────────────────
# [P04] LOAD GITHUB TOKEN
# ──────────────────────────────────────────────────────────────────────────────
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

# ──────────────────────────────────────────────────────────────────────────────
# [P05] REWRITE REMOTE USING TOKEN
# ──────────────────────────────────────────────────────────────────────────────
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

# ──────────────────────────────────────────────────────────────────────────────
# [P06] COMMIT + STAGE + PUSH
# ──────────────────────────────────────────────────────────────────────────────
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

# ──────────────────────────────────────────────────────────────────────────────
# [P07] gitk DISPLAY LIFECYCLE VALIDATION (BLOCKING, HARDENED)
# ──────────────────────────────────────────────────────────────────────────────
if [[ -n "${DISPLAY:-}" ]] || [[ "${XDG_SESSION_TYPE:-}" =~ wayland ]]; then
  echo "[INFO]  📊 Launching gitk GUI (blocking)..."
  echo "[WAIT] ⏳ Waiting for gitk window (max 45s)..."

  for i in {1..45}; do
    GITK_WIN=$(xdotool search --onlyvisible --class gitk 2>/dev/null | head -n1 || true)
    [[ -n "$GITK_WIN" ]] && break
    sleep 1
  done

  if [[ -n "$GITK_WIN" ]]; then
    echo "[PASS] ✅ gitk window found → $GITK_WIN"
    xdotool windowactivate "$GITK_WIN" windowraise "$GITK_WIN"
  else
    echo "[FAIL] ❌ gitk window not detected after 45s"
    git log --graph --decorate --oneline --all | head -n 40
    exit 1
  fi

  echo "[INFO]  🔒 Transferring control to gitk (exec)"
  exec gitk --all  # This blocks and terminates the shell afterward
else
  echo "[INFO] 📈 DISPLAY unset or Wayland not detected—falling back to CLI"
  git log --graph --decorate --oneline --all | head -n 40
fi

# ──────────────────────────────────────────────────────────────────────────────
# [P08] REMOTE RESTORE
# ──────────────────────────────────────────────────────────────────────────────
git remote set-url origin "$REMOTE_URL"
echo "[INFO]  🔐 Remote reset to secure URL"
