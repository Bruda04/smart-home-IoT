import time
import random

def generate_ir_keys():
    keys = ["LEFT", "RIGHT", "UP", "DOWN", "2", "3", "1", "OK", "4", "5", "6", "7", "8", "9", "*", "0", "#"]
    keys_with_silence = keys + [None] * 20 
    while True:
        yield random.choice(keys_with_silence)


def run_ir_simulator(delay, callback, stop_event):
    for button in generate_ir_keys():
        time.sleep(delay)
        if button is not None:
            callback(button)
        if stop_event.is_set():
            break