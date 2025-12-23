import RPi.GPIO as GPIO

class PIRSensor:
    def __init__(self, pin, callback=None, bouncetime=200):
        self.pin = pin
        self.callback = callback
        self.bouncetime = bouncetime

        GPIO.setup(self.pin, GPIO.IN)
        # Use rising edge detection (PIR typically goes HIGH when motion detected)
        GPIO.add_event_detect(self.pin, GPIO.RISING, callback=self._internal_cb, bouncetime=self.bouncetime)

    def _internal_cb(self, channel):
        if self.callback:
            self.callback(None)

    def cleanup(self):
        try:
            GPIO.remove_event_detect(self.pin)
        except Exception:
            pass
