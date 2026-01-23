import RPi.GPIO as GPIO # type: ignore
import time
import threading


# I took this from vjezbe4 tastatura.py, just refactored it to a calss
class Keypad:
    def __init__(self, rows=(25,8,7,1), cols=(12,16,20,21), callback=None, poll_delay=0.2):
        self.R1, self.R2, self.R3, self.R4 = rows
        self.C1, self.C2, self.C3, self.C4 = cols
        self.callback = callback
        self.poll_delay = poll_delay

        # Initialize the GPIO pins
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.R1, GPIO.OUT)
        GPIO.setup(self.R2, GPIO.OUT)
        GPIO.setup(self.R3, GPIO.OUT)
        GPIO.setup(self.R4, GPIO.OUT)

        # Make sure to configure the input pins to use the internal pull-down resistors
        GPIO.setup(self.C1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.C2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.C3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.C4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def _readLine(self, line, characters):
        # The readLine function implements the procedure discussed in the article
        # It sends out a single pulse to one of the rows of the keypad
        # and then checks each column for changes
        # If it detects a change, the user pressed the button that connects the given line
        # to the detected column
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
                # call the readLine function for each row of the keypad
                self._readLine(self.R1, ["1","2","3","A"])
                self._readLine(self.R2, ["4","5","6","B"])
                self._readLine(self.R3, ["7","8","9","C"])
                self._readLine(self.R4, ["*","0","#","D"])
                time.sleep(self.poll_delay)
        finally:
            # no GPIO cleanup here main handles it
            pass
