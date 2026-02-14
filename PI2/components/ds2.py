import json
import time
from simulators.ds2 import run_ds2_simulator
import threading
import paho.mqtt.publish as publish # type: ignore
import settings.broker_settings as broker_settings


ds2_batch = []
publish_data_counter = 0
publish_data_limit = 1
counter_lock = threading.Lock()

def publisher_task(event, ds2_batch, hostname='localhost', port=1883):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_ds2_batch = ds2_batch.copy()
            publish_data_counter = 0
            ds2_batch.clear()
        publish.multiple(local_ds2_batch, hostname=hostname, port=port)
        print(f'[PUBLISH][DS2] {publish_data_limit} values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, ds2_batch, broker_settings.HOSTNAME, broker_settings.PORT))
publisher_thread.daemon = True
publisher_thread.start()

def button_pressed_callback(pressed, publish_event, settings):
    global publish_data_counter, publish_data_limit
    print(f"[DS2] {('PRESSED' if pressed else 'RELEASED')} - {time.strftime('%H:%M:%S', time.localtime())}")

    ds2_payload = {
        "measurement": "DS2",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": pressed,
        "timestamp": time.time_ns()
    }

    with counter_lock:
        ds2_batch.append(('DS2', json.dumps(ds2_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_ds2(settings, threads, stop_event):
        def button_pressed_callback_wrapper(pressed):
                button_pressed_callback(pressed, publish_event, settings)
        if settings['simulated']:
            print("Starting DS2 simulator")
            ds2_thread = threading.Thread(target = run_ds2_simulator, args=(2, button_pressed_callback_wrapper, stop_event))
            ds2_thread.start()
            threads.append(ds2_thread)
            print("DS2 simulator started")
        else:
            from sensors.Button import Button
            
            ds2 = Button(pin = settings['pin'],
                          pull_up = None,
                          bouncetime = settings.get('bouncetime', 100),
                          callback = button_pressed_callback_wrapper)
            