#!/bin/bash
################################################################################
# FILE: batch_process.sh
# DESC: Simple wrapper for batch solar panel processing with verbatim capture
# USAGE: ./batch_process.sh solar_inventory/
################################################################################

set -euo pipefail

# Check if input directory provided
if [ $# -eq 0 ]; then
    echo "📦 BATCH SOLAR PANEL PROCESSOR - SIMPLE WRAPPER"
    echo "Usage: $0 <solar_panel_directory> [workers]"
    echo "Example: $0 solar_inventory/ 8"
    exit 1
fi

INPUT_DIR="$1"
WORKERS="${2:-4}"
OUTPUT_DIR="${3:-catalog/}"
LOG_FILE="batch_$(date +%Y%m%d_%H%M%S).log"

echo "🔧 BATCH SOLAR PANEL PROCESSING WITH VERBATIM CAPTURE"
echo "📅 Started: $(date)"
echo "📁 Input Directory: $INPUT_DIR"
echo "📂 Output Directory: $OUTPUT_DIR"
echo "🔧 Workers: $WORKERS"
echo "📝 Log: $LOG_FILE"
echo "=" * 60

# Run with verbatim capture and logging
python3 cli/batch_processor.py \
    --input "$INPUT_DIR" \
    --output "$OUTPUT_DIR" \
    --workers "$WORKERS" \
    --verbose \
    --github-upload \
    2>&1 | tee "$LOG_FILE"

echo "=" * 60
echo "✅ Batch processing complete! Log saved to: $LOG_FILE"
