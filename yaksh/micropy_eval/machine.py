# machine.py (Unix MicroPython ONLY)
# This file is ignored on ESP32

import time
import random

# =====================
# Pin
# =====================
class Pin:
    IN = 0
    OUT = 1
    OPEN_DRAIN = 2

    PULL_UP = 1
    PULL_DOWN = 2

    def __init__(self, pin, mode=-1, pull=None):
        self.id = pin
        self.mode = mode
        self.pull = pull
        self._value = 0
        print(f"[SIM][Pin] GPIO{pin} initialized")

    def value(self, v=None):
        if v is None:
            return self._value
        self._value = 1 if v else 0
        print(f"[SIM][Pin] GPIO{self.id} -> {'HIGH' if self._value else 'LOW'}")

    def on(self):
        self.value(1)

    def off(self):
        self.value(0)

    def toggle(self):
        self.value(not self._value)

    def irq(self, handler=None, trigger=None):
        print(f"[SIM][Pin] irq registered on GPIO{self.id} (ignored)")
        return None


# =====================
# ADC
# =====================
class ADC:
    ATTN_0DB = 0
    ATTN_2_5DB = 1
    ATTN_6DB = 2
    ATTN_11DB = 3

    def __init__(self, pin):
        self.pin = pin.id if isinstance(pin, Pin) else pin
        self._value = 2048
        print(f"[SIM][ADC] GPIO{self.pin} initialized")

    def atten(self, _):
        pass

    def width(self, _):
        pass

    def read(self):
        print(f"[SIM][ADC] GPIO{self.pin} read -> {self._value}")
        return self._value

    # Non-ESP32 extension: test injection
    def _set(self, value):
        self._value = value


# =====================
# PWM
# =====================
class PWM:
    def __init__(self, pin, freq=1000, duty=0):
        self.pin = pin.id if isinstance(pin, Pin) else pin
        self.freq = freq
        self._duty = duty
        print(f"[SIM][PWM] GPIO{self.pin} initialized @ {freq}Hz")

    def duty(self, value=None):
        if value is None:
            return self._duty
        self._duty = value
        print(f"[SIM][PWM] GPIO{self.pin} duty -> {value}")

    def freq(self, value=None):
        if value is None:
            return self.freq
        self.freq = value
        print(f"[SIM][PWM] freq -> {value}")

    def deinit(self):
        print(f"[SIM][PWM] GPIO{self.pin} deinit")


# =====================
# Time-related stubs
# =====================
def reset():
    print("[SIM][machine] reset() ignored")

def deepsleep(ms=0):
    print(f"[SIM][machine] deepsleep({ms}) ignored")

# =====================
# Timer
# =====================
class Timer:
    ONE_SHOT = 0
    PERIODIC = 1

    def __init__(self, id=0):
        self.id = id
        self.period = None
        self.mode = None
        self.callback = None
        print(f"[SIM][Timer] Timer{self.id} created")

    def init(self, period=0, mode=ONE_SHOT, callback=None):
        self.period = period
        self.mode = mode
        self.callback = callback

        mode_str = "ONE_SHOT" if mode == self.ONE_SHOT else "PERIODIC"
        print(f"[SIM][Timer] Timer{self.id} init period={period} mode={mode_str}")

        # SAFE callback invocation (once only)
        if callback:
            print(f"[SIM][Timer] Timer{self.id} callback invoked")
            try:
                callback(self)
            except TypeError:
                # Some users define callback without args
                callback()

    def deinit(self):
        print(f"[SIM][Timer] Timer{self.id} deinit")
