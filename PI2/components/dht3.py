import json
import time
import threading
import paho.mqtt.publish as publish  # type: ignore
import settings.broker_settings as broker_settings
from simulators.dht3 import run_dht3_simulator

dht3_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()

def publisher_task(event, dht3_batch, hostname='localhost', port=1883):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_batch = dht3_batch.copy()
            publish_data_counter = 0
            dht3_batch.clear()
        publish.multiple(local_batch, hostname=hostname, port=port)
        print(f'[PUBLISH][DHT3] {publish_data_limit} values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(
    target=publisher_task,
    args=(publish_event, dht3_batch, broker_settings.HOSTNAME, broker_settings.PORT)
)
publisher_thread.daemon = True
publisher_thread.start()


def dht3_read_callback(humidity, temperature, publish_event, settings):
    global publish_data_counter, publish_data_limit
    print(f'[DHT3] Temperature: {temperature}°C, Humidity: {humidity}%')

    temp_payload = {
        "measurement": "DHT3-Temperature",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": temperature,
        "timestamp": time.time_ns()
    }

    humidity_payload = {
        "measurement": "DHT3-Humidity",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": humidity,
        "timestamp": time.time_ns()
    }

    with counter_lock:
        dht3_batch.append(('DHT3-Temperature', json.dumps(temp_payload), 0, True))
        dht3_batch.append(('DHT3-Humidity', json.dumps(humidity_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_dht3(settings, threads, stop_event):
    if settings.get('simulated', True):
        print("Starting DHT3 simulator")
        dht3_thread = threading.Thread(
            target=run_dht3_simulator,
            args=(settings.get('poll_delay', 1), dht3_read_callback, stop_event, publish_event, settings)
        )
        dht3_thread.start()
        threads.append(dht3_thread)
        print("DHT3 simulator started")
    else:
        from sensors.DHT import DHT, parseCheckCode

        def run_dht_loop(dht, delay, callback, stop_event, publish_event, settings):
                while not stop_event.is_set():
                    check = dht.readDHT11()
                    code = parseCheckCode(check)
                    if code != "DHTLIB_OK":
                        print(f'[DHT3] Read error: {code}')
                        continue
                    humidity, temperature = dht.humidity, dht.temperature
                    callback(humidity, temperature, publish_event, settings)
                    time.sleep(delay)

        print("Starting dht3 sensor")
        dht = DHT(settings['pin'])
        dht3_thread = threading.Thread(target=run_dht_loop, args=(dht, settings.get('poll_delay', 2), dht3_read_callback, stop_event, publish_event, settings))
        dht3_thread.start()
        threads.append(dht3_thread)
