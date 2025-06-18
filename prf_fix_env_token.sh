#!/usr/bin/env bash
################################################################################
# FILE: prf_fix_env_token_final.sh
# DESC: Final PRF-compliant GitHub token fixer (.env/.env.local auto-rewriter)
# SPEC: PRF‑COMPOSITE‑2025‑06‑18‑C (Fully inline, deterministic, auditable)
################################################################################

set -euo pipefail
IFS=$'\n\t'

# WHAT:
#   GitHub Personal Access Tokens must be validated and stored in .env or .env.local
# WHY:
#   Prevent stalling or authentication errors in token-dependent scripts
# FAIL:
#   This script exits with an error code if no token file is found or the new token is invalid
# UX:
#   All prompts and results are human-readable, visible in the terminal, and auditable
# DEBUG:
#   Displays token length, regex checks, patch file used, and exact result status

# Define the minimal token length (per GitHub requirements) and a fallback regex
MIN_TOKEN_LEN=40
VALID_TOKEN_REGEX='^[A-Za-z0-9_-]{40,}$'
PATCHED=false

# Loop through each allowed .env file
for FILE in .env .env.local; do
  if [[ -f "$FILE" ]]; then

    # WHAT:
    #   Extract and validate the GH_TOKEN line
    # WHY:
    #   Detect malformed, missing, or unsafe token contents
    # DEBUG:
    #   Use grep/cut to extract, tr to sanitize quotes
    echo "# [INFO] Found token file: $FILE"
    CURRENT="$(grep '^GH_TOKEN=' "$FILE" | cut -d= -f2- | tr -d '"')"
    LENGTH=${#CURRENT}

    # WHAT:
    #   Validate against min length and regex (characters, symbols allowed by GitHub)
    # WHY:
    #   New GitHub tokens may be prefixless but must still meet entropy and syntax
    # UX:
    #   Prompt if token is too short or malformed
    if (( LENGTH < MIN_TOKEN_LEN )) || ! [[ "$CURRENT" =~ $VALID_TOKEN_REGEX ]]; then
      echo "# [WARN] Invalid GH_TOKEN in $FILE (len=$LENGTH)"
      echo -n "# [PROMPT] Enter corrected GitHub token: "
      read -r FIXED
      FIXED="${FIXED//\"/}"
      NEWLEN=${#FIXED}

      # WHAT:
      #   Check new token and overwrite the file securely
      # WHY:
      #   Patch must not allow empty or weak tokens
      # UX:
      #   Confirm overwrite with PASS or FAIL
      if (( NEWLEN >= MIN_TOKEN_LEN )) && [[ "$FIXED" =~ $VALID_TOKEN_REGEX ]]; then
        echo "GH_TOKEN=\"$FIXED\"" > "$FILE"
        chmod 600 "$FILE"
        echo "# [PASS] $FILE successfully updated (len=$NEWLEN)"
        PATCHED=true
        break
      else
        echo "# [FAIL] Token does not meet criteria (len=$NEWLEN)"
        exit 2
      fi
    else
      echo "# [PASS] Valid GH_TOKEN found in $FILE (len=$LENGTH)"
      PATCHED=true
      break
    fi
  fi
done

# Final fallback if no files found
if ! $PATCHED; then
  echo "# [FAIL] No valid .env or .env.local file found or patched"
  exit 3
fi
