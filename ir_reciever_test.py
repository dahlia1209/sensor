#!/usr/bin/env python3
import pigpio
import time

IR_PIN = 17

class IRDecoder:
    def __init__(self, pi, gpio):
        self.pi = pi
        self.gpio = gpio
        self.in_code = False
        self.code = []
        self.last_tick = None
        self.last_signal_time = None
        
        pi.set_mode(gpio, pigpio.INPUT)
        pi.callback(gpio, pigpio.EITHER_EDGE, self._callback)
    
    def _callback(self, gpio, level, tick):
        if self.last_tick is not None:
            diff = pigpio.tickDiff(self.last_tick, tick)
            
            if diff > 8000 and not self.in_code:
                self.in_code = True
                self.code = []
            
            if self.in_code:
                self.code.append((level, diff))
                
                if diff > 10000:
                    self.in_code = False
                    if len(self.code) > 10:
                        self.print_code()
        
        self.last_tick = tick
    
    def print_code(self):
        now = time.time()
        print(f"\n=== New Signal ===")
        if self.last_signal_time is not None:
            interval = now - self.last_signal_time
            print(f"Interval since last signal: {interval:.3f}s")
        else:
            print("Interval since last signal: N/A (first signal)")
        self.last_signal_time = now
        print(f"Pulses: {len(self.code)}")
        
        bits = []
        for i, (level, duration) in enumerate(self.code):
            print(f"  [{i}] level={level}, duration={duration}μs")
            
            # リーダーパルス([0]=9ms HIGH, [1]=4.5ms LOW)を除いた
            # LOWパルスのみデコード対象、ストップビット(>15000μs)は除外
            if level == 0 and i >= 3 and duration < 15000:
                if 400 < duration < 800:
                    bits.append('0')
                elif 1400 < duration < 1800:
                    bits.append('1')
                else:
                    print(f"    ^^^ UNRECOGNIZED duration (not decoded as bit)")
        
        print(f"\nDecoded bits: {len(bits)}")
        print(f"Binary: {''.join(bits)}")
        
        # 8ビットごとに区切って表示（読みやすさのため）
        if len(bits) >= 8:
            bytes_list = [bits[i:i+8] for i in range(0, len(bits), 8)]
            hex_list = []
            for b in bytes_list:
                if len(b) == 8:
                    hex_list.append(hex(int(''.join(b), 2)))
            print(f"Hex:    {' '.join(hex_list)}")


pi = pigpio.pi()
if not pi.connected:
    raise RuntimeError("pigpioデーモンに接続できません。'sudo pigpiod' を実行してください。")

decoder = IRDecoder(pi, IR_PIN)
print("IR Decoder ready. Press buttons on your remote...")
print("Press Ctrl+C to exit\n")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\nExiting...")
    pi.stop()
