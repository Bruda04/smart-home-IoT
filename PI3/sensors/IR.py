import RPi.GPIO as GPIO
from datetime import datetime
import time

class IRReceiver:
    def __init__(self, pin, callback):
        self.pin = pin
        self.callback = callback
        
        self.buttons = [
            0x300ff22dd, 0x300ffc23d, 0x300ff629d, 0x300ffa857, 0x300ff9867, 
            0x300ffb04f, 0x300ff6897, 0x300ff02fd, 0x300ff30cf, 0x300ff18e7, 
            0x300ff7a85, 0x300ff10ef, 0x300ff38c7, 0x300ff5aa5, 0x300ff42bd, 
            0x300ff4ab5, 0x300ff52ad
        ]
        self.button_names = [
            "LEFT", "RIGHT", "UP", "DOWN", "2", "3", "1", "OK", "4", "5", 
            "6", "7", "8", "9", "*", "0", "#"
        ]

        GPIO.setup(self.pin, GPIO.IN)

    def _get_binary(self):
        num1s = 0
        binary = 1
        command = []
        previousValue = 0
        
        timeout = time.time() + 0.2  # 200ms timeout
        while GPIO.input(self.pin):
            if time.time() > timeout:
                return None
            time.sleep(0.0001)
            
        startTime = datetime.now()
        while True:
            value = GPIO.input(self.pin)
            if previousValue != value:
                now = datetime.now()
                pulseTime = now - startTime
                startTime = now
                command.append((previousValue, pulseTime.microseconds))
            
            if value:
                num1s += 1
            else:
                num1s = 0
            
            if num1s > 10000:
                break
            
            previousValue = value

        for (typ, tme) in command:
            if typ == 1:
                if tme > 1000:
                    binary = binary * 10 + 1
                else:
                    binary *= 10
                    
        if len(str(binary)) > 34:
            binary = int(str(binary)[:34])
            
        return binary

    def listen_once(self):
        binary_value = self._get_binary()
        if binary_value:
            try:
                in_data = hex(int(str(binary_value), 2))
                for i in range(len(self.buttons)):
                    if hex(self.buttons[i]) == in_data:
                        self.callback(self.button_names[i])
            except (ValueError, SyntaxError):
                pass