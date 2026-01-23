import json
import time
from simulators.ds1 import run_ds1_simulator
import threading
import paho.mqtt.publish as publish # type: ignore
import settings.broker_settings as broker_settings


ds1_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()

def publisher_task(event, ds1_batch, hostname='localhost', port=1883):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_ds1_batch = ds1_batch.copy()
            publish_data_counter = 0
            ds1_batch.clear()
        publish.multiple(local_ds1_batch, hostname=hostname, port=port)
        print(f'[PUBLISH][DS1] {publish_data_limit} values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, ds1_batch, broker_settings.HOSTNAME, broker_settings.PORT))
publisher_thread.daemon = True
publisher_thread.start()

def button_pressed_callback(publish_event, settings):
    global publish_data_counter, publish_data_limit
    print(f"[DS1] pressed - {time.strftime('%H:%M:%S', time.localtime())}")

    ds1_payload = {
        "measurement": "DS1",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": True,
        "timestamp": time.time_ns()
    }

    with counter_lock:
        ds1_batch.append(('DS1', json.dumps(ds1_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_ds1(settings, threads, stop_event):
        if settings['simulated']:
            print("Starting DS1 simulator")
            ds1_thread = threading.Thread(target = run_ds1_simulator, args=(2, button_pressed_callback, stop_event, publish_event, settings))
            ds1_thread.start()
            threads.append(ds1_thread)
            print("DS1 simulator started")
        else:
            from sensors.Button import Button
            def button_pressed_callback_wrapper():
                button_pressed_callback(publish_event, settings)
            ds1 = Button(pin = settings['pin'],
                          pull_up = settings.get('pull_up', True),
                          bouncetime = settings.get('bouncetime', 100),
                          callback = button_pressed_callback_wrapper)