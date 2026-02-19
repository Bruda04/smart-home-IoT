import time
import random

def generate_values():
    while True:
        yield random.choice([True, False, False, False, False])

def run_ds1_simulator(delay, callback, stop_event):
        for press in generate_values():
            time.sleep(delay)
            if press:
                callback(press)
                if random.random() < 0.25:
                     time.sleep(6)
                callback(False)
            if stop_event.is_set():
                  break
              