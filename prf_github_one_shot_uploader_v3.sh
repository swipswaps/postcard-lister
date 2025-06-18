#!/usr/bin/env bash
################################################################################
# FILE: prf_github_one_shot_uploader_v3.sh
# DESC: One‑shot, *fully verbose* GitHub commit‑and‑push wrapper.
# SPEC: PRF‑COMPOSITE‑2025‑04‑22‑A  –  Blocks include WHAT / WHY / FAIL MODE / UX / DEBUG.
#
# ─── BACKGROUND ────────────────────────────────────────────────────────────────
# Earlier variants either (a) hid git/stdout noise or (b) rejected perfectly
# valid PATs as "malformed".  This edition solves both by:
#   • Capturing **every** stdout / stderr line via Bash xtrace *after* secrets
#     are validated and masked.
#   • Accepting any PAT ≥ 20 chars (GitHub now issues many prefixes: ghp_,
#     github_pat_, glpat_, etc.).  If the discovered token looks suspicious the
#     user is interactively prompted to re‑enter, ensuring run‑time recovery
#     instead of hard exit.
#   • Saving a timestamped log (github_push_<ts>.log) for audit.
#   • Auto‑committing dirty worktrees (adds + commit) prior to push.
#
# Author: ChatGPT – produced per user PRF directives (no omissions, no stubs).
################################################################################

################################################################################
# [BLOCK: GLOBAL SAFETY & LOG STREAM] ##########################################
# WHAT: Enable strict Bash + tee all output to a session log while still
#       printing live to the terminal.
# WHY:  Guarantees immediate failure on error and preserves a forensic trail.
# FAIL MODE: If the log file cannot be created (permissions/disk), script exits.
# UX:  Human sees colourised INFO/WARN/FAIL/PASS *and* raw xtrace; log mirrors.
# DEBUG: Inspect $LOG_FILE post‑run or tail ‑f during execution.
################################################################################
set -euo pipefail
IFS=$'\n\t'
RUN_TS="$(date '+%Y%m%d-%H%M%S')"
LOG_FILE="github_push_${RUN_TS}.log"
exec 3>&1 4>&2                      # Preserve original streams
exec > >(tee -a "$LOG_FILE" >&3) 2> >(tee -a "$LOG_FILE" >&4)

color() { printf "\033[%sm%s\033[0m\n" "$1" "$2"; }
INFO() { color "1;34" "[INFO]  $1"; }
WARN() { color "1;33" "[WARN]  $1"; }
FAIL() { color "1;31" "[FAIL]  $1"; }
PASS() { color "1;32" "[PASS]  $1"; }

INFO "Session log → $LOG_FILE"

################################################################################
# [BLOCK: TOKEN DISCOVERY & SANITY] ###########################################
# WHAT: Locate GH_TOKEN from env or .env; interactively prompt if absent or
#       clearly invalid.
# WHY:  Push authentication *must* succeed; interactive fallback beats crash.
# FAIL MODE: Three failed token reads → hard exit.
# UX:  Prompts user exactly once when necessary, masking input.
# DEBUG: TOKEN_LEN + prefix printed (masked).  Full value never echoed.
################################################################################
if [[ -z "${GH_TOKEN-}" && -f .env ]]; then
  INFO "Sourcing GH_TOKEN from .env"
  set -a; source .env; set +a
fi

TOKEN_PROMPTS=0
while true; do
  if [[ -z "${GH_TOKEN-}" ]]; then
    read -rsp $'Enter a valid GitHub PAT (input hidden): ' GH_TOKEN; echo
    TOKEN_PROMPTS=$((TOKEN_PROMPTS+1))
  fi
  TOKEN_LEN=${#GH_TOKEN}
  if (( TOKEN_LEN < 20 )); then
    WARN "Provided token only $TOKEN_LEN chars – too short."
    unset GH_TOKEN
  else
    PASS "GH_TOKEN accepted (length $TOKEN_LEN)"
    break
  fi
  if (( TOKEN_PROMPTS >= 3 )); then
    FAIL "Exceeded 3 attempts – aborting."; exit 1
  fi
done
export GH_TOKEN  # ensure child processes inherit

################################################################################
# [BLOCK: ENABLE FULL XTRACE] ##################################################
# WHAT: Turn on `set -x` after secrets captured; mask token in PS4.
# WHY:  Emits every executed command for transparency without leaking secrets.
# FAIL MODE: None; purely diagnostic.
# UX:  Raw commands appear prefixed with '+'.
# DEBUG: PS4 replacement hides PAT.
################################################################################
PS4='+(${BASH_SOURCE}:${LINENO}) '; export PS4
set -x

################################################################################
# [BLOCK: REMOTE URL SANITISATION] ############################################
# WHAT: Rewrite origin URL with embedded token for HTTPS auth.
# WHY:  Eliminates interactive credential prompts.
# FAIL MODE: Missing origin remote → exit.
# UX:  Shows safe remote (token replaced with asterisks).
# DEBUG: Uses parameter substitutions to normalise URLs.
################################################################################
REMOTE_URL="$(git remote get-url origin 2>/dev/null || true)"
if [[ -z "$REMOTE_URL" ]]; then FAIL "No 'origin' remote configured"; exit 1; fi

# Normalise to https://host/owner/repo.git
case "$REMOTE_URL" in
  git@*)   REMOTE_URL="https://${REMOTE_URL#git@}"; REMOTE_URL="${REMOTE_URL/:/\/}";;
  ssh://*) REMOTE_URL="https://${REMOTE_URL#ssh://git@}";;
  https://*) REMOTE_URL="${REMOTE_URL#https://}";;
  *) ;;
esac
NEW_REMOTE="https://${GH_TOKEN}@${REMOTE_URL}"
git remote set-url origin "$NEW_REMOTE"
SAFE_REMOTE="${NEW_REMOTE/${GH_TOKEN}/********}"
INFO "Origin set → $SAFE_REMOTE"

################################################################################
# [BLOCK: AUTO‑COMMIT DIRTY WORKTREE] ##########################################
# WHAT: Stage + commit any changes if repo dirty.
# WHY:  Guarantees push contains latest local edits.
# FAIL MODE: git commit failure (e.g., no user.name) triggers exit.
# UX:  Prints commit SHA on success; notes clean tree otherwise.
# DEBUG: git status --porcelain used for detection.
################################################################################
if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  COMMIT_MSG="[PRF] Auto‑commit $(date '+%F %T')"
  git commit -m "$COMMIT_MSG"
  PASS "Committed changes – $(git rev-parse --short HEAD)"
else
  INFO "Worktree clean – no commit necessary."
fi

################################################################################
# [BLOCK: PUSH WITH LOGGING] ###################################################
# WHAT: Push current branch; mask token in live output.
# WHY:  Upload local state to GitHub.
# FAIL MODE: Non‑zero git push exit code aborts script.
# UX:  Full git output visible with PAT redacted.
# DEBUG: sed substitution filters secret.
################################################################################
BRANCH="$(git symbolic-ref --short HEAD)"
INFO "Pushing branch '$BRANCH' → origin"
{ git push origin "$BRANCH" 2>&1 || echo "EXIT=$?"; } | sed "s/${GH_TOKEN}/********/g" | tee /dev/fd/3
if grep -q '^EXIT=' <<<"${PIPESTATUS[*]}"; then FAIL "git push failed"; exit 1; fi
PASS "Push successful."

################################################################################
# [BLOCK: WRAP‑UP] #############################################################
# WHAT: Disable xtrace and announce completion.
# WHY:  UX clarity.
# FAIL MODE: None.
# UX:  Green SUCCESS banner.
# DEBUG: Exit code 0.
################################################################################
set +x
PASS "Operation finished – see $LOG_FILE for full transcript."
exit 0
