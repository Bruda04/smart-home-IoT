import RPi.GPIO as GPIO  # type: ignore

class Button:
    def __init__(self, pin, pull_up, bouncetime = 100, callback = None):
        self.pin = pin
        self.pull_up = pull_up
        self.bouncetime = bouncetime
        self.callback = callback

        if pull_up is None:
            self.edge = GPIO.BOTH
        elif pull_up:
            self.edge = GPIO.FALLING
        else:
            self.edge = GPIO.RISING


        GPIO.setup(self.pin,
                    GPIO.IN,
                    pull_up_down = GPIO.PUD_UP if self.pull_up else GPIO.PUD_DOWN
                    )
        GPIO.add_event_detect(self.pin,
                            self.edge,
                            callback = self.callback,
                            bouncetime = self.bouncetime)
        