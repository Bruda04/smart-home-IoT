from simulators.db import DBSimulator

import json
import time
import threading
import paho.mqtt.publish as publish # type: ignore
import settings.broker_settings as broker_settings


db_batch = []
publish_data_counter = 0
publish_data_limit = 2
counter_lock = threading.Lock()

def publisher_task(event, db_batch, hostname='localhost', port=1883):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_db_batch = db_batch.copy()
            publish_data_counter = 0
            db_batch.clear()
        publish.multiple(local_db_batch, hostname=hostname, port=port)
        print(f'[PUBLISH][DB] {publish_data_limit} values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, db_batch, broker_settings.HOSTNAME, broker_settings.PORT))
publisher_thread.daemon = True
publisher_thread.start()

def buzzing_callback(value, publish_event, settings):
    global publish_data_counter, publish_data_limit
    print(f"[DB] {'started buzzing' if value else 'went silent'} - {time.strftime('%H:%M:%S', time.localtime())}")

    db_payload = {
        "measurement": "DB",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": value,
        "timestamp": time.time_ns()
    }

    with counter_lock:
        db_batch.append(('DB', json.dumps(db_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_db(settings):
        def buzz_callback(value):
            buzzing_callback(value, publish_event, settings)

        if settings['simulated']:
            print("Starting DB simulator")
            simulator = DBSimulator(buzz_callback)
            print("DB simulator started")
            return simulator
        else:
            if settings['type'] == 'active':
                from actuators.Buzzer import ActiveBuzzer
                buzzer = ActiveBuzzer(settings['pin'], buzz_callback)
            elif settings['type'] == 'passive':
                from actuators.Buzzer import PassiveBuzzer
                buzzer = PassiveBuzzer(settings['pin'], buzz_callback)

            return buzzer

            