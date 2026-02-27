import json
import time
import threading
import paho.mqtt.publish as publish  # type: ignore
import settings.broker_settings as broker_settings
from simulators.dpir3 import run_dpir3_simulator

dpir_batch = []
publish_data_counter = 0
publish_data_limit = 1
counter_lock = threading.Lock()

def publisher_task(event, dpir_batch, hostname='localhost', port=1883):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_batch = dpir_batch.copy()
            publish_data_counter = 0
            dpir_batch.clear()
        publish.multiple(local_batch, hostname=hostname, port=port)
        print(f'[PUBLISH][DPIR3] {publish_data_limit} values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(
    target=publisher_task,
    args=(publish_event, dpir_batch, broker_settings.HOSTNAME, broker_settings.PORT)
)
publisher_thread.daemon = True
publisher_thread.start()


def motion_detected_callback(publish_event, settings):
    global publish_data_counter, publish_data_limit
    print(f"[DPIR3] motion detected {time.strftime('%H:%M:%S', time.localtime())}")

    payload = {
        "measurement": "DPIR3",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": True,
        "timestamp": time.time_ns()
    }

    with counter_lock:
        dpir_batch.append(('DPIR3', json.dumps(payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_dpir3(settings, threads, stop_event):
    if settings.get('simulated', True):
        print("Starting DPIR3 simulator")
        dpir_thread = threading.Thread(
            target=run_dpir3_simulator,
            args=(settings.get('poll_delay', 1), motion_detected_callback, stop_event, publish_event, settings)
        )
        dpir_thread.start()
        threads.append(dpir_thread)
        print("DPIR3 simulator started")
    else:
        from sensors.PIRSensor import PIRSensor
        def callback_wrapper(_):
            motion_detected_callback(publish_event, settings)

        print("Starting DPIR3 PIR sensor")
        PIRSensor(pin=settings['pin'],
                        callback=callback_wrapper,
                        bouncetime=settings.get('bouncetime', 200))
