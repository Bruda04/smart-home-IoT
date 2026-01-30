import  RPi.GPIO  as GPIO # type: ignore
import  time

class ActiveBuzzer:
    def __init__(self, pin, callback):
        self.pin = pin
        self.callback = callback
        GPIO.setup(self.pin,  GPIO.OUT)

    def buzz(self, pitch, duration):
        period = 1.0 / pitch
        delay = period / 2
        cycles = int(pitch * duration)
        for i in range(cycles):
            GPIO.output(self.pin,  True)
            time.sleep(delay)
            GPIO.output(self.pin,  False)
            time.sleep(delay)

    def on(self):
        GPIO.output(self.pin,  True)
        self.callback(True)

    def off(self):
        GPIO.output(self.pin,  False)
        self.callback(False)


class PassiveBuzzer:
    def __init__(self, pin, callback, frequency=440):
        self.pin = pin
        self.callback = callback
        self.frequency = frequency

        GPIO.setup(self.pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin, self.frequency)
        self.is_on = False

    def buzz(self, pitch, duration, duty_cycle=50):
        self.pwm.ChangeFrequency(pitch)
        self.pwm.start(duty_cycle)
        time.sleep(duration)
        self.pwm.stop()

    def on(self, pitch=None, duty_cycle=50):
        if pitch:
            self.pwm.ChangeFrequency(pitch)

        if not self.is_on:
            self.pwm.start(duty_cycle)
            self.is_on = True
        self.callback(True)

    def off(self):
        if self.is_on:
            self.pwm.stop()
            self.is_on = False
        self.callback(False)