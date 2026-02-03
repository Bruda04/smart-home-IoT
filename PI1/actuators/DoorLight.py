import RPi.GPIO as GPIO # type: ignore

class DoorLight:
    def __init__(self, pin, callback=None):
        self.pin = pin
        self.callback = callback
        GPIO.setup(self.pin, GPIO.OUT)
        self.is_on = False

    def on(self):
        if not self.is_on:
            GPIO.output(self.pin, True)
            self.is_on = True
            if self.callback:
                self.callback(True)

    def off(self):
        if self.is_on:
            GPIO.output(self.pin, False)
            self.is_on = False
            if self.callback:
                self.callback(False)
