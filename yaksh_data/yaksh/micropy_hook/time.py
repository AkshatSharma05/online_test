import time as _host_time

# ----------------------------
# Internal tracking variables
# ----------------------------

_last_sleep = None
_last_sleep_ms = None
_last_sleep_us = None
_last_ticks_add_args = None
_last_ticks_diff_args = None


# ----------------------------
# Sleep functions
# ----------------------------

def sleep(seconds):
    global _last_sleep
    _last_sleep = seconds


def sleep_ms(ms):
    global _last_sleep_ms
    _last_sleep_ms = ms


def sleep_us(us):
    global _last_sleep_us
    _last_sleep_us = us


# ----------------------------
# Time tracking
# ----------------------------

_start_time = _host_time.time()


def time():
    return int(_host_time.time())


def ticks_ms():
    return int((_host_time.time() - _start_time) * 1000)


def ticks_us():
    return int((_host_time.time() - _start_time) * 1_000_000)


def ticks_cpu():
    return ticks_us()


def ticks_add(ticks, delta):
    global _last_ticks_add_args
    _last_ticks_add_args = (ticks, delta)
    return ticks + delta


def ticks_diff(ticks1, ticks2):
    global _last_ticks_diff_args
    _last_ticks_diff_args = (ticks1, ticks2)
    return ticks1 - ticks2


# ----------------------------
# Local time helpers
# ----------------------------

def localtime(secs=None):
    if secs is None:
        secs = _host_time.time()
    return _host_time.localtime(secs)


def mktime(t):
    return int(_host_time.mktime(t))