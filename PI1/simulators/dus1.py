import time
import random

def generate_values():
    while True:
        yield random.uniform(2, 400)

def run_dus1_simulator(delay, callback, stop_event, publish_event, settings):
        for distance in generate_values():
            time.sleep(delay)
            callback(distance, publish_event, settings)
            if stop_event.is_set():
                  break
              