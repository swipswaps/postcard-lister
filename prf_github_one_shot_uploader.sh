#!/usr/bin/env bash
################################################################################
# 📜 prf_github_one_shot_uploader.sh — PRF‑COMPLIANT GITHUB COMMIT & PUSH SCRIPT
# WHAT: One-shot GitHub uploader that validates token, commits, and pushes changes
# WHY: Automates upload without manual Git operations or credential re-entry
# FAIL: Script exits with clear diagnostics on invalid token, no remote, or failed push
# UX: Human-readable messages, error masking, terminal feedback at all stages
# DEBUG: All actions are echoed with visible output, token is masked in logs
################################################################################

# ─── PRF RULES ───────────────────────────────────────────────────────────────
# ❌ No manual intervention allowed
# ✅ All behavior must be self-healing, structured, and fully scriptable
# ❗ If it can be typed, it MUST be scripted
# 📜 All block comments must follow: WHAT / WHY / FAIL / UX / DEBUG
# 🧠 No truncation. No placeholders. Full working copy must be shown
# ⛔ Do not offer partial responses, diffs, or patches — emit full scripts inline
# 📣 Do not re-ask for permission. Do not skip or defer requirements

set -euo pipefail
IFS=$'\n\t'

# ─── STEP 1: LOAD GH_TOKEN ───────────────────────────────────────────────────
# WHAT: Load token from environment or .env file if unset
# WHY: Required to authenticate push to GitHub
# FAIL: Script exits if token is not set
# UX: Prints info when .env is loaded
# DEBUG: Uses allexport to silently load token
if [[ -z "${GH_TOKEN-}" ]]; then
  [[ -f .env ]] && { set -o allexport; source .env; set +o allexport; echo "[INFO] ℹ GH_TOKEN loaded from .env"; }
fi
[[ -z "${GH_TOKEN-}" ]] && { echo "[FAIL] ❌ GH_TOKEN missing"; exit 1; }

# ─── STEP 2: VALIDATE GH_TOKEN FORMAT ───────────────────────────────────────
# WHAT: Token must start with valid GitHub prefix and be plausible
# WHY: Prevents malformed token errors or silent HTTP 401 responses
# FAIL: Script exits if token prefix is invalid
# UX: Shows masked summary of token length and type
# DEBUG: Accepts new GitHub token prefixes of all lengths
VALID_PREFIXES=(ghp_ github_pat_ classic_pat_ gho_ ghu_ ghv_ ghs_)
MATCHED=0
for prefix in "${VALID_PREFIXES[@]}"; do
  [[ "$GH_TOKEN" == ${prefix}* ]] && MATCHED=1 && break
done
[[ $MATCHED -eq 0 ]] && { echo "[FAIL] ❌ Invalid GH_TOKEN prefix"; exit 1; }
echo "[PASS] ✅ GH_TOKEN prefix valid (${#GH_TOKEN} chars, masked)."

# ─── STEP 3: CONFIGURE REMOTE WITH TOKEN ─────────────────────────────────────
# WHAT: Convert SSH/Git URLs into HTTPS+token format
# WHY: Avoids prompt for username/password or SSH issues
# FAIL: Script exits if no remote URL is set
# UX: Only masked URLs are printed
# DEBUG: Handles all major GitHub URL formats
REMOTE=$(git remote get-url origin 2>/dev/null || true)
[[ -z "$REMOTE" ]] && { echo "[FAIL] ❌ No remote found"; exit 1; }

if [[ "$REMOTE" == git@*:* ]]; then
  REMOTE="https://$(echo "$REMOTE" | sed 's/git@//' | sed 's/:/\//')"
elif [[ "$REMOTE" == ssh://git@* ]]; then
  REMOTE="https://$(echo "$REMOTE" | sed -E 's#ssh://git@([^/]+)/#\1/#')"
elif [[ "$REMOTE" == https://* ]]; then
  REMOTE="$(echo "$REMOTE" | sed -E 's#https://[^@]+@#https://#')"
fi

AUTH_REMOTE="https://${GH_TOKEN}@${REMOTE#https://}"
MASKED_REMOTE="$(echo "$AUTH_REMOTE" | sed "s/${GH_TOKEN}/********/g")"
git remote set-url origin "$AUTH_REMOTE"
echo "[INFO] 🔧 Remote set: $MASKED_REMOTE"

# ─── STEP 4: AUTO‑COMMIT ─────────────────────────────────────────────────────
# WHAT: Commit all uncommitted changes with timestamp
# WHY: Prevents push rejection on dirty trees
# FAIL: Git errors (e.g. user.name not set) will abort
# UX: Timestamped commit message, user feedback
# DEBUG: Shows status if changes exist
if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  MSG="[PRF] Auto‑commit on $(date '+%Y-%m-%d %H:%M:%S')"
  git commit -m "$MSG"
  echo "[INFO] 📦 Auto‑committed changes."
else
  echo "[INFO] 📦 No uncommitted changes."
fi

# ─── STEP 5: PUSH TO GITHUB ──────────────────────────────────────────────────
# WHAT: Push local branch to remote
# WHY: Reflects local commits on GitHub
# FAIL: Any network/auth issues exit with full error log
# UX: Branch name is shown, push output masked
# DEBUG: Output filtered to hide token
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
echo "[INFO] 🔄 Pushing branch $BRANCH..."
OUT="$(git push origin "$BRANCH" 2>&1)" || {
  echo "$OUT" | sed "s/${GH_TOKEN}/********/g"
  echo "[FAIL] ❌ Push failed."
  exit 1
}
echo "$OUT" | sed "s/${GH_TOKEN}/********/g"
echo "[PASS] ✅ Push succeeded."
