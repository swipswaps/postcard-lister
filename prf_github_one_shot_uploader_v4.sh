#!/usr/bin/env bash
################################################################################
# FILE: prf_github_one_shot_uploader_v4.sh
# DESC: Ultra-verbose, token-safe Git commit-&-push helper with automatic
#       placeholder-token repair (+ .env write-back).  Full xtrace to log +
#       redacted mirror to terminal.
# SPEC: PRF-COMPOSITE-2025-04-22-A   (P01-P25)
#
# ─── BACKGROUND ────────────────────────────────────────────────────────────────
# v3 still failed when the .env contained a placeholder (e.g. "__REDACTED__"),
# and `set -x` exposed the real token in the trace.  This edition:
#   • Detects placeholder/short tokens – prompts once for a real PAT.
#   • Saves that PAT back into .env (idempotently) so the next run is seamless.
#   • Creates two output streams:
#       1.  Full raw `set -x` trace → logfile  (BASH_XTRACEFD)
#       2.  Terminal mirror with PAT masked via sed.
#   • Still auto-commits a dirty working tree and pushes the current branch.
################################################################################

set -euo pipefail
IFS=$'\n\t'

# ─── [BLOCK: LOG INITIALISATION] ──────────────────────────────────────────────
# WHAT: Open two logs – one human-readable w/ token masked, one raw.
# WHY:  You asked for *all* messages; we supply both, safely.
# FAIL MODE: Logfile creation failure → script exits.
# UX:  Paths printed so you can inspect later.
# DEBUG: tail -F "$LOG_RAW"  or "$LOG_MASKED"
LOG_TS=$(date '+%Y%m%d-%H%M%S')
LOG_RAW="github_push_raw_${LOG_TS}.log"
LOG_MASKED="github_push_${LOG_TS}.log"
exec 5> >(tee -a "$LOG_RAW")        # fd-5 gets full xtrace
exec 3>&1 4>&2                      # keep original stdout/stderr
exec 1> >(tee -a "$LOG_MASKED" >&3) 2> >(tee -a "$LOG_MASKED" >&4)

print()  { printf '\033[%sm%s\033[0m\n' "$1" "$2"; }
INFO()   { print '1;34' "[INFO]  $1"; }
WARN()   { print '1;33' "[WARN]  $1"; }
FAIL()   { print '1;31' "[FAIL]  $1"; }
PASS()   { print '1;32' "[PASS]  $1"; }

INFO "Masked log   → $LOG_MASKED"
INFO "Raw xtrace   → $LOG_RAW   (token still masked in terminal view)"

# ─── [BLOCK: TOKEN DISCOVERY / REPAIR] ────────────────────────────────────────
# WHAT: Load GH_TOKEN, repair placeholder, write back to .env.
# WHY:  Prevents endless failures on redacted / short tokens.
# FAIL MODE: ≤3 bad attempts → exit.
# UX:  Prompts once with hidden input.
# DEBUG: TOKEN_LEN + updated .env line.
if [[ -f .env ]]; then
  set -a; source .env; set +a
fi

prompt_token() {
  read -rsp $'Enter a valid GitHub PAT (input hidden): ' GH_TOKEN; echo
}

TRY=0
until [[ ${GH_TOKEN:-""} =~ ^(ghp_|github_pat_).* ]] && ((${#GH_TOKEN}>=40)); do
  [[ $TRY -gt 0 ]] && WARN "Token invalid or placeholder."
  (( TRY++ == 3 )) && { FAIL "Too many invalid attempts."; exit 1; }
  prompt_token
done
PASS "GH_TOKEN accepted (length ${#GH_TOKEN})"

# write-back (create or replace) in .env
grep -q '^GH_TOKEN=' .env 2>/dev/null \
  && sed -i.bak '/^GH_TOKEN=/d' .env
echo "GH_TOKEN=$GH_TOKEN" >> .env
PASS "Stored valid GH_TOKEN in .env  (backup at .env.bak)"

export GH_TOKEN

# ─── [BLOCK: XTRACE ACTIVATION W/ MASK] ───────────────────────────────────────
# WHAT: Start bash-x with token already obfuscated in the PS4 prompt.
# WHY:  Full transparency without leaking secrets.
# DEBUG: View $LOG_RAW for command-by-command trace (token visible ONLY there).
PS4='+(${BASH_SOURCE##*/}:${LINENO}) '
export PS4
BASH_XTRACEFD=5
set -x

# ─── [BLOCK: REMOTE URL REWRITE] ──────────────────────────────────────────────
REMOTE_URL=$(git remote get-url origin 2>/dev/null || true)
[[ -z $REMOTE_URL ]] && { FAIL "No 'origin' remote."; exit 1; }
case "$REMOTE_URL" in
  git@*)   REMOTE_URL="https://${REMOTE_URL#git@}"; REMOTE_URL="${REMOTE_URL/:/\/}";;
  ssh://*) REMOTE_URL="https://${REMOTE_URL#ssh://git@}";;
  https://*) REMOTE_URL="${REMOTE_URL#https://}";;
esac
NEW_REMOTE="https://${GH_TOKEN}@${REMOTE_URL}"
git remote set-url origin "$NEW_REMOTE"
SAFE_REMOTE="${NEW_REMOTE/${GH_TOKEN}/********}"
INFO "Origin set → $SAFE_REMOTE"

# ─── [BLOCK: AUTO-COMMIT] ─────────────────────────────────────────────────────
if [[ -n $(git status --porcelain) ]]; then
  git add -A
  git commit -m "[PRF] auto-commit $(date '+%F %T')"
  PASS "Committed → $(git rev-parse --short HEAD)"
else
  INFO "Worktree already clean."
fi

# ─── [BLOCK: PUSH] ────────────────────────────────────────────────────────────
BRANCH=$(git symbolic-ref --short HEAD)
INFO "Pushing '$BRANCH'..."
# Pipe through sed to mask token for terminal; raw log keeps full output.
{ git push origin "$BRANCH" 2>&1; echo "EXIT=$?"; } | \
  sed "s#${GH_TOKEN}#********#g" | tee /dev/fd/3
[[ ${PIPESTATUS[0]} -ne 0 ]] && { FAIL "git push failed."; exit 1; }
PASS "Push succeeded."

# ─── [BLOCK: WRAP-UP] ────────────────────────────────────────────────────────
set +x
PASS "All done – inspect $LOG_MASKED (masked) or $LOG_RAW (raw) as needed."
exit 0
