import threading
import time
import json
import paho.mqtt.publish as publish # type: ignore
import settings.broker_settings as broker_settings

ir_batch = []
publish_data_counter = 0
publish_data_limit = 1
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
        print(f'[PUBLISH][IR] Data sent to MQTT')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, ir_batch, broker_settings.HOSTNAME, broker_settings.PORT))
publisher_thread.daemon = True
publisher_thread.start()

def ir_callback(button_name, publish_event, settings):
    global publish_data_counter
    print(f"[IR] Button: {button_name} pressed")

    payload = {
        "measurement": "IR",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": button_name,
        "timestamp": time.time_ns()
    }

    with counter_lock:
        ir_batch.append(('IR', json.dumps(payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_ir(settings, threads, stop_event):
    if settings['simulated']:
        from simulators.ir import run_ir_simulator
        print("Starting IR simulator")
        def sim_callback(btn):
            ir_callback(btn, publish_event, settings)
        
        simulator = threading.Thread(target=run_ir_simulator, args=(2, sim_callback, stop_event))
        simulator.daemon = True
        simulator.start()
        threads.append(simulator)
    else:
        from sensors.IR import IRReceiver
        print("Starting IR sensor")
        
        def sensor_callback(btn):
            ir_callback(btn, publish_event, settings)

        ir_sensor = IRReceiver(settings['pin'], sensor_callback)
        
        def listen_loop():
            while not stop_event.is_set():
                ir_sensor.listen_once() 
                
        ir_thread = threading.Thread(target=listen_loop)
        ir_thread.start()
        threads.append(ir_thread)
