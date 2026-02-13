import RPi.GPIO as GPIO # type: ignore

class RGB_LED:
    def __init__(self, red_pin, green_pin, blue_pin):
        self.red_pin = red_pin
        self.green_pin = green_pin
        self.blue_pin = blue_pin
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([self.red_pin, self.green_pin, self.blue_pin], GPIO.OUT)
        
        self.red_pwm = GPIO.PWM(self.red_pin, 100)
        self.green_pwm = GPIO.PWM(self.green_pin, 100)
        self.blue_pwm = GPIO.PWM(self.blue_pin, 100)
        
        self.red_pwm.start(0)
        self.green_pwm.start(0)
        self.blue_pwm.start(0)
        
        self.current_color = [0, 0, 0]
        self.is_on = False

    def set_color(self, r, g, b):
        self.current_color = [r, g, b]
        if self.is_on:
            self.red_pwm.ChangeDutyCycle((r / 255) * 100)
            self.green_pwm.ChangeDutyCycle((g / 255) * 100)
            self.blue_pwm.ChangeDutyCycle((b / 255) * 100)

    def on(self):
        self.is_on = True
        if self.current_color == [0, 0, 0]:
            self.set_color(255, 255, 255)
        else:
            self.set_color(*self.current_color)

    def off(self):
        self.is_on = False
        self.red_pwm.ChangeDutyCycle(0)
        self.green_pwm.ChangeDutyCycle(0)
        self.blue_pwm.ChangeDutyCycle(0)