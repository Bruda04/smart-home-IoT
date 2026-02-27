import RPi.GPIO as GPIO # type: ignore
import time
import threading


class Keypad:
    def __init__(self, rows=(25,8,7,1), cols=(12,16,20,21), callback=None, poll_delay=0.2):
        self.R1, self.R2, self.R3, self.R4 = rows
        self.C1, self.C2, self.C3, self.C4 = cols
        self.callback = callback
        self.poll_delay = poll_delay

        GPIO.setup(self.R1, GPIO.OUT)
        GPIO.setup(self.R2, GPIO.OUT)
        GPIO.setup(self.R3, GPIO.OUT)
        GPIO.setup(self.R4, GPIO.OUT)

        GPIO.setup(self.C1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.C2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.C3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.C4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def _readLine(self, line, characters):
        GPIO.output(line, GPIO.HIGH)
        if GPIO.input(self.C1) == 1:
            if self.callback:
                self.callback(characters[0])
        if GPIO.input(self.C2) == 1:
            if self.callback:
                self.callback(characters[1])
        if GPIO.input(self.C3) == 1:
            if self.callback:
                self.callback(characters[2])
        if GPIO.input(self.C4) == 1:
            if self.callback:
                self.callback(characters[3])
        GPIO.output(line, GPIO.LOW)

    def start_loop(self, stop_event):
        try:
            while not stop_event.is_set():
                self._readLine(self.R1, ["1","2","3","A"])
                self._readLine(self.R2, ["4","5","6","B"])
                self._readLine(self.R3, ["7","8","9","C"])
                self._readLine(self.R4, ["*","0","#","D"])
                time.sleep(self.poll_delay)
        finally:
            pass
