import json
import time
from simulators.btn import run_btn_simulator
import threading
import paho.mqtt.publish as publish # type: ignore
import settings.broker_settings as broker_settings


btn_batch = []
publish_data_counter = 0
publish_data_limit = 1
counter_lock = threading.Lock()

def publisher_task(event, btn_batch, hostname='localhost', port=1883):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_btn_batch = btn_batch.copy()
            publish_data_counter = 0
            btn_batch.clear()
        publish.multiple(local_btn_batch, hostname=hostname, port=port)
        print(f'[PUBLISH][BTN] {publish_data_limit} values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, btn_batch, broker_settings.HOSTNAME, broker_settings.PORT))
publisher_thread.daemon = True
publisher_thread.start()

def button_pressed_callback(publish_event, settings):
    global publish_data_counter, publish_data_limit
    print(f"[BTN] pressed - {time.strftime('%H:%M:%S', time.localtime())}")

    btn_payload = {
        "measurement": "BTN",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": True,
        "timestamp": time.time_ns()
    }

    with counter_lock:
        btn_batch.append(('BTN', json.dumps(btn_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_btn(settings, threads, stop_event):
        if settings['simulated']:
            print("Starting BTN simulator")
            btn_thread = threading.Thread(target = run_btn_simulator, args=(2, button_pressed_callback, stop_event, publish_event, settings))
            btn_thread.start()
            threads.append(btn_thread)
            print("BTN simulator started")
        else:
            from sensors.Button import Button
            from RPi import GPIO # type: ignore
            def button_pressed_callback_wrapper(event=None):
                button_pressed_callback(publish_event, settings)
            btn = Button(pin = settings['pin'],
                          pull_up = settings.get('pull_up', True),
                          edge=GPIO.FALLING,
                          bouncetime = settings.get('bouncetime', 100),
                          callback = button_pressed_callback_wrapper)
            