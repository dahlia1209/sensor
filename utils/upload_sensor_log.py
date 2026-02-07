import os
import sys
import shutil
from typing import Optional
from datetime import datetime
from azure.storage.blob import BlobServiceClient, ContentSettings
from pathlib import Path
import json

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import setup_upload_logging


logger = setup_upload_logging()


class BlobConnectionManager:
    """Azure Blob Storage接続マネージャー（シングルトン）"""
    
    _instance: Optional['BlobConnectionManager'] = None
    client: Optional['BlobServiceClient'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
            if not connection_string:
                raise ValueError("AZURE_STORAGE_CONNECTION_STRING environment variable is not set")
            cls.client = BlobServiceClient.from_connection_string(connection_string)
        return cls._instance


def upload_sensor_log_append(
    log_file_path: Optional[str] = None,
    container_name: Optional[str] = None,
    blob_name: Optional[str] = None,
    use_copy: bool = True,
    track_position: bool = True
) -> bool:
    """
    センサーログをAppend Blobとして追記アップロード
    
    Args:
        log_file_path: アップロードするログファイルのパス（Noneの場合は環境変数または自動検出）
        container_name: Azureのコンテナ名
        blob_name: Blob名
        use_copy: 一時コピーを作成してアップロード
        track_position: 前回アップロード位置を記録（差分のみアップロード）
    
    Returns:
        bool: アップロード成功時True
    """
    temp_file = None
    position_file = None
    
    try:
        # ログファイルパスの決定
        if log_file_path is None:
            log_file_path = os.getenv('SENSOR_LOG_FILE')
            if log_file_path is None:
                base_dir = Path.cwd()
                log_file_path = str(base_dir / 'logs' / 'sensor.log')
        
        log_path = Path(log_file_path).expanduser()
        
        if not log_path.exists():
            logger.error(f"ログファイルが見つかりません: {log_path}")
            return False
        
        # 前回アップロード位置を記録するファイル
        if track_position:
            position_file = log_path.parent / f".{log_path.name}.position"
            last_position = 0
            last_timestamp = None
            
            if position_file.exists():
                try:
                    with open(position_file, 'r') as f:
                        data = json.load(f)
                        last_position = data.get('last_position', 0)
                        last_timestamp = data.get('last_timestamp')
                except json.JSONDecodeError as e:
                    logger.warning(f"JSONの解析に失敗: {e}")
                    last_position = 0
                    last_timestamp = None
                except Exception as e:
                    logger.warning(f"位置ファイルの読み込みに失敗: {e}")
                    last_position = 0
                    last_timestamp = None
        else:
            last_position = 0
            last_timestamp = None
        
        # ファイルロック回避のため一時コピーを作成
        if use_copy:
            temp_file = log_path.with_suffix('.tmp')
            shutil.copy2(log_path, temp_file)
            upload_path = temp_file
        else:
            upload_path = log_path
        
        # 差分データを読み込み
        file_size = upload_path.stat().st_size
        current_mtime = int(upload_path.stat().st_mtime)
        
        # ファイルサイズとタイムスタンプのチェック
        if file_size < last_position:
            if last_timestamp is None or current_mtime > last_timestamp:
                logger.info("ログローテーションを検知しました。最初から読み込みます")
                last_position = 0
            else:
                logger.warning("ファイルサイズが縮小していますが、タイムスタンプが古いため処理をスキップします")
                return True
        elif file_size == last_position:
            logger.info("新しいログデータがありません")
            return True
        
        # 差分データの読み取り
        with open(upload_path, 'rb') as file:
            file.seek(last_position)
            new_content = file.read()
        
        new_data_size = len(new_content)
        
        # ファイルサイズチェック（Azure Append Blobの制限）
        max_append_size = 4 * 1024 * 1024  # 4MB per append operation
        if new_data_size > max_append_size:
            logger.warning(
                f"1回の追記サイズが大きいです: {new_data_size:,} bytes "
                f"(上限: {max_append_size:,} bytes)"
            )
        
        # BlobConnectionManagerのインスタンスを取得
        manager = BlobConnectionManager()
        
        # コンテナ名とBlob名の設定
        container = container_name or os.getenv("AZURE_BLOB_CONTAINER_NAME", "sensor-logs")
        blob = blob_name or os.getenv("AZURE_BLOB_NAME", "sensor-data/sensor.log")
        
        # Append Blob クライアントを取得
        blob_client = manager.client.get_blob_client(
            container=container,
            blob=blob
        )
        
        # Append Blobが存在しない場合は作成
        try:
            blob_client.get_blob_properties()
            logger.info(f"既存のAppend Blobに追記: {container}/{blob}")
        except Exception:
            logger.info(f"新規Append Blobを作成: {container}/{blob}")
            blob_client.create_append_blob(
                content_settings=ContentSettings(content_type='text/plain; charset=utf-8')
            )
        
        # データを追記
        logger.info(f"追記開始: {new_data_size:,} bytes (位置: {last_position} -> {file_size})")
        blob_client.append_block(new_content)
        
        # 位置を記録
        if track_position and position_file:
            try:
                mtime = int(log_path.stat().st_mtime)
                with open(position_file, 'w') as f:
                    data = {
                        'last_position': file_size,
                        'last_timestamp': mtime,
                        'uploaded_at': datetime.now().isoformat()
                    }
                    json.dump(data, f, indent=4)
            except Exception as e:
                logger.error(f"位置ファイルの保存に失敗: {e}")
        
        logger.info(f"追記完了: {new_data_size:,} bytes")
        logger.info(f"タイムスタンプ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        logger.error(f"アップロードエラー: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
        
    finally:
        # 一時ファイルのクリーンアップ
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
            except Exception as e:
                logger.warning(f"一時ファイルの削除に失敗: {e}")


if __name__ == '__main__':
    # 環境変数の確認
    from dotenv import load_dotenv
    load_dotenv()
    
    required_env_vars = ["AZURE_STORAGE_CONNECTION_STRING"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error("以下の環境変数が設定されていません:")
        for var in missing_vars:
            logger.error(f"  - {var}")
        exit(1)
    
    # ログファイルパスを取得（環境変数 or デフォルト）
    log_file = os.getenv("SENSOR_LOG_FILE")
    if log_file is None:
        log_file = str(Path.cwd() / 'logs' / 'sensor.log')
    
    logger.info("=== センサーログアップロード実行 ===")
    success = upload_sensor_log_append(log_file, track_position=True)
    
    if success:
        logger.info("アップロード成功")
    else:
        logger.error("アップロード失敗")
    
    exit(0 if success else 1)

