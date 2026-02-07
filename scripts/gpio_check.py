import RPi.GPIO as GPIO
import time

print("=" * 60)
print("電源供給確認テスト")
print("=" * 60)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

pin = 4
GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # プルダウンに変更
time.sleep(0.1)

print("\n【テスト1】プルダウンモード")
state_down = GPIO.input(pin)
print(f"GPIO4の状態: {'HIGH' if state_down else 'LOW'}")

GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # プルアップに変更
time.sleep(0.1)

print("\n【テスト2】プルアップモード")
state_up = GPIO.input(pin)
print(f"GPIO4の状態: {'HIGH' if state_up else 'LOW'}")

print("\n" + "=" * 60)
print("診断結果:")
print("=" * 60)

if state_down == 1 and state_up == 1:
    print("✓ OUT線から信号が出ている（センサーに電源供給されている）")
    print("  → 配線は正しい可能性が高い")
    print("  → ライブラリまたはタイミングの問題")
elif state_down == 0 and state_up == 1:
    print("△ プルアップでのみHIGH（浮いている状態）")
    print("  → OUT線が接続されていないか、センサーに電源なし")
else:
    print("? 予期しない結果")

GPIO.cleanup()
print("=" * 60)
