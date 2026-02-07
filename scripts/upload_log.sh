#!/bin/bash

# エラー時に停止
set -e

# スクリプトのディレクトリを取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# 作業ディレクトリに移動
cd "$PROJECT_DIR"

# 仮想環境を有効化
source .venv/bin/activate

# 環境変数を読み込み
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Pythonスクリプトを実行
python3 "$PROJECT_DIR/utils/upload_sensor_log.py"

# 実行結果を記録
echo "Upload completed at $(date)" >> "$PROJECT_DIR/logs/upload_success.log"
