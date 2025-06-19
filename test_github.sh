#!/bin/bash
################################################################################
# FILE: test_github.sh
# DESC: Simple wrapper for GitHub authentication testing with verbatim capture
# USAGE: ./test_github.sh
################################################################################

set -euo pipefail

GITHUB_TOKEN="your_github_token_here"
LOG_FILE="github_test_$(date +%Y%m%d_%H%M%S).log"

echo "🔧 GITHUB AUTHENTICATION TEST WITH VERBATIM CAPTURE"
echo "📅 Started: $(date)"
echo "📝 Log: $LOG_FILE"
echo "=" * 60

# Run GitHub authentication test with verbatim capture
python3 debug_github_auth.py "$GITHUB_TOKEN" 2>&1 | tee "$LOG_FILE"

echo "=" * 60
echo "✅ GitHub test complete! Log saved to: $LOG_FILE"
