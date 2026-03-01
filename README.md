# センサーデータ収集システム

AM2302/DHT22温湿度センサーからデータを収集し、Azure Blob Storageに定期的にアップロードするシステムです。

## 機能

- 温湿度データの定期収集（デフォルト: 60秒間隔）
- ローカルログへの記録（ローテーション対応）
  - **人間が読みやすいテキスト形式** (`sensor.log`)
  - **機械処理しやすいJSON形式** (`sensor.json`)
- 統計情報の自動計算と定期出力
- Azure Blob Storage への差分アップロード（15分ごと）
- ダッシュボード用 `index.html` のアップロード
- systemdサービスによる自動起動・常時稼働
- エラーハンドリングとリトライ機能

## ハードウェア要件

- Raspberry Pi Zero 2 W（または他のRaspberry Piモデル）
- AM2302 (DHT22) 温湿度センサー
- 5V 2A電源

### ハードウェア接続

AM2302センサーの配線:
- **VCC** → ラズパイの **5V** (物理ピン2 または 4)
- **DATA** → ラズパイの **GPIO4** (物理ピン7)
- **GND** → ラズパイの **GND** (物理ピン6, 9, 14, 20など)

```
ラズパイピン配置:
   3.3V  [ 1] [ 2]  5V      ← VCC接続
  GPIO2  [ 3] [ 4]  5V
  GPIO3  [ 5] [ 6]  GND     ← GND接続
  GPIO4  [ 7] [ 8]  GPIO14  ← DATA接続
    GND  [ 9] [10]  GPIO15
```

## セットアップ

### 1. 仮想環境の作成

```bash
cd ~/src/sensor
python3 -m venv .venv
source .venv/bin/activate
```

### 2. パッケージのインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

`.env.example` をコピーして `.env` を作成し、必要な値を設定します。

```bash
cp .env.example .env
nano .env
```

**必須の環境変数:**
- `AZURE_STORAGE_CONNECTION_STRING`: Azure Storage接続文字列

**オプションの環境変数:**
- `AZURE_BLOB_CONTAINER_NAME`: コンテナ名（デフォルト: sensor-logs）
- `AZURE_BLOB_NAME`: Blob名（デフォルト: sensor-data/sensor.log）
- `SENSOR_INTERVAL`: センサー読み取り間隔（秒、デフォルト: 60）
- `SENSOR_GPIO`: GPIOピン番号（デフォルト: 4）
- `SENSOR_LOG_INTERVAL`: 統計ログ出力間隔（回数、デフォルト: 10）
- `SENSOR_LOG_FILE`: センサーログのパス（デフォルト: ./logs/sensor.log）
- `SENSOR_JSON_LOG_FILE`: JSONログのパス（デフォルト: ./logs/sensor.json）
- `UPLOAD_LOG_FILE`: アップロードログのパス（デフォルト: ./logs/upload.log）

**注意**: ログファイルのパスを指定しない場合、プロジェクトディレクトリ（カレントディレクトリ）の `logs/` 配下に自動作成されます。

### 4. Azure Storage の準備

Azure Portalで以下を作成：
1. ストレージアカウント
2. コンテナ（例: `sensor-logs`）
3. 接続文字列を取得して `.env` に設定

## 使用方法

### センサー読み取りテスト

```bash
source .venv/bin/activate
python3 services/sensor.py
```

### メイン監視プログラムの実行（手動）

```bash
source .venv/bin/activate
python3 main.py
```

### systemdサービスとして実行（推奨）

#### サービスファイルの作成

```bash
sudo nano /etc/systemd/system/sensor-monitor.service
```

以下を貼り付け（**ユーザー名とパスを自分の環境に合わせて変更**）:

```ini
[Unit]
Description=Temperature and Humidity Sensor Monitor
After=network.target

[Service]
Type=simple
User=dahlia1209
WorkingDirectory=/home/dahlia1209/src/sensor
Environment="PATH=/home/dahlia1209/src/sensor/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/dahlia1209/src/sensor/.venv/bin/python3 /home/dahlia1209/src/sensor/main.py
Restart=always
RestartSec=10
StandardOutput=append:/home/dahlia1209/src/sensor/logs/service.log
StandardError=append:/home/dahlia1209/src/sensor/logs/service.log

[Install]
WantedBy=multi-user.target
```

> ⚠️ **注意**: サービスは必ず `sudo systemctl` 経由で操作してください。`sudo python3 main.py` のように直接実行すると `service.log` が root 所有になり、次回サービス起動時に `sensor.json` への書き込みが失敗する原因になります。

#### サービスの有効化と起動

```bash
# systemdをリロード
sudo systemctl daemon-reload

# サービスを有効化（再起動後も自動起動）
sudo systemctl enable sensor-monitor

# サービスを開始
sudo systemctl start sensor-monitor

# 状態確認
sudo systemctl status sensor-monitor
```

#### サービス管理コマンド

```bash
# 状態確認
sudo systemctl status sensor-monitor

# 停止
sudo systemctl stop sensor-monitor

# 開始
sudo systemctl start sensor-monitor

# 再起動
sudo systemctl restart sensor-monitor

# 自動起動を無効化
sudo systemctl disable sensor-monitor

# 自動起動を有効化
sudo systemctl enable sensor-monitor
```

### ログの確認

```bash
# テキストログをリアルタイム表示
tail -f ~/src/sensor/logs/sensor.log

# JSONログをリアルタイム表示
tail -f ~/src/sensor/logs/sensor.json

# systemdのログを表示
sudo journalctl -u sensor-monitor -f

# 最新100行を表示
tail -n 100 ~/src/sensor/logs/sensor.log

# サービスログ
tail -f ~/src/sensor/logs/service.log
```

## 定期アップロード設定

### 手動アップロード（センサーログ）

```bash
source .venv/bin/activate
/home/dahlia1209/src/sensor/scripts/upload_all_logs.sh
```

### cronで15分ごとに自動アップロード

#### 1. スクリプトに実行権限を付与

```bash
chmod +x /home/dahlia1209/src/sensor/scripts/upload_all_logs.sh
```

#### 2. crontabを編集

```bash
crontab -e
```

#### 3. 以下の行を追加（パスは自分の環境に合わせて変更）

```cron
*/15 * * * * /home/dahlia1209/src/sensor/scripts/upload_all_logs.sh
```

#### 4. 設定を確認

```bash
crontab -l
```

#### 5. アップロードログの確認

```bash
tail -f ~/src/sensor/logs/upload_all.log
```

## ダッシュボード (index.html) のアップロード

`html/index.html` を `sensor-logs` コンテナのルートに Block Blob としてアップロードします。センサーデータ (`sensor.json`) とは独立したスクリプトで管理します。

### 初回セットアップ

```bash
chmod +x /home/dahlia1209/src/sensor/scripts/upload_html.sh
```

### 手動アップロード

```bash
./scripts/upload_html.sh
```

### アップロードログの確認

```bash
tail -f ~/src/sensor/logs/upload_html.log
```

## プロジェクト構造

```
sensor/
├── .env                       # 環境変数（要作成）
├── .env.example               # 環境変数サンプル
├── .gitignore                 # Git除外設定
├── README.md                  # このファイル
├── requirements.txt           # 依存パッケージ
├── main.py                    # メインプログラム
├── html/
│   └── index.html            # ダッシュボード画面
├── models/
│   ├── __init__.py
│   └── sensor.py             # データモデル
├── services/
│   ├── __init__.py
│   └── sensor.py             # センサー読み取りサービス
├── utils/
│   ├── __init__.py
│   ├── logging_config.py     # ロギング設定
│   ├── upload_sensor_log.py  # センサーログのBLOBアップロード
│   └── upload_html.py        # index.htmlのBLOBアップロード
├── scripts/
│   ├── upload_all_logs.sh    # センサーログ一括アップロードスクリプト
│   └── upload_html.sh        # index.htmlアップロードスクリプト
└── logs/
    ├── .gitkeep
    ├── sensor.log            # センサーログ（テキスト形式、自動生成）
    ├── sensor.json           # センサーログ（JSON形式、自動生成）
    ├── service.log           # systemdサービスログ（自動生成）
    ├── upload.log            # アップロードログ（自動生成）
    ├── upload_all.log        # 一括アップロードログ（自動生成）
    ├── upload_html.log       # HTMLアップロードログ（自動生成）
    └── .sensor.log.position  # アップロード位置記録（自動生成）
```

## データフォーマット

### センサーログの例（テキスト形式: sensor.log）

```
2026-02-07 10:30:00 - INFO - 2026-02-07 10:30:00 | SUCCESS | Temperature: 23.5°C | Humidity: 45.2% | GPIO: 4
2026-02-07 10:31:00 - INFO - 2026-02-07 10:31:00 | SUCCESS | Temperature: 23.6°C | Humidity: 45.1% | GPIO: 4
2026-02-07 10:32:00 - INFO - 2026-02-07 10:32:00 | FAILURE | Error: RuntimeError: Checksum did not validate | GPIO: 4
```

### センサーログの例（JSON形式: sensor.json）

```json
{"timestamp": "2026-02-07T10:30:00.123456", "temperature": 23.5, "humidity": 45.2, "gpio_pin": 4, "success": true, "error_message": null}
{"timestamp": "2026-02-07T10:31:00.234567", "temperature": 23.6, "humidity": 45.1, "gpio_pin": 4, "success": true, "error_message": null}
{"timestamp": "2026-02-07T10:32:00.345678", "temperature": null, "humidity": null, "gpio_pin": 4, "success": false, "error_message": "RuntimeError: Checksum did not validate"}
```

各行が1つのJSONオブジェクトです（JSONL形式）。Python、jq、各種データ分析ツールで簡単に処理できます。

### 統計サマリーの例

10回の読み取りごとに以下のような統計が出力されます：

```
======================================================================
センサー統計サマリー
======================================================================
総読み取り回数:    100
成功回数:          95
失敗回数:          5
成功率:            95.0%

平均温度:          23.7°C
温度範囲:          22.1°C ~ 25.3°C
平均湿度:          44.8%
湿度範囲:          40.2% ~ 49.5%

開始時刻:          2026-02-07 10:00:00
最終更新:          2026-02-07 11:40:00
稼働時間:          1:40:00
======================================================================
```

## システム全体の動作

完成したシステムの動作フロー：

1. **センサー監視**: systemdで常時稼働（60秒間隔で読み取り）
2. **ログ記録**:
   - テキスト形式 → `sensor.log`（人間が読む用）
   - JSON形式 → `sensor.json`（プログラム処理用）
   - 10MBごとに自動ローテーション
3. **統計出力**: 10回ごとに統計サマリー表示
4. **Azure同期**: 15分ごとに差分アップロード（cronで自動実行）
5. **ダッシュボード**: `index.html` を手動アップロード、`sensor.json` を参照して可視化
6. **自動起動**: Raspberry Pi再起動後も自動で開始

## システムステータス確認

```bash
# サービス状態
sudo systemctl status sensor-monitor

# 最新のセンサーデータ
tail -n 5 ~/src/sensor/logs/sensor.log

# JSON最新データ
tail -n 1 ~/src/sensor/logs/sensor.json | jq '.'

# cron設定
crontab -l

# ログファイル一覧
ls -lh ~/src/sensor/logs/

# ログファイルの所有者確認（root所有になっていないか）
ls -l ~/src/sensor/logs/service.log
```

## トラブルシューティング

### sensor.json が更新されない

`service.log` が root 所有になっていると、`sensor.json` への書き込みに失敗することがあります。

```bash
# 所有者を確認
ls -l ~/src/sensor/logs/service.log

# root所有の場合は修正して再起動
sudo chown dahlia1209:dahlia1209 ~/src/sensor/logs/service.log
sudo systemctl restart sensor-monitor
```

### cronが動いているか確認

```bash
# cronサービスの状態
sudo systemctl status cron

# cronの実行履歴
sudo journalctl -u cron | tail -20

# アップロードログで実行結果を確認
tail -f ~/src/sensor/logs/upload_all.log
```

## パフォーマンス

**Raspberry Pi Zero 2 W での動作:**
- CPU使用率: ほぼ0%（待機時）
- メモリ使用量: 約65-100MB
- 消費電力: 約1.2W（通常動作時）
- 完全に24時間稼働可能

## 参考

- このプロジェクトは blockchain-project の構造を参考に作成されています
- センサー: AM2302 (DHT22)
- ライブラリ: adafruit-circuitpython-dht
- クラウド: Azure Blob Storage (Append Blob)

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 作成者

Raspberry Pi Zero 2 W + AM2302センサーによる温湿度監視システム
