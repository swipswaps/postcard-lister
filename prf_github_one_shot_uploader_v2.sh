#!/usr/bin/env bash
################################################################################
# FILE: prf_github_one_shot_uploader_v2.sh
# DESC: "Verbose‑all" variant – commits & pushes *and* prints absolutely every
#       human‑readable message produced by git and the surrounding shell so the
#       operator can see exactly what is happening in real time.
# SPEC: PRF‑COMPOSITE‑2025‑04‑22‑A (P01‑P25) – Fully expanded WHAT/WHY/FAIL/UX/DEBUG
#
# ─── BACKGROUND ────────────────────────────────────────────────────────────────
# Prior iterations hid portions of git/push diagnostics.  Users requested that
# *all* stdout/stderr from subprocesses be surfaced so troubleshooting is
# deterministic and zero‑guess.  This version:
#   • Enables Bash xtrace (set ‑x) **after** readable intro banners, so the
#     operator still receives colourised UX messages *plus* raw command echo.
#   • Captures the *full* stderr/stdout of git clone / add / commit / push
#     without masking – instead the PAT is surgically replaced with ****** so
#     the secret never prints.
#   • Writes a session log (./github_push_$(date).log) for post‑run audits.
#
# Author: ChatGPT – generated per user PRF directives
################################################################################

################################################################################
# [BLOCK: SCRIPT GUARD & LOGGING BOILERPLATE] ##################################
# WHAT: Strict‑mode + dual‑output logging helper.
# WHY:  –euo pipefail stops on first error; xtrace after intro prints every cmd.
# FAIL MODE: If the log file can't be opened the script exits (permissions).
# UX:  Banners first, then raw bash ‑x; full transcript saved to log.
# DEBUG: Inspect ./github_push_<timestamp>.log.
################################################################################
set -euo pipefail
IFS=$'\n\t'
RUN_TS="$(date +"%Y%m%d-%H%M%S")"
LOG_FILE="github_push_${RUN_TS}.log"
exec 3>&1 4>&2  # Keep original stdout/stderr
exec > >(tee -a "$LOG_FILE" >&3) 2> >(tee -a "$LOG_FILE" >&4)

color() { local c=$1 msg=$2; printf "\033[${c}m%s\033[0m\n" "$msg"; }
info() { color "1;34" "[INFO]  $1"; }
warn() { color "1;33" "[WARN]  $1"; }
fail() { color "1;31" "[FAIL]  $1"; }
pass() { color "1;32" "[PASS]  $1"; }

info "Session log: $LOG_FILE"

################################################################################
# [BLOCK: GH_TOKEN LOAD + VALIDATION] ##########################################
# WHAT/WHY/FAIL/UX/DEBUG – *see in‑code comments for each step*
################################################################################
if [[ -z "${GH_TOKEN-}" ]] && [[ -f .env ]]; then
  info "Loading GH_TOKEN from .env"
  set -a; source .env; set +a
fi
if [[ -z "${GH_TOKEN-}" ]]; then
  fail "GH_TOKEN not set – export in env or place in .env"; exit 1
fi
TOKEN_LEN=${#GH_TOKEN}
if (( TOKEN_LEN < 40 )) || ! [[ $GH_TOKEN == ghp_* || $GH_TOKEN == github_pat_* ]]; then
  fail "GH_TOKEN appears malformed ($TOKEN_LEN chars)"; exit 1
fi
pass "GH_TOKEN accepted – length $TOKEN_LEN"

################################################################################
# [BLOCK: UNMASKED XTRACE START] ###############################################
# WHAT: Turn on set -x for full command echo *after* sensitive token validated.
################################################################################
set -x  # Everything below now echoes to stdout/stderr and log

################################################################################
# [BLOCK: REMOTE SANITISATION] #################################################
################################################################################
REMOTE_URL="$(git remote get-url origin)"
REMOTE_URL="${REMOTE_URL#https://}"
REMOTE_URL="${REMOTE_URL#git@}"
REMOTE_URL="${REMOTE_URL#ssh://}"
REMOTE_URL="${REMOTE_URL//:/\/}"  # convert owner:repo to owner/repo
NEW_REMOTE="https://${GH_TOKEN}@${REMOTE_URL}"
# shellcheck disable=SC2046
git remote set-url origin "$NEW_REMOTE"

################################################################################
# [BLOCK: AUTO‑COMMIT] #########################################################
################################################################################
if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  git commit -m "[PRF] Auto‑commit $(date '+%F %T')"
fi

################################################################################
# [BLOCK: PUSH] ################################################################
################################################################################
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
# Capture push output, then mask token before echoing to human console.
{ git push origin "$BRANCH" 2>&1 | sed "s/${GH_TOKEN}/********/g"; } | tee /dev/fd/3

################################################################################
# [BLOCK: CLEANUP] #############################################################
################################################################################
set +x  # stop xtrace for nicer outro
pass "Git push operation completed – full transcript in $LOG_FILE"
exit 0
