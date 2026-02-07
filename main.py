import os
import time
import signal
import sys
import logging
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

from services.sensor import SensorService
from models.sensor import SensorStatistics
from utils.logging_config import setup_sensor_logging


# 環境変数を読み込み
load_dotenv()

# ロガーの設定
logger = setup_sensor_logging()


class SensorMonitor:
    """センサーデータ収集・監視システム"""
    
    def __init__(
        self,
        gpio_pin: int = 4,
        interval: int = 60,
        log_interval: int = 10
    ):
        """
        Args:
            gpio_pin: GPIOピン番号
            interval: センサー読み取り間隔（秒）
            log_interval: 統計情報ログ出力間隔（読み取り回数）
        """
        self.gpio_pin = gpio_pin
        self.interval = interval
        self.log_interval = log_interval
        
        self.sensor_service: Optional[SensorService] = None
        self.statistics = SensorStatistics()
        self.running = False
        
        # シグナルハンドラーの設定
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """シグナル受信時の処理"""
        logger.info(f"シグナル {signum} を受信しました。停止処理を開始...")
        self.stop()
    
    def start(self):
        """監視を開始"""
        logger.info("=" * 70)
        logger.info("センサー監視システム起動")
        logger.info("=" * 70)
        logger.info(f"GPIO ピン:         {self.gpio_pin}")
        logger.info(f"読み取り間隔:      {self.interval}秒")
        logger.info(f"統計ログ間隔:      {self.log_interval}回ごと")
        logger.info("=" * 70)
        
        try:
            # センサーサービスの初期化
            logger.info("センサーを初期化中...")
            self.sensor_service = SensorService(gpio_pin=self.gpio_pin)
            logger.info("センサー初期化完了")
            
            # JSONロガーを取得
            json_logger = logging.getLogger('sensor_monitor_json')
            
            self.running = True
            reading_count = 0
            
            while self.running:
                try:
                    # センサー読み取り
                    reading = self.sensor_service.read_sensor()
                    
                    # 通常ログに記録
                    logger.info(reading.to_log_string())
                    
                    # JSONログに記録
                    if json_logger.handlers:
                        json_logger.info(reading.to_json_string())
                    
                    # 統計を更新
                    self.statistics.update_with_reading(reading)
                    reading_count += 1
                    
                    # 定期的に統計情報を出力
                    if reading_count % self.log_interval == 0:
                        logger.info("\n" + self.statistics.to_summary_string())
                    
                    # 次の読み取りまで待機
                    if self.running:
                        time.sleep(self.interval)
                
                except Exception as e:
                    logger.error(f"読み取り中にエラーが発生: {type(e).__name__}: {e}")
                    if self.running:
                        logger.info(f"{self.interval}秒後にリトライします...")
                        time.sleep(self.interval)
        
        except KeyboardInterrupt:
            logger.info("キーボード割り込みを検知しました")
        
        except Exception as e:
            logger.error(f"致命的エラー: {type(e).__name__}: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        finally:
            self.cleanup()
    
    def stop(self):
        """監視を停止"""
        self.running = False
        logger.info("停止処理中...")
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        logger.info("\n" + "=" * 70)
        logger.info("センサー監視システム停止")
        logger.info("=" * 70)
        
        # 最終統計を出力
        if self.statistics.total_readings > 0:
            logger.info("\n" + self.statistics.to_summary_string())
        
        # センサーサービスのクリーンアップ
        if self.sensor_service:
            try:
                self.sensor_service.cleanup()
                logger.info("センサーリソースをクリーンアップしました")
            except Exception as e:
                logger.error(f"クリーンアップエラー: {e}")
        
        logger.info("=" * 70)
        logger.info(f"終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 70)


def main():
    """メイン関数"""
    # 環境変数から設定を取得
    gpio_pin = int(os.getenv("SENSOR_GPIO", "4"))
    interval = int(os.getenv("SENSOR_INTERVAL", "60"))
    log_interval = int(os.getenv("SENSOR_LOG_INTERVAL", "10"))
    
    # センサー監視システムを起動
    monitor = SensorMonitor(
        gpio_pin=gpio_pin,
        interval=interval,
        log_interval=log_interval
    )
    
    try:
        monitor.start()
    except Exception as e:
        logger.error(f"起動エラー: {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

