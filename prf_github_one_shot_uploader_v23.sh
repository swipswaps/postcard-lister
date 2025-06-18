#!/usr/bin/env bash
################################################################################
# FILE: prf_github_one_shot_uploader_v23.sh
# DESC: Hardened GitHub uploader with full PRF-compliant event messages, token repair,
#       realtime visibility, and diagnostic logging
# SPEC: PRF‑COMPOSITE‑2025‑06‑18‑A (P01–P27 full compliance, no omissions)
################################################################################

set -euo pipefail
IFS=$'\n\t'

# ─────────────────────────── PRF-DECLARED CONSTANTS ───────────────────────────
NOW="$(date '+%Y%m%d')"
RUN_ID="$(date '+%H%M%S')"

# ──────────────── AUTO-INSTALL `ts` IF NOT PRESENT (SELF-HEAL) ────────────────
# WHAT: Ensure real-time timestamping via `ts`
# WHY: Required for masked logging and time-aligned event correlation
# FAIL: Script halts if package install fails
# UX: Self-heal with `[SELF-HEAL]`, `[FAIL]` messages visible in terminal
# DEBUG: Uses fallback detection for `dnf`, `apt`, or exits
if ! command -v ts &>/dev/null; then
  echo "[SELF-HEAL] Installing 'ts' from moreutils…" >&2
  if command -v dnf &>/dev/null; then
    sudo dnf install -y moreutils || { echo "[FAIL] dnf could not install moreutils"; exit 127; }
  elif command -v apt &>/dev/null; then
    sudo apt update && sudo apt install -y moreutils || { echo "[FAIL] apt could not install moreutils"; exit 127; }
  else
    echo "[FAIL] No known package manager found to install 'ts'"; exit 127
  fi
fi

# ──────────────── PRF LOG STRUCTURE: MASKED + RAW SPLIT ────────────────
LOG_DIR="logs/$NOW"
mkdir -p "$LOG_DIR"
LOG_RAW="$LOG_DIR/raw_${RUN_ID}.log"
LOG_MASKED="$LOG_DIR/masked_${RUN_ID}.log"

# PRF: Human-timestamp wrapper fallback if `ts` is shadowed or fails
ts() { awk '{ print strftime("[%F %T]"), $0 }'; }

# ──────── REROUTE STDOUT/STDERR TO TEE + MASKED LOG + LIVE TERMINAL ────────
exec 3>&1 4>&2
exec 1> >(stdbuf -o0 ts | tee -a "$LOG_MASKED" >&3) \
     2> >(stdbuf -o0 ts | tee -a "$LOG_MASKED" >&4)
exec 5>>"$LOG_RAW"

# ──────────────── USER-FACING LOG FORMATTING (FULL TERMINAL) ────────────────
INFO() { printf '\033[1;34m[INFO]  %s\033[0m\n' "$1"; }
WARN() { printf '\033[1;33m[WARN]  %s\033[0m\n' "$1"; }
FAIL() { printf '\033[1;31m[FAIL]  %s\033[0m\n' "$1"; }
PASS() { printf '\033[1;32m[PASS]  %s\033[0m\n' "$1"; }

INFO "📂 Masked log → $LOG_MASKED"
INFO "🗃  Raw log    → $LOG_RAW"

# ──────────────── GH_TOKEN HANDLING AND SELF-HEALING REPAIR ────────────────
# WHAT: Load from `.env` or prompt with repair fallback
# WHY: Avoids manual token entry unless invalid
# FAIL: Script exits if valid token not obtained
# UX: No manual edit needed, fully self-repairs
# DEBUG: Logs source of token and repair actions
GH_TOKEN=""
for ENV_FILE in .env .env.local; do
  if [[ -f "$ENV_FILE" ]]; then
    INFO "🔎 Reading token from $ENV_FILE"
    set -o allexport; source "$ENV_FILE"; set +o allexport
    GH_TOKEN="${GH_TOKEN//\"/}"
    break
  fi
done

# Sanitize token length and format
TOKEN_LEN="${#GH_TOKEN}"
if (( TOKEN_LEN < 40 )) || ! [[ "$GH_TOKEN" =~ ^(ghp_|github_pat_) ]]; then
  WARN "❌ Invalid token (len=$TOKEN_LEN), prompting for re-entry (no manual .env edits)"
  echo -n "Enter valid GitHub PAT: " > /dev/tty
  read -r GH_TOKEN < /dev/tty
  GH_TOKEN="${GH_TOKEN//\"/}"
  TOKEN_LEN="${#GH_TOKEN}"
  if (( TOKEN_LEN < 40 )) || ! [[ "$GH_TOKEN" =~ ^(ghp_|github_pat_) ]]; then
    FAIL "❌ Token still invalid. Exiting."
    exit 1
  fi
  echo "GH_TOKEN=$GH_TOKEN" > .env
  chmod 600 .env
  PASS "✅ Token validated and saved to .env (no manual edit required)"
else
  PASS "✅ Token appears valid (len=$TOKEN_LEN)"
fi

# ──────────────── GIT REMOTE REWRITE TO EMBED TOKEN ────────────────
REMOTE_URL="$(git remote get-url origin 2>/dev/null || true)"
[[ -z "$REMOTE_URL" ]] && { FAIL "❌ No remote 'origin' configured"; exit 1; }

# Rewrite SSH → HTTPS and sanitize user@ tokens
if [[ "$REMOTE_URL" == git@*:* ]]; then
  REMOTE_URL="https://$(echo "$REMOTE_URL" | cut -d':' -f1 | sed 's/git@//')/$(echo "$REMOTE_URL" | cut -d':' -f2-)"
elif [[ "$REMOTE_URL" =~ ^ssh://git@ ]]; then
  REMOTE_URL="https://$(echo "$REMOTE_URL" | sed -E 's#ssh://git@([^/]+)/#\1/#')"
elif [[ "$REMOTE_URL" =~ https://[^@]+@ ]]; then
  REMOTE_URL="$(echo "$REMOTE_URL" | sed -E 's#https://[^/]+@#https://#')"
fi

NEW_REMOTE="https://${GH_TOKEN}@${REMOTE_URL#https://}"
SAFE_REMOTE="${NEW_REMOTE//$GH_TOKEN/********}"
git remote set-url origin "$NEW_REMOTE"
INFO "🔧 Git remote rewritten → $SAFE_REMOTE"

# ──────────────── COMMIT CHANGES IF DETECTED ────────────────
if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  MSG="[PRF] Auto-commit @ $(date '+%F %T')"
  git commit -m "$MSG"
  INFO "📦 Changes auto-committed → $MSG"
else
  INFO "📦 No staged changes to commit"
fi

# ──────────────── PUSH TO ORIGIN + MASKED OUTPUT ────────────────
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
INFO "🚀 Pushing branch '$BRANCH' to origin..."
export GIT_TRACE=5 GIT_TRACE_PACKET=5 GIT_TRACE_SETUP=5 GIT_CURL_VERBOSE=1

PUSH_OUTPUT="$(git push origin "$BRANCH" 2>&1)"
PUSH_EXIT=$?
echo "$PUSH_OUTPUT" | sed "s/${GH_TOKEN}/********/g"

if (( PUSH_EXIT != 0 )); then
  FAIL "❌ Push failed (code $PUSH_EXIT)"
  exit $PUSH_EXIT
fi

if echo "$PUSH_OUTPUT" | grep -q "Everything up-to-date"; then
  PASS "✅ No new changes pushed."
else
  PASS "✅ Push to '$BRANCH' successful."
fi
