from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class SensorReading(BaseModel):
    """温湿度センサーの読み取りデータモデル"""
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="読み取り日時"
    )
    temperature: float = Field(
        ...,
        description="温度（摂氏）"
    )
    humidity: float = Field(
        ...,
        ge=0,
        le=100,
        description="湿度（%）"
    )
    gpio_pin: int = Field(
        ...,
        description="使用したGPIOピン番号"
    )
    success: bool = Field(
        default=True,
        description="読み取り成功フラグ"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="エラーメッセージ（失敗時）"
    )
    
    def to_log_string(self) -> str:
        """ログ出力用の文字列を生成"""
        timestamp_str = self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        if self.success:
            return (
                f"{timestamp_str} | SUCCESS | "
                f"Temperature: {self.temperature:.1f}°C | "
                f"Humidity: {self.humidity:.1f}% | "
                f"GPIO: {self.gpio_pin}"
            )
        else:
            return (
                f"{timestamp_str} | FAILURE | "
                f"Error: {self.error_message} | "
                f"GPIO: {self.gpio_pin}"
            )
    
    def to_json_string(self) -> str:
        """JSON形式の文字列を生成"""
        import json
        data = {
            "timestamp": self.timestamp.isoformat(),
            "temperature": round(self.temperature, 1) if self.success else None,
            "humidity": round(self.humidity, 1) if self.success else None,
            "gpio_pin": self.gpio_pin,
            "success": self.success,
            "error_message": self.error_message
        }
        return json.dumps(data, ensure_ascii=False)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SensorStatistics(BaseModel):
    """センサー統計情報"""
    
    total_readings: int = Field(default=0, description="総読み取り回数")
    successful_readings: int = Field(default=0, description="成功回数")
    failed_readings: int = Field(default=0, description="失敗回数")
    avg_temperature: Optional[float] = Field(default=None, description="平均温度")
    avg_humidity: Optional[float] = Field(default=None, description="平均湿度")
    min_temperature: Optional[float] = Field(default=None, description="最低温度")
    max_temperature: Optional[float] = Field(default=None, description="最高温度")
    min_humidity: Optional[float] = Field(default=None, description="最低湿度")
    max_humidity: Optional[float] = Field(default=None, description="最高湿度")
    start_time: Optional[datetime] = Field(default=None, description="開始時刻")
    last_update: Optional[datetime] = Field(default=None, description="最終更新時刻")
    
    def update_with_reading(self, reading: SensorReading):
        """読み取りデータで統計を更新"""
        self.total_readings += 1
        self.last_update = reading.timestamp
        
        if self.start_time is None:
            self.start_time = reading.timestamp
        
        if reading.success:
            self.successful_readings += 1
            
            # 平均値の更新
            if self.avg_temperature is None:
                self.avg_temperature = reading.temperature
                self.avg_humidity = reading.humidity
            else:
                n = self.successful_readings
                self.avg_temperature = (self.avg_temperature * (n - 1) + reading.temperature) / n
                self.avg_humidity = (self.avg_humidity * (n - 1) + reading.humidity) / n
            
            # 最小値・最大値の更新
            if self.min_temperature is None or reading.temperature < self.min_temperature:
                self.min_temperature = reading.temperature
            if self.max_temperature is None or reading.temperature > self.max_temperature:
                self.max_temperature = reading.temperature
            if self.min_humidity is None or reading.humidity < self.min_humidity:
                self.min_humidity = reading.humidity
            if self.max_humidity is None or reading.humidity > self.max_humidity:
                self.max_humidity = reading.humidity
        else:
            self.failed_readings += 1
    
    def get_success_rate(self) -> float:
        """成功率を計算（%）"""
        if self.total_readings == 0:
            return 0.0
        return (self.successful_readings / self.total_readings) * 100
    
    def to_summary_string(self) -> str:
        """統計サマリーの文字列を生成"""
        if self.total_readings == 0:
            return "統計データなし"
        
        lines = [
            "=" * 70,
            "センサー統計サマリー",
            "=" * 70,
            f"総読み取り回数:    {self.total_readings}",
            f"成功回数:          {self.successful_readings}",
            f"失敗回数:          {self.failed_readings}",
            f"成功率:            {self.get_success_rate():.1f}%",
        ]
        
        if self.successful_readings > 0:
            lines.extend([
                "",
                f"平均温度:          {self.avg_temperature:.1f}°C",
                f"温度範囲:          {self.min_temperature:.1f}°C ~ {self.max_temperature:.1f}°C",
                f"平均湿度:          {self.avg_humidity:.1f}%",
                f"湿度範囲:          {self.min_humidity:.1f}% ~ {self.max_humidity:.1f}%",
            ])
        
        if self.start_time and self.last_update:
            duration = self.last_update - self.start_time
            lines.extend([
                "",
                f"開始時刻:          {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
                f"最終更新:          {self.last_update.strftime('%Y-%m-%d %H:%M:%S')}",
                f"稼働時間:          {duration}",
            ])
        
        lines.append("=" * 70)
        return "\n".join(lines)

