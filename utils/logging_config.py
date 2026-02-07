import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
import os


def setup_sensor_logging(
    log_file: Optional[str] = None,
    json_log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    log_level: int = logging.INFO,
    enable_json: bool = True
) -> logging.Logger:
    """
    センサーデータ収集用のロギングを設定
    
    Args:
        log_file: ログファイルのパス（Noneの場合は環境変数または自動検出）
        json_log_file: JSONログファイルのパス（Noneの場合は自動設定）
        max_bytes: ログファイルの最大サイズ（デフォルト: 10MB）
        backup_count: 保持するバックアップ数（デフォルト: 5）
        log_level: ログレベル（デフォルト: INFO）
        enable_json: JSON形式のログも出力するか（デフォルト: True）
    
    Returns:
        logging.Logger: 設定済みロガー
    """
    logger = logging.getLogger('sensor_monitor')
    logger.setLevel(log_level)
    
    # 既存のハンドラーをクリア
    logger.handlers.clear()
    
    # ログファイルパスの決定
    if log_file is None:
        # 環境変数から取得、なければカレントディレクトリベース
        log_file = os.getenv('SENSOR_LOG_FILE')
        if log_file is None:
            # カレントディレクトリまたはスクリプトのディレクトリから相対パスで設定
            base_dir = Path.cwd()
            log_file = str(base_dir / 'logs' / 'sensor.log')
    
    # JSONログファイルパスの決定
    if json_log_file is None and enable_json:
        json_log_file = os.getenv('SENSOR_JSON_LOG_FILE')
        if json_log_file is None:
            # 通常のログファイルと同じディレクトリに .json 拡張子で作成
            log_path = Path(log_file)
            json_log_file = str(log_path.parent / f"{log_path.stem}.json")
    
    # ログディレクトリを作成
    log_path = Path(log_file).expanduser()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # フォーマッター
    log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # ファイルハンドラー（ローテーション対応）- 通常ログ
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(log_level)
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    console_handler.setLevel(log_level)
    
    # ハンドラーを追加
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # JSON用のロガーを別途作成
    if enable_json and json_log_file:
        json_logger = logging.getLogger('sensor_monitor_json')
        json_logger.setLevel(log_level)
        json_logger.handlers.clear()
        json_logger.propagate = False  # 親ロガーに伝播しない
        
        json_handler = RotatingFileHandler(
            Path(json_log_file).expanduser(),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        # JSONログにはフォーマッターを使わず、生のメッセージを出力
        json_handler.setFormatter(logging.Formatter('%(message)s'))
        json_handler.setLevel(log_level)
        json_logger.addHandler(json_handler)
    
    return logger


def setup_upload_logging(
    log_file: Optional[str] = None,
    max_bytes: int = 5 * 1024 * 1024,  # 5MB
    backup_count: int = 5,
    log_level: int = logging.INFO
) -> logging.Logger:
    """
    アップロード処理用のロギングを設定
    
    Args:
        log_file: ログファイルのパス（Noneの場合は環境変数または自動検出）
        max_bytes: ログファイルの最大サイズ（デフォルト: 5MB）
        backup_count: 保持するバックアップ数（デフォルト: 5）
        log_level: ログレベル（デフォルト: INFO）
    
    Returns:
        logging.Logger: 設定済みロガー
    """
    logger = logging.getLogger('sensor_upload')
    logger.setLevel(log_level)
    
    # 既存のハンドラーをクリア
    logger.handlers.clear()
    
    # ログファイルパスの決定
    if log_file is None:
        # 環境変数から取得、なければカレントディレクトリベース
        log_file = os.getenv('UPLOAD_LOG_FILE')
        if log_file is None:
            base_dir = Path.cwd()
            log_file = str(base_dir / 'logs' / 'upload.log')
    
    # ログディレクトリを作成
    log_path = Path(log_file).expanduser()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # フォーマッター
    log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # ファイルハンドラー（ローテーション対応）
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(log_level)
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    console_handler.setLevel(log_level)
    
    # ハンドラーを追加
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
