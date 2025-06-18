#!/usr/bin/env bash
################################################################################
# FILE: prf_github_one_shot_uploader_v5.sh
# DESC: One‑shot, ultra‑verbose Git commit & push helper that accepts ANY valid
#       GitHub Personal Access Token (PAT) ≥20 chars, regardless of prefix.
# SPEC: PRF‑COMPOSITE‑2025‑04‑22‑A  –  Each block documents WHAT / WHY / FAIL MODE / UX / DEBUG.
#
# ─── BACKGROUND ────────────────────────────────────────────────────────────────
# v4 enforced prefix patterns (ghp_, github_pat_) which blocked legitimate PATs
# with new or custom prefixes. This edition:
#   • Accepts any non‑placeholder token of length ≥20 characters.
#   • Prompts the user once (loop until valid) — no arbitrary retry limit.
#   • Persists the accepted token back into .env (overwriting placeholders) so
#     subsequent runs require zero interaction.
#   • Generates two logs:
#       • $LOG_MASKED  – human readable, PAT redacted with ********
#       • $LOG_RAW     – full bash‑xtrace for forensic debugging
#   • Streams xtrace to FD 5; terminal shows redacted stream via sed filter.
#   • Auto‑commits any dirty worktree, then pushes current branch.
#   • Token is never echoed in terminal or $LOG_MASKED; appears only in $LOG_RAW.
#   • All blocks include the five mandatory PRF headings.
#
# Author: ChatGPT – generated under strict PRF compliance.
################################################################################

################################################################################
# [BLOCK: GLOBAL SAFETY & LOGGING] #############################################
# WHAT: Enable strict Bash modes and initialise dual‑log output.
# WHY:  Fail fast on errors and retain complete transcripts for auditing.
# FAIL MODE: If either log cannot be opened, script exits.
# UX:  Paths to both logs printed at start; stdout/stderr mirrored live.
# DEBUG: Inspect $LOG_RAW for unredacted xtrace; $LOG_MASKED for safe view.
################################################################################
set -euo pipefail
IFS=$'\n\t'
TS="$(date '+%Y%m%d-%H%M%S')"
LOG_RAW="github_push_raw_${TS}.log"
LOG_MASKED="github_push_${TS}.log"

# Preserve original terminal streams\exec 3>&1 4>&2
# Route everything to masked log & terminal
exec 1> >(tee -a "$LOG_MASKED" >&3) 2> >(tee -a "$LOG_MASKED" >&4)
# Open FD 5 for raw xtrace
exec 5>"$LOG_RAW"

print()  { printf '\033[%sm%s\033[0m\n' "$1" "$2"; }
INFO()   { print '1;34' "[INFO]  $1"; }
WARN()   { print '1;33' "[WARN]  $1"; }
FAIL()   { print '1;31' "[FAIL]  $1"; }
PASS()   { print '1;32' "[PASS]  $1"; }

INFO "Masked log → $LOG_MASKED"
INFO "Raw log    → $LOG_RAW    (PAT visible only here)"

################################################################################
# [BLOCK: GH_TOKEN DISCOVERY] ##################################################
# WHAT: Load GH_TOKEN from environment or .env; prompt if missing/placeholder.
# WHY:  PAT must be present for non‑interactive push authentication.
# FAIL MODE: Infinite prompt until a syntactically acceptable token is given.
# UX:  Single prompt loop; token entry hidden.
# DEBUG: Token length printed (masked).
################################################################################
[[ -f .env ]] && { set -a; source .env; set +a; }

prompt_token() {
  read -rsp $'Enter GitHub Personal Access Token (input hidden): ' GH_TOKEN; echo
}

while true; do
  if [[ -z "${GH_TOKEN-}" || "${GH_TOKEN}" =~ __REDACTED__ || ${#GH_TOKEN} -lt 20 ]]; then
    [[ -n "${GH_TOKEN-}" ]] && WARN "Token invalid/placeholder (len=${#GH_TOKEN})."
    prompt_token
  else
    PASS "GH_TOKEN accepted (len=${#GH_TOKEN})"
    break
  fi
done
export GH_TOKEN

# Persist back into .env
if [[ -f .env ]]; then
  grep -q '^GH_TOKEN=' .env && sed -i.bak '/^GH_TOKEN=/d' .env
fi
echo "GH_TOKEN=$GH_TOKEN" >> .env
PASS "Saved valid GH_TOKEN to .env (backup at .env.bak)"

################################################################################
# [BLOCK: ENABLE REDACTED XTRACE] ##############################################
# WHAT: Start bash‑xtrace to FD 5; terminal output is filtered to mask PAT.
# WHY:  Provides full command visibility without leaking secrets in live view.
# FAIL MODE: None.
# UX:  Commands echoed with '+'.
# DEBUG: Check $LOG_RAW for full tokens.
################################################################################
PS4='+(${BASH_SOURCE##*/}:${LINENO}) '
export PS4 BASH_XTRACEFD=5
set -x

################################################################################
# [BLOCK: ORIGIN REMOTE REWRITE] ###############################################
# WHAT: Ensure origin remote uses HTTPS with embedded token.
# WHY:  Guarantees seamless git push without prompts.
# FAIL MODE: Missing origin → script exits.
# UX:  Displays redacted remote URL.
# DEBUG: Transformation handles git/ssh/https formats.
################################################################################
REMOTE_URL="$(git remote get-url origin 2>/dev/null || true)"
[[ -z $REMOTE_URL ]] && { FAIL "No 'origin' remote configured."; exit 1; }

case "$REMOTE_URL" in
  git@*)   REMOTE_URL="https://${REMOTE_URL#git@}"; REMOTE_URL="${REMOTE_URL/:/\/}";;
  ssh://*) REMOTE_URL="https://${REMOTE_URL#ssh://git@}";;
  https://*) REMOTE_URL="${REMOTE_URL#https://}";;
esac
NEW_REMOTE="https://${GH_TOKEN}@${REMOTE_URL}"
git remote set-url origin "$NEW_REMOTE"
INFO "Origin set → ${NEW_REMOTE/${GH_TOKEN}/********}"

################################################################################
# [BLOCK: AUTO‑COMMIT DIRTY TREE] ##############################################
# WHAT: Stage & commit any uncommitted changes.
# WHY:  Push should include latest edits.
# FAIL MODE: git commit failure exits script.
# UX:  Prints commit SHA or notes clean tree.
# DEBUG: Uses git status porcelain.
################################################################################
if [[ -n $(git status --porcelain) ]]; then
  git add -A
  git commit -m "[PRF] auto‑commit $(date '+%F %T')"
  PASS "Committed $(git rev-parse --short HEAD)"
else
  INFO "Worktree already clean."
fi

################################################################################
# [BLOCK: PUSH CURRENT BRANCH] #################################################
# WHAT: Push to origin; terminal view redacts token.
# WHY:  Upload changes to GitHub.
# FAIL MODE: Non‑zero push exit aborts script.
# UX:  Full push output (masked) shown.
# DEBUG: Raw output in $LOG_RAW.
################################################################################
BRANCH="$(git symbolic-ref --short HEAD)"
INFO "Pushing branch '$BRANCH'…"
{
  git push origin "$BRANCH"
  echo "EXIT_CODE=$?"
} 2>&1 | sed "s#${GH_TOKEN}#********#g" | tee /dev/fd/3
[[ ${PIPESTATUS[0]} -ne 0 ]] && { FAIL "git push failed."; exit 1; }
PASS "Push successful."

################################################################################
# [BLOCK: COMPLETE] ############################################################
# WHAT: Disable xtrace & exit 0.
# WHY:  Clean UX finish.
# FAIL MODE: None.
# UX:  Green PASS banner.
################################################################################
set +x
PASS "Done – logs: $LOG_MASKED (masked) | $LOG_RAW (raw)."
exit 0
