from simulators.dl import DLSimulator
import json
import time
import threading
import paho.mqtt.publish as publish # type: ignore
import settings.broker_settings as broker_settings

dl_batch = []
publish_data_counter = 0
publish_data_limit = 1
counter_lock = threading.Lock()

def publisher_task(event, dl_batch, hostname='localhost', port=1883):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_dl_batch = dl_batch.copy()
            publish_data_counter = 0
            dl_batch.clear()
        publish.multiple(local_dl_batch, hostname=hostname, port=port)
        print(f'[PUBLISH][DL] {publish_data_limit} values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(
    target=publisher_task, 
    args=(publish_event, dl_batch, broker_settings.HOSTNAME, broker_settings.PORT)
)
publisher_thread.daemon = True
publisher_thread.start()

def dl_callback(value, publish_event, settings):
    global publish_data_counter, publish_data_limit
    print(f"[DL] {'ON' if value else 'OFF'} - {time.strftime('%H:%M:%S', time.localtime())}")
    payload = {
        "measurement": "DL",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": value,
        "timestamp": time.time_ns()
    }
    with counter_lock:
        dl_batch.append(('DL', json.dumps(payload), 0, True))
        publish_data_counter += 1
    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_dl(settings):
    def callback_wrapper(value):
        dl_callback(value, publish_event, settings)

    if settings['simulated']:
        print("Starting DL simulator")
        simulator = DLSimulator(callback_wrapper)
        print("DL simulator started")
        return simulator
    else:
        from actuators.DoorLight import DoorLight
        dl = DoorLight(settings['pin'], callback_wrapper)
        return dl
