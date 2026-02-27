import RPi.GPIO as GPIO # type: ignore
class Button:
    def __init__(self, pin, pull_up=True, edge=None, bouncetime=200, callback=None):
        self.pin = pin
        self.bouncetime = bouncetime
        self.callback = callback

        if pull_up is True:
            pud = GPIO.PUD_UP
        elif pull_up is False:
            pud = GPIO.PUD_DOWN
        else:
            pud = GPIO.PUD_OFF

        if edge is not None:
            self._edge = edge
        elif pull_up is True:
            self._edge = GPIO.FALLING
        elif pull_up is False:
            self._edge = GPIO.RISING
        else:
            self._edge = GPIO.BOTH

        GPIO.setup(self.pin, GPIO.IN, pull_up_down=pud)

        self.pressed = not bool(GPIO.input(self.pin)) if pull_up else bool(GPIO.input(self.pin))

        def button_callback(channel):
            current_state = bool(GPIO.input(self.pin))
            if pull_up is True:
                current_state = not current_state
            
            if current_state == self.pressed:
                return
            self.pressed = current_state
            if self.callback is not None:
                self.callback(self.pressed)

        GPIO.add_event_detect(self.pin, self._edge, callback=button_callback, bouncetime=self.bouncetime)