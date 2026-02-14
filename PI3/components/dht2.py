import json
import time
import threading
import paho.mqtt.publish as publish  # type: ignore
import settings.broker_settings as broker_settings
from simulators.dht2 import run_dht2_simulator

dht2_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()

def publisher_task(event, dht2_batch, hostname='localhost', port=1883):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_batch = dht2_batch.copy()
            publish_data_counter = 0
            dht2_batch.clear()
        publish.multiple(local_batch, hostname=hostname, port=port)
        print(f'[PUBLISH][DHT2] {publish_data_limit} values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(
    target=publisher_task,
    args=(publish_event, dht2_batch, broker_settings.HOSTNAME, broker_settings.PORT)
)
publisher_thread.daemon = True
publisher_thread.start()


def dht2_read_callback(humidity, temperature, publish_event, settings):
    global publish_data_counter, publish_data_limit
    print(f'[DHT2] Temperature: {temperature}°C, Humidity: {humidity}%')

    temp_payload = {
        "measurement": "DHT2-Temperature",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": temperature,
        "timestamp": time.time_ns()
    }

    humidity_payload = {
        "measurement": "DHT2-Humidity",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": humidity,
        "timestamp": time.time_ns()
    }

    with counter_lock:
        dht2_batch.append(('DHT2-Temperature', json.dumps(temp_payload), 0, True))
        dht2_batch.append(('DHT2-Humidity', json.dumps(humidity_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_dht2(settings, threads, stop_event):
    if settings.get('simulated', True):
        print("Starting DHT2 simulator")
        dht2_thread = threading.Thread(
            target=run_dht2_simulator,
            args=(settings.get('poll_delay', 1), dht2_read_callback, stop_event, publish_event, settings)
        )
        dht2_thread.start()
        threads.append(dht2_thread)
        print("DHT2 simulator started")
    else:
        from sensors.DHT import DHT, parseCheckCode

        def run_dht_loop(dht, delay, callback, stop_event, publish_event, settings):
                while not stop_event.is_set():
                    check = dht.readDHT11()
                    code = parseCheckCode(check)
                    if code != "DHTLIB_OK":
                        print(f'[DHT2] Read error: {code}')
                        continue
                    humidity, temperature = dht.humidity, dht.temperature
                    callback(humidity, temperature, publish_event, settings)
                    time.sleep(delay)

        print("Starting dht2 sensor")
        dht = DHT(settings['pin'])
        dht2_thread = threading.Thread(target=run_dht_loop, args=(dht, settings.get('poll_delay', 2), dht2_read_callback, stop_event, publish_event, settings))
        dht2_thread.start()
        threads.append(dht2_thread)
