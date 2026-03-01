import os
import sys
from datetime import datetime
from azure.storage.blob import BlobServiceClient, ContentSettings
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import setup_upload_logging

logger = setup_upload_logging()


def upload_index_html(
    html_path: str | None = None,
    container_name: str | None = None,
) -> bool:
    """
    index.html を Block Blob として上書きアップロードする

    Args:
        html_path: index.htmlのパス（Noneの場合は html/index.html を使用）
        container_name: Azureコンテナ名（Noneの場合は環境変数 AZURE_BLOB_CONTAINER_NAME）

    Returns:
        bool: 成功時True
    """
    if html_path is None:
        html_path = str(Path.cwd() / "html" / "index.html")

    path = Path(html_path).expanduser()
    if not path.exists():
        logger.error(f"ファイルが見つかりません: {path}")
        return False

    container = container_name or os.getenv("AZURE_BLOB_CONTAINER_NAME", "sensor-logs")

    try:
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not connection_string:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING が設定されていません")

        client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = client.get_blob_client(container=container, blob="sensor-data/index.html")

        file_size = path.stat().st_size
        logger.info(f"アップロード開始: {path} → {container}/sensor-data/index.html ({file_size:,} bytes)")

        with open(path, "rb") as f:
            blob_client.upload_blob(
                f,
                overwrite=True,
                content_settings=ContentSettings(content_type="text/html; charset=utf-8"),
            )

        logger.info(f"アップロード完了: {container}/sensor-data/index.html")
        logger.info(f"タイムスタンプ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return True

    except Exception as e:
        logger.error(f"アップロードエラー: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    if not os.getenv("AZURE_STORAGE_CONNECTION_STRING"):
        logger.error("環境変数が設定されていません: AZURE_STORAGE_CONNECTION_STRING")
        sys.exit(1)

    logger.info("=== index.html アップロード開始 ===")
    success = upload_index_html()
    logger.info("アップロード成功" if success else "アップロード失敗")
    sys.exit(0 if success else 1)
