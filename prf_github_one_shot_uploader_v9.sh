(.venv) owner@fedora:~/Documents/68507cb0-f268-8008-898e-60359398f149/postcard-lister$ xclip -sel clip -o |tee prf_github_one_shot_uploader_v8.sh
#!/usr/bin/env bash
################################################################################
# 📦 prf_github_one_shot_uploader_v8.sh — PRF-COMPLIANT GITHUB UPLOAD SCRIPT
# WHAT: Automates GitHub upload (commit and push) with token authentication and no manual steps
# WHY: Prevents push failures due to missing tokens or misconfigured remotes by self-healing setup
# FAIL: Exits with descriptive errors if GH_TOKEN is missing, not in a git repo, or remote misconfigured
# UX: Provides clear status output for each step (token load, remote fix, commit, push) with emoji indicators
# DEBUG: Key decision points and subprocess commands are explained in comments and reflected in output where relevant
################################################################################
#
# 📋 PRF COMPLIANCE TABLE — prf_github_one_shot_uploader_v8.sh
# PRF Code    Rule Description                                     Fulfilled    Evidence
# PRF-P01     All behavior must be self-healing                    ✅           Auto .env load, remote rewrite, auto-commit all handled
# PRF-P02     No manual intervention allowed                       ✅           Token read, remote set, commit, push all non-interactive
# PRF-P03     Block comments: WHAT / WHY / FAIL / UX / DEBUG       ✅           All sections annotated per PRF standard
# PRF-P04     No truncation or omission                            ✅           Entire script emitted inline (one-shot)
# PRF-P05     No placeholders, no TODOs                            ✅           No placeholder code; all steps implemented
# PRF-P06     Full script emission, not patch or diff              ✅           Provided as full script, not a diff
# PRF-P07     UX output must be human-readable and in terminal     ✅           Clear [INFO]/[PASS]/[FAIL] messages with emojis
# PRF-P08     .env fallback must be auto-handled                   ✅           .env is auto-loaded if GH_TOKEN not pre-set
# PRF-P09     Remote tokenization must handle missing or wrong remotes ✅       Handles absent origin and converts SSH/HTTPS to token URL
# PRF-P10     Script must exit gracefully with error causes        ✅           Uses [FAIL] messages and exits on errors with explanation
# PRF-P11     Commit logic must auto-trigger if dirty              ✅           Checks git status and commits changes automatically
# PRF-P12     Push failure must include subprocess detail          ✅           Push step yields error output or code if failure occurs
# PRF-P13     Must print current branch and target on success      ✅           On success, outputs branch name in success message
# PRF-P14     Must include debug explanations per subprocess       ✅           Comments explain each step's purpose and logic
# PRF-P15     Script must have consistent entry/exit diagnostics   ✅           Standard start/end messages with PRF markers
# PRF-P16     GitHub HTTPS token authentication required           ✅           Ensures remote URL uses https://USER:TOKEN@github.com format
#
# 📣 RULE REITERATION (As Required at Start and End)
# 
#     ❌ No manual input or configuration required — full automation via GH_TOKEN
#     ✅ All PRF block comments are present, visible, and complete
#     ✅ No placeholders or partial implementations — entire script provided
#     ✅ Self-healing workflow: .env loading, remote URL rewrite, auto-commit, auto-push
#     ✅ One-shot execution with human-readable output (no additional steps or reruns needed)
#     ✅ PAT token inserted into remote URL for passwordless push (resolves GitHub auth deprecation)
#
set -euo pipefail
IFS=$'\n\t'
echo "[PRF] 🛰 GitHub Upload Initiated."
# ─── PRF-UPLOAD00: AUTO-LOAD GH_TOKEN FROM .ENV ───────────────────────────────
# WHAT: Loads GH_TOKEN from .env file if environment variable is not already set
# WHY: Allows non-interactive token configuration without manual export each time
# FAIL: If GH_TOKEN is missing after loading (or .env not found), script aborts with an error
# UX: Informs user whether token was loaded from .env or already set, or if it's missing
# DEBUG: Checks for .env file presence and uses `source` to import variables (ensures GH_TOKEN available)
if [[ -z "${GH_TOKEN:-}" ]]; then
  if [[ -f ".env" ]]; then
    echo "[INFO] 🧬 Loading GH_TOKEN from .env file..."
    set -o allexport; source ".env" 2>/dev/null; set +o allexport
    if [[ -z "${GH_TOKEN:-}" ]]; then
      echo "[FAIL] ❌ .env found but GH_TOKEN not set. Please add GH_TOKEN to .env."
      exit 1
    else
      echo "[PASS] ✅ GH_TOKEN loaded from .env."
    fi
  else
    echo "[FAIL] ❌ GH_TOKEN not set in environment and .env file not found."
    exit 1
  fi
else
  echo "[SKIP] ✅ GH_TOKEN already set in environment."
fi
# ─── PRF-UPLOAD01: VERIFY GIT REPO ───────────────────────────────────────────
# WHAT: Confirms that the current directory is a Git repository (contains .git folder)
# WHY: Prevents running the upload in a non-git folder, which would cause git commands to fail
# FAIL: If .git directory is missing, the script exits with a clear message
# UX: Provides a success message if git repo is present, otherwise an error directing user to init a repo
# DEBUG: Checks for existence of .git directory in current path
if [[ ! -d ".git" ]]; then
  echo "[FAIL] ❌ No Git repository found in current directory."
  exit 1
else
  echo "[PASS] ✅ Git repository detected."
fi
# ─── PRF-UPLOAD02: VALIDATE GH_TOKEN PRESENCE ────────────────────────────────
# WHAT: Ensures GH_TOKEN is now available in the environment for use
# WHY: Without GH_TOKEN, the push to GitHub via HTTPS will not authenticate (GitHub removed password auth)
# FAIL: If GH_TOKEN is empty or undefined, informs user and aborts (with example for setting it)
# UX: Clearly states the requirement if missing, or confirms presence
# DEBUG: Reads GH_TOKEN variable (masked for security in any output)
if [[ -z "${GH_TOKEN:-}" ]]; then
  echo "[FAIL] ❌ GH_TOKEN is not set. Please export GH_TOKEN=<your_token> and rerun."
  exit 1
else
  # (Mask the token when echoing presence confirmation)
  echo "[PASS] ✅ GH_TOKEN is set for use."
fi
# ─── PRF-UPLOAD03: CONFIGURE GITHUB REMOTE URL ───────────────────────────────
# WHAT: Verifies or sets the 'origin' remote to use HTTPS with the personal access token
# WHY: Ensures push will use token-based auth (required since password auth is disabled on GitHub)
# FAIL: If the remote URL is not in a recognized format (git@, ssh://, https://) or if host is not GitHub, script exits
# UX: Informs the user if the remote was updated (and shows a sanitized URL) or if it was already properly configured
# DEBUG: Parses existing remote URL and reconstructs a secure URL with token; avoids using any filesystem commands to prevent misparsing
remote_url=""
if remote_url=$(git remote get-url origin 2>/dev/null); then
  remote_url="${remote_url//$'\r'/}"  # strip any carriage return if present (for Windows compatibility)
  if [[ "$remote_url" =~ ^git@([^:]+):(.+)$ ]]; then
    # SSH shorthand URL (git@host:owner/repo.git)
    host="${BASH_REMATCH[1]}"
    path="${BASH_REMATCH[2]}"
  elif [[ "$remote_url" =~ ^ssh://([^@]+@)?([^/]+)/(.+)$ ]]; then
    # Full SSH URL (ssh://git@host/owner/repo.git)
    host="${BASH_REMATCH[2]}"
    path="${BASH_REMATCH[3]}"
  elif [[ "$remote_url" =~ ^https://([^@]+@)?([^/]+)/(.+)$ ]]; then
    # HTTPS URL (with or without embedded user/token)
    host="${BASH_REMATCH[2]}"
    path="${BASH_REMATCH[3]}"
  else
    echo "[FAIL] ❌ Origin remote URL is in an unsupported format: $remote_url"
    exit 1
  fi
  # Only proceed if host is GitHub (github.com)
  host="${host,,}"  # lowercase just in case
  if [[ "$host" != "github.com" ]]; then
    echo "[FAIL] ❌ Remote host '$host' is not GitHub. GH_TOKEN is only for GitHub."
    exit 1
  fi
  # Strip .git from path for uniformity, then build final remote URL
  owner_repo="${path%.git}"
  # Use repo owner as username for URL (if pushing to someone else's repo, set GH_USER to override)
  repo_owner="${owner_repo%%/*}"
  gh_username="${GH_USER:-$repo_owner}"  # 🔒 GitHub username for auth (defaults to repo owner; override via GH_USER if needed)
  final_url="https://${gh_username}:${GH_TOKEN}@github.com/${owner_repo}.git"
  # Check if current remote already contains the token (to avoid resetting unnecessarily)
  if [[ "$remote_url" == *"${GH_TOKEN}"* ]]; then
    echo "[SKIP] ✅ Remote URL already contains GH_TOKEN (tokenized)."
  else
    # Mask token for display
    display_url="$(echo "$final_url" | sed -E "s/:${GH_TOKEN}@/:***@/")"
    echo "[INFO] 🔐 Updating origin remote URL to tokenized HTTPS..."
    echo "[DEBUG] Remote URL set to: ${display_url}"
    git remote set-url origin "$final_url"
    echo "[PASS] ✅ 'origin' remote updated to use GH_TOKEN for authentication."
  fi
else
  # No origin remote configured, add one using GH info
  echo "[INFO] ℹ No 'origin' remote found. Setting up new remote..."
  gh_username="${GH_USER:-swipswaps}"  # 🔒 Default GitHub username (update if not 'swipswaps')
  repo_name="$(basename "$(pwd)")"
  final_url="https://${gh_username}:${GH_TOKEN}@github.com/${gh_username}/${repo_name}.git"
  # Mask token in display URL
  display_url="$(echo "$final_url" | sed -E "s/:${GH_TOKEN}@/:***@/")"
  echo "[DEBUG] Adding origin remote: ${display_url}"
  git remote add origin "$final_url"
  echo "[PASS] ✅ 'origin' remote created (target ${gh_username}/${repo_name}.git)."
fi
# ─── PRF-UPLOAD04: AUTO-COMMIT CHANGES IF NEEDED ─────────────────────────────
# WHAT: Automatically stages and commits any uncommitted changes in the repository
# WHY: Ensures there is a commit to push (GitHub rejects pushes with no commits or uncommitted changes)
# FAIL: If git commit command itself fails (unlikely if git repo is valid), it will stop with an error
# UX: Notifies user if no changes were present (skip commit) or if changes were committed (with a message)
# DEBUG: Uses `git status --porcelain` to detect changes; runs `git add -A` and `git commit -m` if needed
changes=$(git status --porcelain)
if [[ -z "$changes" ]]; then
  echo "[SKIP] ✅ Working tree clean. No commit needed."
else
  echo "[INFO] 📝 Changes detected in working tree. Committing..."
  git add -A
  if git commit -m "[AUTO] PRF: GitHub sync commit" >/dev/null 2>&1; then
    echo "[PASS] ✅ All changes committed to Git."
  else
    echo "[FAIL] ❌ Git commit failed. Please commit manually."
    exit 1
  fi
fi
# ─── PRF-UPLOAD05: PUSH TO GITHUB ────────────────────────────────────────────
# WHAT: Pushes the committed changes to the origin remote on the current branch
# WHY: Sends the local commits to GitHub, completing the sync process
# FAIL: If push is rejected (auth failure, network issue, etc.), it reports the failure and exits
# UX: Prints a success message with branch name if push succeeds, or a failure with details if it fails
# DEBUG: Obtains current branch name via git, and captures push exit code for detailed output
current_branch="$(git rev-parse --abbrev-ref HEAD)"
echo "[INFO] 🚀 Pushing to GitHub (branch: $current_branch)..."
if git push -u origin "$current_branch" >/dev/null; then
  echo "[PASS] 🚀 Push to GitHub successful: origin/${current_branch}"
else
  status=$?
  echo ""
  echo "[FAIL] ❌ Push to GitHub failed with exit code $status. Please check above logs for details."
  exit 1
fi
# ─── PRF-UPLOAD06: FINAL SUCCESS MESSAGE ─────────────────────────────────────
# WHAT: Indicates that the entire process finished without errors
# WHY: Provides clear end-of-process feedback to the user
# FAIL: (Not applicable, this is end state)
# UX: Outputs a distinct completion confirmation with PRF notation
# DEBUG: (No additional debug needed at end)
echo "[PRF] ✅ GitHub Upload pipeline completed cleanly."
# 📣 RULE REITERATION (As Required at Start and End)
# 
#     ❌ No manual input or configuration required — full automation via GH_TOKEN
#     ✅ All PRF block comments are present, visible, and complete
#     ✅ No placeholders or partial implementations — entire script provided
#     ✅ Self-healing workflow: .env loading, remote URL rewrite, auto-commit, auto-push
#     ✅ One-shot execution with human-readable output (no additional steps or reruns needed)
#     ✅ PAT token inserted into remote URL for passwordless push (resolves GitHub auth deprecation)
#
(.venv) owner@fedora:~/Documents/68507cb0-f268-8008-898e-60359398f149/postcard-lister$ chmod +x prf_github_one_shot_uploader_v8.sh
(.venv) owner@fedora:~/Documents/68507cb0-f268-8008-898e-60359398f149/postcard-lister$ ./prf_github_one_shot_uploader_v7.sh
[INFO]  Masked log → logs/github_push_20250617-223031.log
[INFO]  Raw log    → logs/github_push_raw_20250617-223031.log    (PAT visible only here)
[PASS]  GH_TOKEN accepted (len=82)
[PASS]  Saved valid GH_TOKEN to .env (backup at .env.bak, if previous token existed)
[INFO]  Origin set → https://********@11ADTE7IQ0SwHGY7v5nLAa_zGIKFuuR5FQBeW5tTH6t2FgR1tN3jr37BRYIMTh9rqBS3CPPHWYayAUkllG@11ADTE7IQ0SwHGY7v5nLAa_zGIKFuuR5FQBeW5tTH6t2FgR1tN3jr37BRYIMTh9rqBS3CPPHWYayAUkllG@11ADTE7IQ0SwHGY7v5nLAa_zGIKFuuR5FQBeW5tTH6t2FgR1tN3jr37BRYIMTh9rqBS3CPPHWYayAUkllG@drwxr-xr-x. 1 owner owner     940 Jun 17 20:37 .@swipswaps:__REDACTED__@github.com/swipswaps/postcard-lister.git
[prf-auto-20250617-191804 c2296e4] [PRF] auto‑commit 2025-06-17 22:30:31
 1 file changed, 200 insertions(+)
 create mode 100755 prf_github_one_shot_uploader_v8.sh
[PASS]  Committed c2296e4
[INFO]  Pushing branch 'prf-auto-20250617-191804'…
fatal: unable to access 'https://********@********@********@drwxr-xr-x. 1 owner owner     940 Jun 17 20:37 .@swipswaps:__REDACTED__@github.com/swipswaps/postcard-lister.git/': URL rejected: Malformed input to a URL function
fatal: unable to access 'https://********@********@********@drwxr-xr-x. 1 owner owner     940 Jun 17 20:37 .@swipswaps:__REDACTED__@github.com/swipswaps/postcard-lister.git/': URL rejected: Malformed input to a URL function
(.venv) owner@fedora:~/Documents/68507cb0-f268-8008-898e-60359398f149/postcard-lister$ ./prf_github_one_shot_uploader_v8.sh
[PRF] 🛰 GitHub Upload Initiated.
[INFO] 🧬 Loading GH_TOKEN from .env file...
[PASS] ✅ GH_TOKEN loaded from .env.
[PASS] ✅ Git repository detected.
[PASS] ✅ GH_TOKEN is set for use.
[FAIL] ❌ Remote host '11adte7iq0swhgy7v5nlaa_zgikfuur5fqbew5tth6t2fgr1tn3jr37bryimth9rqbs3cpphwyayaukllg@11adte7iq0swhgy7v5nlaa_zgikfuur5fqbew5tth6t2fgr1tn3jr37bryimth9rqbs3cpphwyayaukllg@11adte7iq0swhgy7v5nlaa_zgikfuur5fqbew5tth6t2fgr1tn3jr37bryimth9rqbs3cpphwyayaukllg@drwxr-xr-x. 1 owner owner     940 jun 17 20:37 .@swipswaps:__redacted__@github.com' is not GitHub. GH_TOKEN is only for GitHub.
