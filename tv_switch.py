#!/usr/bin/env python3
import pigpio
import time
IR_TX_PIN = 18
def send_nec_raw_binary(pi, gpio, binary_str):
    """受信したバイナリデータをそのまま送信"""
    
    pi.set_mode(gpio, pigpio.OUTPUT)
    
    wf = []
    
    def add_mark(duration_us):
        cycles = int(duration_us / 26)
        for _ in range(cycles):
            wf.append(pigpio.pulse(1 << gpio, 0, 13))
            wf.append(pigpio.pulse(0, 1 << gpio, 13))
    
    def add_space(duration_us):
        wf.append(pigpio.pulse(0, 1 << gpio, duration_us))
    
    # リーダーコード
    add_mark(9000)
    add_space(4500)
    
    # バイナリ文字列から各ビットを送信
    for bit_char in binary_str:
        add_mark(560)
        if bit_char == '1':
            add_space(1690)
        else:
            add_space(560)
    
    # 終了ビット
    add_mark(560)
    
    # Wave送信
    pi.wave_clear()
    pi.wave_add_generic(wf)
    wid = pi.wave_create()
    
    if wid >= 0:
        pi.wave_send_once(wid)
        while pi.wave_tx_busy():
            time.sleep(0.001)
        pi.wave_delete(wid)
    
    pi.write(gpio, 0)

# メイン
pi = pigpio.pi()
# リモコンから受信したバイナリデータ
remote_binary = "00000001110001101111000000001111"
print("Sending exact remote signal")
print(f"Binary: {remote_binary}")
print("Address: 0x01 (inv: 0xC6)")
print("Command: 0xF0 (inv: 0x0F)")
print("Expected: 0x01C6F00F")

for i in range(1):
    send_nec_raw_binary(pi, IR_TX_PIN, remote_binary)
    print(f"Signal sent! ({i+1}/2)")
    time.sleep(0.1)

pi.stop()
