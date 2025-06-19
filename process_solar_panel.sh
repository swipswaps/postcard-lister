#!/bin/bash
################################################################################
# FILE: process_solar_panel.sh
# DESC: Simple wrapper for solar panel processing with verbatim capture
# USAGE: ./process_solar_panel.sh solar_panel.jpg
################################################################################

set -euo pipefail

# Check if input file provided
if [ $# -eq 0 ]; then
    echo "🌞 SOLAR PANEL PROCESSOR - SIMPLE WRAPPER"
    echo "Usage: $0 <solar_panel_image>"
    echo "Example: $0 solar_panel.jpg"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_DIR="${2:-catalog/}"
LOG_FILE="solar_panel_$(date +%Y%m%d_%H%M%S).log"

echo "🔧 SOLAR PANEL PROCESSING WITH VERBATIM CAPTURE"
echo "📅 Started: $(date)"
echo "📁 Input: $INPUT_FILE"
echo "📂 Output: $OUTPUT_DIR"
echo "📝 Log: $LOG_FILE"
echo "=" * 60

# Run with verbatim capture and logging
python3 cli/main.py \
    --input "$INPUT_FILE" \
    --output "$OUTPUT_DIR" \
    --verbose \
    --github-upload \
    2>&1 | tee "$LOG_FILE"

echo "=" * 60
echo "✅ Processing complete! Log saved to: $LOG_FILE"
