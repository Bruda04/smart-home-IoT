import RPi.GPIO as GPIO  # type: ignore

class Button:
    def __init__(self, pin, pull_up = True, bouncetime = 100, callback = None, publish_event = None, settings = None):
        self.pin = pin
        self.pull_up = pull_up
        self.bouncetime = bouncetime
        self.callback = callback
        self.publish_event = publish_event
        self.settings = settings

        GPIO.setup(self.pin,
                    GPIO.IN,
                    pull_up_down = GPIO.PUD_UP if self.pull_up else GPIO.PUD_DOWN
                    )
        GPIO.add_event_detect(self.pin,
                            GPIO.RISING if self.pull_up else GPIO.FALLING,
                            callback = self._callback_wrapper,
                            bouncetime = self.bouncetime)
        
        def _callback_wrapper(self):
            if self.callback is not None:
                self.callback(self.publish_event, self.settings)