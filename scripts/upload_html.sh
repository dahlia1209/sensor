#!/bin/bash
# index.html を Azure Blob Storage (sensor-logs コンテナ) にアップロードする
#
# 使用方法:
#   ./scripts/upload_html.sh

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_DIR"
source .venv/bin/activate

if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

echo "=== $(date) ===" >> "$PROJECT_DIR/logs/upload_html.log"

python3 "$PROJECT_DIR/utils/upload_html.py" 2>&1 | tee -a "$PROJECT_DIR/logs/upload_html.log"

echo "Done: $(date)" >> "$PROJECT_DIR/logs/upload_html.log"
