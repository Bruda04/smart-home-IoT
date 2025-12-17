from simulators.ds1 import run_ds1_simulator
import threading

def button_pressed_callback(event):
   print("DS1 BUTTON PRESS DETECTED")


def run_ds1(settings, threads, stop_event):
        if settings['simulated']:
            print("Starting DS1 simulator")
            ds1_thread = threading.Thread(target = run_ds1_simulator, args=(2, button_pressed_callback, stop_event))
            ds1_thread.start()
            threads.append(ds1_thread)
            print("DS1 simulator started")
        else:
            from sensors.Button import Button
            ds1 = Button(pin = settings['pin'],
                          pull_up = settings.get('pull_up', True),
                          bouncetime = settings.get('bouncetime', 100),
                          callback = button_pressed_callback)