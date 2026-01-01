class Pin:
    OUT = 1

    def __init__(self, pin, mode=None):
        self.pin = pin
        self.mode = mode
        self.state = 0

    def on(self):
        self.state = 1

    def off(self):
        self.state = 0


class ADC:
    def __init__(self, pin):
        self.pin = pin
        self._value = 0

    def read(self):
        return self._value

    def atten(self, _):
        pass

    def width(self, _):
        pass


class PWM:
    def __init__(self, pin):
        self.pin = pin
        self._freq = None
        self._duty = None

    def freq(self, value=None):
        if value is not None:
            self._freq = value
        return self._freq

    def duty(self, value=None):
        if value is not None:
            self._duty = value
        return self._duty


class Timer:
    ONE_SHOT = 0
    PERIODIC = 1

    def __init__(self, timer_id):
        self.timer_id = timer_id
        self.period = None
        self.mode = None
        self.callback = None

    def init(self, period, mode, callback):
        self.period = period
        self.mode = mode
        self.callback = callback