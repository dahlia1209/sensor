import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import time
import board
import adafruit_dht
from typing import Optional
from models.sensor import SensorReading
from datetime import datetime


class SensorService:
    """AM2302/DHT22センサー読み取りサービス"""
    
    def __init__(self, gpio_pin: int = 4, use_pulseio: bool = False, retry_count: int = 3, retry_delay: float = 0.5):
        """
        Args:
            gpio_pin: GPIOピン番号（デフォルト: 4）
            use_pulseio: pulseioを使用するか（デフォルト: False）
            retry_count: リトライ回数（デフォルト: 3）
            retry_delay: リトライ間隔（秒、デフォルト: 0.5）
        """
        self.gpio_pin = gpio_pin
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        
        # GPIOピン番号からboardのピンを取得
        self.board_pin = self._get_board_pin(gpio_pin)
        
        # センサーデバイスの初期化
        self.device = adafruit_dht.DHT22(self.board_pin, use_pulseio=use_pulseio)
        
        # 初期化後の待機
        time.sleep(2)
    
    def _get_board_pin(self, gpio_num: int):
        """GPIO番号からboardのピンオブジェクトを取得"""
        pin_map = {
            4: board.D4,
            17: board.D17,
            27: board.D27,
            22: board.D22,
            23: board.D23,
            24: board.D24,
            25: board.D25,
            # 必要に応じて追加
        }
        
        if gpio_num not in pin_map:
            raise ValueError(f"GPIO{gpio_num}はサポートされていません。サポートされているピン: {list(pin_map.keys())}")
        
        return pin_map[gpio_num]
    
    def read_sensor(self) -> SensorReading:
        """
        センサーから温湿度を読み取る（リトライ機能付き）
        
        Returns:
            SensorReading: 読み取り結果
        """
        for attempt in range(self.retry_count):
            try:
                temperature = self.device.temperature
                humidity = self.device.humidity
                
                # 値の妥当性チェック
                if temperature is not None and humidity is not None:
                    if -40 <= temperature <= 80 and 0 <= humidity <= 100:
                        return SensorReading(
                            timestamp=datetime.now(),
                            temperature=temperature,
                            humidity=humidity,
                            gpio_pin=self.gpio_pin,
                            success=True
                        )
                    else:
                        error_msg = f"異常値検出 (T:{temperature}°C, H:{humidity}%)"
                        if attempt < self.retry_count - 1:
                            time.sleep(self.retry_delay)
                            continue
                        else:
                            return SensorReading(
                                timestamp=datetime.now(),
                                temperature=0.0,
                                humidity=0.0,
                                gpio_pin=self.gpio_pin,
                                success=False,
                                error_message=error_msg
                            )
                else:
                    error_msg = f"None値取得 (T:{temperature}, H:{humidity})"
                    if attempt < self.retry_count - 1:
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        return SensorReading(
                            timestamp=datetime.now(),
                            temperature=0.0,
                            humidity=0.0,
                            gpio_pin=self.gpio_pin,
                            success=False,
                            error_message=error_msg
                        )
            
            except RuntimeError as e:
                error_msg = f"RuntimeError: {str(e)}"
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    return SensorReading(
                        timestamp=datetime.now(),
                        temperature=0.0,
                        humidity=0.0,
                        gpio_pin=self.gpio_pin,
                        success=False,
                        error_message=error_msg
                    )
            
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                return SensorReading(
                    timestamp=datetime.now(),
                    temperature=0.0,
                    humidity=0.0,
                    gpio_pin=self.gpio_pin,
                    success=False,
                    error_message=error_msg
                )
        
        # 全リトライ失敗
        return SensorReading(
            timestamp=datetime.now(),
            temperature=0.0,
            humidity=0.0,
            gpio_pin=self.gpio_pin,
            success=False,
            error_message=f"全{self.retry_count}回のリトライ失敗"
        )
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        try:
            self.device.exit()
        except Exception as e:
            print(f"クリーンアップエラー: {e}")


def test_sensor_reading(gpio_pin: int = 4, count: int = 5):
    """センサー読み取りのテスト"""
    print("=" * 70)
    print("AM2302センサー読み取りテスト")
    print("=" * 70)
    print(f"GPIO: {gpio_pin}")
    print(f"読み取り回数: {count}")
    print("=" * 70)
    
    service = SensorService(gpio_pin=gpio_pin)
    
    success_count = 0
    for i in range(count):
        print(f"\n[{i+1}/{count}] ", end="", flush=True)
        reading = service.read_sensor()
        print(reading.to_log_string())
        
        if reading.success:
            success_count += 1
        
        if i < count - 1:
            time.sleep(3)
    
    service.cleanup()
    
    print("\n" + "=" * 70)
    print(f"結果: {success_count}/{count}回成功 ({(success_count/count)*100:.1f}%)")
    print("=" * 70)


if __name__ == "__main__":
    # テスト実行
    test_sensor_reading(gpio_pin=4, count=5)
