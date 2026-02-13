import json
import time
import threading
import paho.mqtt.publish as publish  # type: ignore
from simulators.gsg import run_gsg_simulator
import settings.broker_settings as broker_settings


gsg_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()


def publisher_task(event, batch, hostname='localhost', port=1883):
    global publish_data_counter
    while True:
        event.wait()
        with counter_lock:
            local_batch = batch.copy()
            publish_data_counter = 0
            batch.clear()

        publish.multiple(local_batch, hostname=hostname, port=port)
        print(f'[PUBLISH][GSG] {publish_data_limit} values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(
    target=publisher_task,
    args=(publish_event, gsg_batch, broker_settings.HOSTNAME, broker_settings.PORT)
)
publisher_thread.daemon = True
publisher_thread.start()


def gsg_callback(publish_event, settings):
    global publish_data_counter

    print("[GSG] Significant movement detected")

    payload = {
        "measurement": "GSG",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": True,
        "timestamp": time.time_ns()
    }

    with counter_lock:
        gsg_batch.append(('GSG', json.dumps(payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_gsg(settings, threads, stop_event):
    if settings.get('simulated', True):
        print("Starting GSG simulator")
        gsg_thread = threading.Thread(target = run_gsg_simulator, args=(settings.get('poll_delay', 0.2), gsg_callback, stop_event, publish_event, settings))
        gsg_thread.start()
        threads.append(gsg_thread)
        print("GSG simulator started")
    else:
        from sensors.Gyroscope import Gyroscope

        print("Starting GSG sensor")
        sensor = Gyroscope(
            accel_threshold_g=settings.get('accel_threshold_g', 0.3),
            gyro_threshold_dps=settings.get('gyro_threshold_dps', 50),
            cooldown_time_s=settings.get('cooldown_time_s', 2)
        )

        def sensor_loop():
            while not stop_event.is_set():
                accel_g, gyro_dps = sensor.get_data()

                if accel_g is not None:
                    if sensor.is_significant_movement(accel_g, gyro_dps):
                        gsg_callback(publish_event, settings)

                time.sleep(settings.get('poll_delay', 0.1))


        thread = threading.Thread(target=sensor_loop)
        thread.start()
        threads.append(thread)
