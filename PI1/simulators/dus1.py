import time
import random

def generate_values():
    while True:
        yield random.uniform(2, 400)

def run_dus1_simulator(delay, callback, stop_event):
        for distance in generate_values():
            time.sleep(delay)
            callback(distance)
            if stop_event.is_set():
                  break
              