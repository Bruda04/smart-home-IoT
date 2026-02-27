from simulators.sd import StopwatchDisplaySimulator
import json
import time
import threading
import paho.mqtt.publish as publish # type: ignore
import settings.broker_settings as broker_settings

sd_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()

def publisher_task(event, sd_batch, hostname='localhost', port=1883):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_sd_batch = sd_batch.copy()
            publish_data_counter = 0
            sd_batch.clear()
        publish.multiple(local_sd_batch, hostname=hostname, port=port)
        print(f'[PUBLISH][SD] {publish_data_limit} values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(
    target=publisher_task, 
    args=(publish_event, sd_batch, broker_settings.HOSTNAME, broker_settings.PORT)
)
publisher_thread.daemon = True
publisher_thread.start()

def sd_callback(value, publish_event, settings):
    global publish_data_counter, publish_data_limit
    payload = {
        "measurement": "SD",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": value,
        "timestamp": time.time_ns()
    }
    with counter_lock:
        sd_batch.append(('SD', json.dumps(payload), 0, True))
        publish_data_counter += 1
    if publish_data_counter >= publish_data_limit or value == 0:
        publish_event.set()


def run_sd(settings):
    def callback(value):
        sd_callback(value, publish_event, settings)

    if settings['simulated']:
        print("Starting 4SD simulator")
        simulator = StopwatchDisplaySimulator(callback)
        return simulator
    else:
        from actuators.SegmentDisplay import StopwatchDisplay
        segments, digits = settings["segments"], settings["digits"]
        display = StopwatchDisplay(
            segments=segments, 
            digits=digits,
            add_delta_seconds=settings.get('delta', 10),
            callback=callback
        )
        return display