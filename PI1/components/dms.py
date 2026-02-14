import json
import time
import threading
import paho.mqtt.publish as publish  # type: ignore
import settings.broker_settings as broker_settings
from simulators.dms import run_dms_simulator


dms_batch = []
publish_data_counter = 0
publish_data_limit = 1
counter_lock = threading.Lock()

def publisher_task(event, dms_batch, hostname='localhost', port=1883):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_batch = dms_batch.copy()
            publish_data_counter = 0
            dms_batch.clear()
        publish.multiple(local_batch, hostname=hostname, port=port)
        print(f'[PUBLISH][DMS] {publish_data_limit} values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(
    target=publisher_task,
    args=(publish_event, dms_batch, broker_settings.HOSTNAME, broker_settings.PORT)
)
publisher_thread.daemon = True
publisher_thread.start()



def keypad_callback(key, publish_event, settings):
    global publish_data_counter, publish_data_limit
    print(f"[DMS] key detected: {key} - {time.strftime('%H:%M:%S', time.localtime())}")

    payload = {
        "measurement": "DMS",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": key,
        "timestamp": time.time_ns()
    }

    with counter_lock:
        dms_batch.append(('DMS', json.dumps(payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_dms(settings, threads, stop_event):
    if 'rows' not in settings or 'cols' not in settings:
        raise ValueError("DMS requires 'rows' and 'cols' in settings to function as keypad")

    def callback_wrapper(key):
        keypad_callback(key, publish_event, settings)

    if settings.get('simulated', True):
        print("Starting DMS (keypad) simulator")
        kp_thread = threading.Thread(
            target=run_dms_simulator,
            args=(settings.get('poll_delay', 0.2), callback_wrapper, stop_event, publish_event, settings)
        )
        kp_thread.start()
        threads.append(kp_thread)
        print("DMS (keypad) simulator started")
    else:
        # real hardware
        from sensors.Keypad import Keypad
        print("Starting DMS keypad sensor")
        kp_sensor = Keypad(
            rows=tuple(settings.get('rows')),
            cols=tuple(settings.get('cols')),
            callback=callback_wrapper,
            poll_delay=settings.get('poll_delay', 0.2)
        )
        sensor_thread = threading.Thread(target=kp_sensor.start_loop, args=(stop_event,))
        sensor_thread.start()
        threads.append(sensor_thread)
