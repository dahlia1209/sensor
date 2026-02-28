#!/usr/bin/env python3
import pigpio
import time

IR_TX_PIN = 18

def send_nec_raw_binary(pi, gpio, binary_str):
    pi.set_mode(gpio, pigpio.OUTPUT)
    pi.write(gpio, 0) 
    wf = []

    def add_mark(duration_us):
        cycles = int(duration_us / 26)
        for _ in range(cycles):
            wf.append(pigpio.pulse(1 << gpio, 0, 13))
            wf.append(pigpio.pulse(0, 1 << gpio, 13))

    def add_space(duration_us):
        wf.append(pigpio.pulse(0, 1 << gpio, duration_us))

    add_mark(9000)
    add_space(4500)

    for bit_char in binary_str:
        add_mark(560)
        if bit_char == '1':
            add_space(1690)
        else:
            add_space(560)

    add_mark(560)

    pi.wave_clear()
    pi.wave_add_generic(wf)
    wid = pi.wave_create()

    if wid >= 0:
        pi.wave_send_once(wid)
        while pi.wave_tx_busy():
            time.sleep(0.001)
        pi.wave_delete(wid)

    pi.write(gpio, 0)

pi = pigpio.pi()

# ★順序を元のリモコンに合わせて修正
signals = [
    {
        "binary": "00110000010100000000011000000011",
        "label": "Signal 1",
        "full_code": "0x30500603",
    },
    {
        "binary": "00000000000100000000000000000111",
        "label": "Signal 2",
        "full_code": "0x00100007",
    },
]

for sig in signals:
    print(f"Sending {sig['label']} (Full code: {sig['full_code']})")
    print(f"Binary: {sig['binary']}")
    send_nec_raw_binary(pi, IR_TX_PIN, sig["binary"])
    print(f"{sig['label']} sent!")
    time.sleep(0.167)

print("All signals sent!")
pi.stop()
