import RPi.GPIO as GPIO

class Button:
    def __init__(self, pin, pull_up = True, bouncetime = 100, callback = None):
        self.pin = pin
        self.pull_up = pull_up
        self.bouncetime = bouncetime
        self.callback = callback

        GPIO.setup(self.pin,
                    GPIO.IN,
                    pull_up_down = GPIO.PUD_UP if self.pull_up else GPIO.PUD_DOWN
                    )
        GPIO.add_event_detect(self.pin,
                            GPIO.RISING if self.pull_up else GPIO.FALLING,
                            callback = self.callback,
                            bouncetime = self.bouncetime)