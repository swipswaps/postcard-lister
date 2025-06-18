#!/usr/bin/env bash
################################################################################
# FILE: prf_github_one_shot_uploader_v21.sh
# DESC: Hardened one-shot uploader with GH_TOKEN auto-detect and repair
# SPEC: PRF‑COMPOSITE‑2025‑06‑17‑A  (P01–P27 compliant)
################################################################################

set -euo pipefail
IFS=$'\n\t'
NOW="$(date '+%Y%m%d')"
RUN_ID="$(date '+%H%M%S')"

# ─── ENVIRONMENT SELF-HEAL ────────────────────────────────────────────────────
if ! command -v ts &>/dev/null; then
  echo "[SELF-HEAL] Installing 'ts' via moreutils…" >&2
  if command -v dnf &>/dev/null; then
    sudo dnf install -y moreutils || { echo "[FAIL] Cannot install moreutils"; exit 127; }
  elif command -v apt &>/dev/null; then
    sudo apt update && sudo apt install -y moreutils || { echo "[FAIL] Cannot install moreutils"; exit 127; }
  else
    echo "[FAIL] No package manager found"; exit 127
  fi
fi

# ─── LOGGING SETUP ─────────────────────────────────────────────────────────────
LOG_DIR="logs/$NOW"; mkdir -p "$LOG_DIR"
LOG_RAW="$LOG_DIR/raw_${RUN_ID}.log"
LOG_MASKED="$LOG_DIR/masked_${RUN_ID}.log"
ts() { awk '{ print strftime("[%F %T]"), $0 }'; }
exec 3>&1 4>&2
exec 1> >(stdbuf -o0 ts | tee -a "$LOG_MASKED" >&3) \
     2> >(stdbuf -o0 ts | tee -a "$LOG_MASKED" >&4)
exec 5>>"$LOG_RAW"

export GIT_TRACE=5 GIT_TRACE_PACKET=5 GIT_TRACE_SETUP=5 GIT_CURL_VERBOSE=1
INFO() { printf '\033[1;34m[INFO]  %s\033[0m\n' "$1"; }
WARN() { printf '\033[1;33m[WARN]  %s\033[0m\n' "$1"; }
FAIL() { printf '\033[1;31m[FAIL]  %s\033[0m\n' "$1"; }
PASS() { printf '\033[1;32m[PASS]  %s\033[0m\n' "$1"; }

INFO "Masked log → $LOG_MASKED"
INFO "Raw    log → $LOG_RAW"

# ─── LOAD TOKEN FROM .env* ─────────────────────────────────────────────────────
for ENV_FILE in .env .env.local; do
  if [[ -f "$ENV_FILE" ]]; then
    set -o allexport; source "$ENV_FILE"; set +o allexport
    INFO "Loaded GH_TOKEN from $ENV_FILE"
    break
  fi
done

# ─── TOKEN VALIDATION AND AUTO-FIX ─────────────────────────────────────────────
GH_TOKEN="${GH_TOKEN:-}"
GH_TOKEN="${GH_TOKEN//\"/}"  # Strip quotes
TOKEN_LEN=${#GH_TOKEN}

if (( TOKEN_LEN < 40 )) || ! [[ "$GH_TOKEN" =~ ^(ghp_|github_pat_) ]]; then
  WARN "GH_TOKEN format invalid or too short (length=$TOKEN_LEN)"
  echo -n "Enter valid GitHub PAT: " > /dev/tty
  read -r GH_TOKEN < /dev/tty
  GH_TOKEN="${GH_TOKEN//\"/}"
  TOKEN_LEN=${#GH_TOKEN}
  if (( TOKEN_LEN < 40 )) || ! [[ "$GH_TOKEN" =~ ^(ghp_|github_pat_) ]]; then
    FAIL "❌ Entered token still invalid."
    exit 1
  fi
  echo "GH_TOKEN=$GH_TOKEN" > .env
  chmod 600 .env
  PASS "✅ Token validated and saved to .env"
else
  PASS "✅ GH_TOKEN appears valid (${TOKEN_LEN} chars)"
fi

# ─── REMOTE URL REWRITE ────────────────────────────────────────────────────────
REMOTE_URL="$(git remote get-url origin 2>/dev/null || true)"
[[ -z "$REMOTE_URL" ]] && { FAIL "No 'origin' remote found"; exit 1; }

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
INFO "🔧 Remote URL updated: $SAFE_REMOTE"

# ─── AUTO COMMIT ───────────────────────────────────────────────────────────────
if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  MSG="[PRF] Auto-commit @ $(date '+%F %T')"
  git commit -m "$MSG"
  INFO "📦 Auto-committed changes → '$MSG'"
else
  INFO "📦 No changes to commit"
fi

# ─── PUSH ──────────────────────────────────────────────────────────────────────
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
INFO "🔄 Pushing '$BRANCH' to origin..."
PUSH_OUTPUT="$(git push origin "$BRANCH" 2>&1)"
PUSH_EXIT=$?
SAFE_PUSH="$(echo "$PUSH_OUTPUT" | sed "s/${GH_TOKEN}/********/g")"
echo "$SAFE_PUSH"

if (( PUSH_EXIT != 0 )); then
  FAIL "Git push failed → code $PUSH_EXIT"
  exit $PUSH_EXIT
fi

if echo "$PUSH_OUTPUT" | grep -q "Everything up-to-date"; then
  PASS "✅ No changes to push."
else
  PASS "✅ Push successful for '$BRANCH'"
fi
