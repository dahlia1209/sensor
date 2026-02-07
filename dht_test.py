import time
import board
import adafruit_dht

print("=" * 60)
print("AM2302センサーテスト - 改善版")
print("=" * 60)

# 重要: use_pulseio=False を明示
dhtDevice = adafruit_dht.DHT22(board.D4, use_pulseio=False)

print("\n初期化完了。5秒待機...")
time.sleep(5)  # 長めの待機時間

print("\n読み取り開始 (10回テスト)\n")

success_count = 0
for i in range(10):
    print(f"試行 {i+1}/10: ", end="", flush=True)
    
    # 複数回リトライ
    for retry in range(3):
        try:
            temperature = dhtDevice.temperature
            humidity = dhtDevice.humidity
            
            if temperature is not None and humidity is not None:
                print(f"成功! 温度: {temperature:.1f}°C  湿度: {humidity:.1f}%")
                success_count += 1
                break
        except RuntimeError as e:
            if retry == 2:  # 最後のリトライ
                print(f"失敗 ({e.args[0]})")
            time.sleep(0.5)  # リトライ前に待機
        except Exception as e:
            print(f"エラー: {e}")
            break
    
    time.sleep(3)  # 次の読み取りまで長めに待機

dhtDevice.exit()
print(f"\n結果: {success_count}/10回成功")

