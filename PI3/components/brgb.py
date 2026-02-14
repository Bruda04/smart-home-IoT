from simulators.brgb import RGB_LEDSimulator
import json
import time
import threading
import paho.mqtt.publish as publish # type: ignore
import settings.broker_settings as broker_settings

brgb_batch = []
publish_data_counter = 0
publish_data_limit = 1
counter_lock = threading.Lock()

def publisher_task(event, brgb_batch, hostname='localhost', port=1883):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_brgb_batch = brgb_batch.copy()
            publish_data_counter = 0
            brgb_batch.clear()
        publish.multiple(local_brgb_batch, hostname=hostname, port=port)
        print(f'[PUBLISH][BRGB] {publish_data_limit} values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(
    target=publisher_task, 
    args=(publish_event, brgb_batch, broker_settings.HOSTNAME, broker_settings.PORT)
)
publisher_thread.daemon = True
publisher_thread.start()

def brgb_callback(value, publish_event, settings):
    global publish_data_counter, publish_data_limit
    is_on = value[3]
    color = (value[0], value[1], value[2])
    print(f"[BRGB] Color: {color}, On: {is_on}")
    payload = {
        "measurement": "BRGB",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": {
            "red": value[0],
            "green": value[1],
            "blue": value[2],
            "is_on": value[3]
        },
        "timestamp": time.time_ns()
    }
    with counter_lock:
        brgb_batch.append(('BRGB', json.dumps(payload), 0, True))
        publish_data_counter += 1
    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_brgb(settings):
        if settings['simulated']:
            print("Starting RGB LED simulator")
            simulator = RGB_LEDSimulator(brgb_callback)
            print("RGB LED simulator started")
            return simulator
        else:
            from actuators.RGBLed import RGB_LED
            rgb_led = RGB_LED(
                settings['red_pin'],
                settings['green_pin'],
                settings['blue_pin'],
                brgb_callback
            )
            return rgb_led


            