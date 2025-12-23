import time
import random

def generate_keys():
    keys = ["1","2","3","4","5","6","7","8","9","0","A","B","C","D","*","#", None, None, None]
    while True:
        yield random.choice(keys)


def run_dms_simulator(delay, callback, stop_event):
    for key in generate_keys():
        time.sleep(delay)
        if key is not None:
            callback(key)
        if stop_event.is_set():
            break
