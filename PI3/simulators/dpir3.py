import time
import random

def generate_motion():
    while True:
        yield random.choice([True, False, False, False, False])

def run_dpir3_simulator(delay, callback, stop_event, publish_event, settings):
    for motion in generate_motion():
        time.sleep(delay)
        if motion:
            callback(publish_event, settings)
        if stop_event.is_set():
            break
