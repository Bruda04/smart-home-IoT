import RPi.GPIO as GPIO  # type: ignore
import time
import threading


class StopwatchDisplay:
    def __init__(self, segments, digits, refresh_rate=0.002, add_delta_seconds=10, callback=None):
        self.segments = segments
        self.digits = digits
        self.refresh_rate = refresh_rate
        self.add_delta_seconds = add_delta_seconds
        self.callback = callback

        self.current_value = "0000"
        self.running = True
        self.blinking = False

        self.total_seconds = 0
        self.start_time = time.time()
        self.last_reported_remaining = None


        self.lock = threading.Lock()

        for seg in self.segments:
            GPIO.setup(seg, GPIO.OUT)
            GPIO.output(seg, 0)

        for dig in self.digits:
            GPIO.setup(dig, GPIO.OUT)
            GPIO.output(dig, 1)

        self.num_map = {
            '0': (1,1,1,1,1,1,0), '1': (0,1,1,0,0,0,0),
            '2': (1,1,0,1,1,0,1), '3': (1,1,1,1,0,0,1),
            '4': (0,1,1,0,0,1,1), '5': (1,0,1,1,0,1,1),
            '6': (1,0,1,1,1,1,1), '7': (1,1,1,0,0,0,0),
            '8': (1,1,1,1,1,1,1), '9': (1,1,1,1,0,1,1),
            ' ': (0,0,0,0,0,0,0)
        }

        threading.Thread(target=self._display_loop, daemon=True).start()
    def set_time(self, minutes, seconds):
        with self.lock:
            self.total_seconds = minutes * 60 + seconds
            self.start_time = time.time()
            self.blinking = False
            self.current_value = f"{minutes:02}{seconds:02}"
            remaining = self.total_seconds
            self.last_reported_remaining = remaining
            if self.callback:
                self.callback(remaining)

    def add_seconds(self):
        with self.lock:
            if self.blinking and self.total_seconds == 0:
                self.blinking = False
                self.total_seconds = 0
                self.current_value = "0000"
                if self.last_reported_remaining != 0:
                    self.last_reported_remaining = 0
                    if self.callback:
                        self.callback(0)
                return

            now = time.time()
            elapsed = int(now - self.start_time)

            if self.total_seconds > 0:
                remaining = max(self.total_seconds - elapsed, 0)
                self.total_seconds = remaining + self.add_delta_seconds
            else:
                self.total_seconds = self.add_delta_seconds

            self.start_time = now
            self.blinking = False
            self.current_value = f"{self.total_seconds//60:02}{self.total_seconds%60:02}"

            self.last_reported_remaining = self.total_seconds
            if self.callback:
                self.callback(self.total_seconds)


    def set_add_seconds(self, seconds):
        with self.lock:
            self.add_delta_seconds = seconds

    def _display_loop(self):
        while self.running:
            with self.lock:
                new_display_value = self.current_value

                if self.total_seconds > 0:
                    elapsed = int(time.time() - self.start_time)
                    remaining = max(self.total_seconds - elapsed, 0)

                    if remaining > 0:
                        minutes = remaining // 60
                        seconds = remaining % 60
                        new_display_value = f"{minutes:02}{seconds:02}"
                    else:
                        self.blinking = True
                        self.total_seconds = 0
                        new_display_value = "0000"

                if self.blinking:
                    if int(time.time() * 2) % 2 == 0:
                        new_display_value = "0000"
                    else:
                        new_display_value = "    "

                if new_display_value != self.current_value:
                    self.current_value = new_display_value
                    if self.total_seconds > 0:
                        elapsed = int(time.time() - self.start_time)
                        remaining = max(self.total_seconds - elapsed, 0)

                        if remaining != self.last_reported_remaining:
                            self.last_reported_remaining = remaining
                            if self.callback:
                                self.callback(remaining)

                    elif self.blinking:
                        if self.last_reported_remaining != 0:
                            self.last_reported_remaining = 0
                            if self.callback:
                                self.callback(0)


            for digit_index, digit_pin in enumerate(self.digits):
                char = self.current_value[digit_index]
                segments_state = self.num_map.get(char, (0,0,0,0,0,0,0))

                for seg_index, seg_pin in enumerate(self.segments[:7]):
                    GPIO.output(seg_pin, segments_state[seg_index])

                GPIO.output(digit_pin, 0)
                time.sleep(self.refresh_rate)
                GPIO.output(digit_pin, 1)