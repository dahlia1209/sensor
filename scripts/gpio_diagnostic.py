import RPi.GPIO as GPIO
import time
import sys

print("=" * 60)
print("GPIO診断プログラム - AM2302センサー")
print("=" * 60)

# GPIO設定
GPIO_PIN = 4  # GPIO4を使用
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

print("\n[ステップ1] GPIOピンの状態確認")
print(f"使用GPIO: GPIO{GPIO_PIN} (物理ピン7)")

try:
    # 入力モードで読み取り
    GPIO.setup(GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    time.sleep(0.1)
    
    initial_state = GPIO.input(GPIO_PIN)
    print(f"初期状態 (プルアップ有効): {'HIGH (1)' if initial_state else 'LOW (0)'}")
    
    if initial_state == 0:
        print("⚠ 警告: ピンがLOWです")
        print("  原因候補:")
        print("    - DATA線がGNDにショート")
        print("    - センサーが故障してLOWを出力")
        print("    - 配線間違い")
    else:
        print("✓ ピンはHIGHです")
    
    # プルアップなしでも確認
    GPIO.setup(GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_OFF)
    time.sleep(0.1)
    state_no_pull = GPIO.input(GPIO_PIN)
    print(f"初期状態 (プルアップなし): {'HIGH (1)' if state_no_pull else 'LOW (0)'}")
    
    if state_no_pull == 0 and initial_state == 0:
        print("⚠ プルアップなしでもLOW → 確実にショートまたは故障")
    elif state_no_pull == 0 and initial_state == 1:
        print("⚠ プルアップ抵抗がない、またはセンサー未接続")
    
    # 連続読み取りテスト
    print("\n[ステップ2] 3秒間のピン状態監視")
    GPIO.setup(GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    states = []
    print("監視中", end="", flush=True)
    for i in range(30):
        state = GPIO.input(GPIO_PIN)
        states.append(state)
        print(".", end="", flush=True)
        time.sleep(0.1)
    
    print("\n")
    changes = sum(1 for i in range(len(states)-1) if states[i] != states[i+1])
    high_count = sum(states)
    low_count = len(states) - high_count
    
    print(f"HIGH回数: {high_count}/30")
    print(f"LOW回数: {low_count}/30")
    print(f"状態変化回数: {changes}回")
    
    if changes == 0:
        if states[0] == 0:
            print("✗ 常にLOW → 配線ショート、またはセンサー故障")
        else:
            print("✗ 常にHIGH → センサー未接続、DATA線未接続、または電源未供給")
    elif changes > 10:
        print("⚠ 頻繁な変化 → ノイズまたは不安定な接続")
    else:
        print("? わずかな変化を検出")
    
    # 手動通信テスト
    print("\n[ステップ3] センサー起動シーケンステスト")
    print("DHT22プロトコルで起動信号を送信...")
    
    # 起動信号送信
    GPIO.setup(GPIO_PIN, GPIO.OUT)
    GPIO.output(GPIO_PIN, GPIO.HIGH)
    time.sleep(0.25)
    GPIO.output(GPIO_PIN, GPIO.LOW)
    time.sleep(0.02)  # 20ms LOW
    
    # 入力モードに切り替え
    GPIO.setup(GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    time.sleep(0.00004)  # 40us待機
    
    # センサーからの応答を待つ
    print("センサー応答待機中 (最大1ms)...")
    
    timeout_time = time.time() + 0.001
    response_low = False
    response_high = False
    
    # LOWへの変化を待つ (センサーが80us LOWを出力するはず)
    while time.time() < timeout_time:
        if GPIO.input(GPIO_PIN) == 0:
            response_low = True
            print("✓ センサーからLOW応答検出!")
            break
    
    if response_low:
        # HIGHへの変化を待つ
        timeout_time = time.time() + 0.001
        while time.time() < timeout_time:
            if GPIO.input(GPIO_PIN) == 1:
                response_high = True
                print("✓ センサーからHIGH応答検出!")
                break
    
    time.sleep(0.1)
    
    print("\n--- 診断結果 ---")
    if response_low and response_high:
        print("✓ センサーは応答しています!")
        print("  → ライブラリまたはタイミングの問題の可能性")
    elif response_low and not response_high:
        print("△ LOW応答のみ検出")
        print("  → センサーは動作しているが不完全")
    else:
        print("✗ センサーからの応答なし")
        print("\n最も可能性の高い原因:")
        if initial_state == 0:
            print("  1. DATA線がGNDにショート")
            print("  2. センサーが故障")
        else:
            print("  1. DATA線が接続されていない")
            print("  2. センサーに電源が供給されていない (VCC, GND確認)")
            print("  3. 間違ったGPIOピンに接続 (GPIO4 = 物理ピン7)")
            print("  4. センサーの向きが逆")

except KeyboardInterrupt:
    print("\n中断されました")
except Exception as e:
    print(f"\nエラー発生: {e}")
    import traceback
    traceback.print_exc()

finally:
    GPIO.cleanup()
    print("\nGPIOクリーンアップ完了")

# 物理的な確認ガイド
print("\n" + "=" * 60)
print("物理的な確認事項")
print("=" * 60)
print("\n【配線確認】")
print("ラズベリーパイのピン配置 (GPIO.BCM モード):")
print("")
print("   3.3V  [ 1] [ 2]  5V")
print("  GPIO2  [ 3] [ 4]  5V") 
print("  GPIO3  [ 5] [ 6]  GND")
print("  GPIO4  [ 7] [ 8]  GPIO14  ← GPIO4はここ!")
print("    GND  [ 9] [10]  GPIO15")
print("")
print("接続確認:")
print("  1. AM2302のVCCピン → ラズパイの 5V (ピン2または4)")
print("  2. AM2302のDATAピン → ラズパイの GPIO4 (物理ピン7)")
print("  3. AM2302のGNDピン → ラズパイの GND (ピン6, 9, 14, 20など)")
print("")
print("【電源確認】")
print("  - ラズパイの電源は十分か? (推奨5V 3A)")
print("  - USBハブ経由の場合は直接接続を試す")
print("")
print("【センサー確認】")
print("  - センサーの向き: 穴(グリッド)が手前、ピンが下")
print("  - ピンの曲がり、接触不良がないか")
print("  - 別のセンサーと交換して試す")
print("")
print("【次のテスト】")
print("GPIO17 (物理ピン11) で試してみる:")
print("  dhtDevice = adafruit_dht.DHT22(board.D17, use_pulseio=False)")
print("=" * 60)
