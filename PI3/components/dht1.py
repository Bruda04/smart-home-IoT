import json
import time
import threading
import paho.mqtt.publish as publish  # type: ignore
import settings.broker_settings as broker_settings
from simulators.dht1 import run_dht1_simulator

dht1_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()

def publisher_task(event, dht1_batch, hostname='localhost', port=1883):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_batch = dht1_batch.copy()
            publish_data_counter = 0
            dht1_batch.clear()
        publish.multiple(local_batch, hostname=hostname, port=port)
        print(f'[PUBLISH][DHT1] {publish_data_limit} values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(
    target=publisher_task,
    args=(publish_event, dht1_batch, broker_settings.HOSTNAME, broker_settings.PORT)
)
publisher_thread.daemon = True
publisher_thread.start()


def dht1_read_callback(humidity, temperature, publish_event, settings):
    global publish_data_counter, publish_data_limit

    temp_payload = {
        "measurement": "DHT1-Temperature",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": temperature,
        "timestamp": time.time_ns()
    }

    humidity_payload = {
        "measurement": "DHT1-Humidity",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": humidity,
        "timestamp": time.time_ns()
    }

    with counter_lock:
        dht1_batch.append(('DHT1-Temperature', json.dumps(temp_payload), 0, True))
        dht1_batch.append(('DHT1-Humidity', json.dumps(humidity_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_dht1(settings, threads, stop_event):
    if settings.get('simulated', True):
        print("Starting DHT1 simulator")
        dht1_thread = threading.Thread(
            target=run_dht1_simulator,
            args=(settings.get('poll_delay', 1), dht1_read_callback, stop_event, publish_event, settings)
        )
        dht1_thread.start()
        threads.append(dht1_thread)
        print("DHT1 simulator started")
    else:
        from sensors.DHT import DHT, parseCheckCode

        def run_dht_loop(dht, delay, callback, stop_event, publish_event, settings):
                while not stop_event.is_set():
                    check = dht.readDHT11()
                    code = parseCheckCode(check)
                    if code != "DHTLIB_OK":
                        print(f'[DHT1] Read error: {code}')
                        continue
                    humidity, temperature = dht.humidity, dht.temperature
                    callback(humidity, temperature, publish_event, settings)
                    time.sleep(delay)

        print("Starting dht1 sensor")
        dht = DHT(settings['pin'])
        dht1_thread = threading.Thread(target=run_dht_loop, args=(dht, settings.get('poll_delay', 2), dht1_read_callback, stop_event, publish_event, settings))
        dht1_thread.start()
        threads.append(dht1_thread)
