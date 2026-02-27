from simulators.dus2 import run_dus2_simulator
import threading
import time
import json
import paho.mqtt.publish as publish # type: ignore
import settings.broker_settings as broker_settings

dus2_batch = []
publish_data_counter = 0
publish_data_limit = 3
counter_lock = threading.Lock()

def publisher_task(event, dus2_batch, hostname='localhost', port=1883):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_dus2_batch = dus2_batch.copy()
            publish_data_counter = 0
            dus2_batch.clear()
        publish.multiple(local_dus2_batch, hostname=hostname, port=port)
        print(f'[PUBLISH][DUS2] {publish_data_limit} values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, dus2_batch, broker_settings.HOSTNAME, broker_settings.PORT))
publisher_thread.daemon = True
publisher_thread.start()


def distance_callback(distance, publish_event, settings):
    global publish_data_counter, publish_data_limit
    print(f"[DUS2] distance: {distance:.2f} cm - {time.strftime('%H:%M:%S', time.localtime())}")

    dus2_payload = {
        "measurement": "DUS2",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": distance,
        "timestamp": time.time_ns()
    }

    with counter_lock:
        dus2_batch.append(('DUS2', json.dumps(dus2_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_dus2(settings, threads, stop_event):
        if settings['simulated']:
            print("Starting DUS2 simulator")
            dus2_thread = threading.Thread(target = run_dus2_simulator, args=(2, distance_callback, stop_event, publish_event, settings))
            dus2_thread.start()
            threads.append(dus2_thread)
            print("DUS2 simulator started")
        else:
            from sensors.Ultrasonic import Ultrasonic
            print("Starting DUS2 sensor")
            dus2_sensor = Ultrasonic(settings['pin'][0], settings['pin'][1])

            def sensor_loop():
                while not stop_event.is_set():
                    distance = dus2_sensor.get_distance()
                    if distance is not None:
                        distance_callback(distance, publish_event, settings)
                    time.sleep(settings.get('poll_delay', 1))

            sensor_thread = threading.Thread(target=sensor_loop)
            sensor_thread.start()
            threads.append(sensor_thread)