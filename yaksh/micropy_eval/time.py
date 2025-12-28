# time.py (Yaksh abstraction for MicroPython)
# This overrides the real time module during evaluation
# Non-blocking, syntax-validation only

print("[SIM][time] module loaded")

# =====================
# sleep functions
# =====================
def sleep(seconds):
    print(f"[SIM][time] sleep({seconds}s)")


def sleep_ms(ms):
    print(f"[SIM][time] sleep_ms({ms}ms)")


def sleep_us(us):
    print(f"[SIM][time] sleep_us({us}us)")


# =====================
# ticks functions
# =====================
def ticks_ms():
    print("[SIM][time] ticks_ms()")
    return 0


def ticks_us():
    print("[SIM][time] ticks_us()")
    return 0


def ticks_cpu():
    print("[SIM][time] ticks_cpu()")
    return 0


def ticks_diff(ticks1, ticks2):
    print(f"[SIM][time] ticks_diff({ticks1}, {ticks2})")
    return ticks1 - ticks2


def ticks_add(ticks, delta):
    print(f"[SIM][time] ticks_add({ticks}, {delta})")
    return ticks + delta
