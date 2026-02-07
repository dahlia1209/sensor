#!/bin/bash
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

echo "=== $(date) ===" >> "$PROJECT_DIR/logs/upload_all.log"

# テキストログをアップロード
echo "Uploading sensor.log..." >> "$PROJECT_DIR/logs/upload_all.log"
python3 "$PROJECT_DIR/utils/upload_sensor_log.py" 2>&1 | tee -a "$PROJECT_DIR/logs/upload_all.log"

# JSONログをアップロード
echo "Uploading sensor.json..." >> "$PROJECT_DIR/logs/upload_all.log"
SENSOR_LOG_FILE="$PROJECT_DIR/logs/sensor.json" \
AZURE_BLOB_NAME="sensor-data/sensor.json" \
python3 "$PROJECT_DIR/utils/upload_sensor_log.py" 2>&1 | tee -a "$PROJECT_DIR/logs/upload_all.log"

echo "Upload completed at $(date)" >> "$PROJECT_DIR/logs/upload_all.log"
