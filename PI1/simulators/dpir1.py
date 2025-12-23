import time
import random

def generate_motion():
    while True:
        yield random.choice([True, False, False, False, False])

def run_dpir1_simulator(delay, callback, stop_event):
    for motion in generate_motion():
        time.sleep(delay)
        if motion:
            callback(None)
        if stop_event.is_set():
            break
