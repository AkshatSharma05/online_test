# machine.py (Unix MicroPython ONLY)
# This file is ignored on ESP32

import os
import time

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

    def value(self, v=None):
        if v is None:
            return self._value
        self._value = 1 if v else 0

    def on(self):
        self.value(1)

    def off(self):
        self.value(0)

    def toggle(self):
        self.value(not self._value)

    def irq(self, handler=None, trigger=None):
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
        self._used = False

    def atten(self, _):
        pass

    def width(self, _):
        pass

    def read(self):
        inject = os.getenv("SIM_TEMP_INJECT")
        if inject is None:
            raise RuntimeError(
                "ADC.read() called but SIM_TEMP_INJECT not set"
            )
        self._used = True
        return int(inject)


# =====================
# PWM
# =====================
class PWM:
    def __init__(self, pin, freq=1000, duty=0):
        self.pin = pin.id if isinstance(pin, Pin) else pin
        self._freq = freq
        self._duty = duty

    def duty(self, value=None):
        if value is None:
            return self._duty
        self._duty = value

    def freq(self, value=None):
        if value is None:
            return self._freq
        self._freq = value

    def deinit(self):
        pass


# =====================
# Power / Sleep
# =====================
def reset():
    pass

def deepsleep(ms=0):
    pass


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

    def init(self, period=0, mode=ONE_SHOT, callback=None):
        self.period = period
        self.mode = mode
        self.callback = callback

        # IMPORTANT: callback still executes
        if callback:
            try:
                callback(self)
            except TypeError:
                callback()

    def deinit(self):
        pass

    # =====================
    # time module equivalents (NON-BLOCKING)
    # =====================
    @staticmethod
    def sleep(seconds):
        pass

    @staticmethod
    def sleep_ms(ms):
        pass

    @staticmethod
    def sleep_us(us):
        pass

    # =====================
    # ticks functions
    # =====================
    @staticmethod
    def ticks_ms():
        return int(time.time() * 1000)

    @staticmethod
    def ticks_us():
        return int(time.time() * 1_000_000)

    @staticmethod
    def ticks_cpu():
        return int(time.time() * 1_000_000)

    @staticmethod
    def ticks_diff(ticks1, ticks2):
        return ticks1 - ticks2

    @staticmethod
    def ticks_add(ticks, delta):
        return ticks + delta

    # =====================
    # micropython.schedule abstraction
    # =====================
    @staticmethod
    def schedule(func, arg):
        try:
            func(arg)
        except TypeError:
            func()
