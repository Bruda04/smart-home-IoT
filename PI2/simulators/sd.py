import time
import threading

class StopwatchDisplaySimulator:
    def __init__(self, callback):
        self.callback = callback
        self.current_value = "0000"
        self.running = True
        self.blinking = False
        self.total_seconds = 0
        self.start_time = time.time()
        self.add_delta_seconds = 10
        self.lock = threading.Lock()
        self.last_reported_remaining = None

        threading.Thread(target=self._simulation_loop, daemon=True).start()

    def set_time(self, minutes, seconds):
        with self.lock:
            self.total_seconds = minutes * 60 + seconds
            self.start_time = time.time()
            self.blinking = False
            self.current_value = f"{minutes:02}{seconds:02}"

    def add_seconds(self):
        with self.lock:
            if self.blinking and self.total_seconds == 0:
                self.blinking = False
                self.current_value = "0000"

                if self.callback:
                    if self.blinking:
                        self.callback(0)
                    else:
                        self.callback(self.total_seconds)

                return

            now = time.time()

            if self.total_seconds > 0:
                elapsed = int(now - self.start_time)
                remaining = max(self.total_seconds - elapsed, 0)
                self.total_seconds = remaining + self.add_delta_seconds
            else:
                self.total_seconds = self.add_delta_seconds

            self.start_time = now
            self.blinking = False

            minutes = self.total_seconds // 60
            seconds = self.total_seconds % 60
            self.current_value = f"{minutes:02}{seconds:02}"

            if self.callback:
                if self.blinking:
                    self.callback(0)
                else:
                    self.callback(self.total_seconds)



    def set_add_seconds(self, seconds):
        with self.lock:
            self.add_delta_seconds = seconds

    def _simulation_loop(self):
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
                    print(f"[SD] {self.current_value[:2]}:{self.current_value[2:]}")

                    if self.callback:
                        if self.blinking:
                            if self.last_reported_remaining != 0:
                                self.last_reported_remaining = 0
                                self.callback(0)
                        else:
                            elapsed = int(time.time() - self.start_time)
                            remaining = max(self.total_seconds - elapsed, 0)

                            if remaining != self.last_reported_remaining:
                                self.last_reported_remaining = remaining
                                self.callback(remaining)



            time.sleep(0.1)