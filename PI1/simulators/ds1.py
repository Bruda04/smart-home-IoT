import time
import random

def generate_values():
    while True:
        yield random.choice([True, False, False, False, False])

def run_ds1_simulator(delay, callback, stop_event, publish_event, settings):
        for press in generate_values():
            time.sleep(delay)
            if press:
                callback(publish_event, settings)
            if stop_event.is_set():
                  break
              