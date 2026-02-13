from threading import Timer
import time
from flask import Flask
from flask_socketio import SocketIO
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import paho.mqtt.client as mqtt
import json
from settings.settings import load_settings


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# System state
state = {
    "alarm_active": False,
    "armed": False,
    "people_count": 0,
    "last_dus1_values": [],
    "ds1_start_time": None,
    "inputed": []
}

conf = load_settings()

# InfluxDB Configuration
idb_token = conf["influxdb"]["token"]
idb_org = conf["influxdb"]["org"]
idb_url = conf["influxdb"]["url"]
idb_bucket = conf["influxdb"]["bucket"]
influxdb_client = InfluxDBClient(url=idb_url, token=idb_token, org=idb_org)

# MQTT Configuration
mqtt_host = conf["mqtt"]["host"]
mqtt_port = conf["mqtt"]["port"]
mqtt_topics = conf["mqtt"]["topics"]

mqtt_client = mqtt.Client()
mqtt_client.connect(mqtt_host, mqtt_port, 60)
mqtt_client.loop_start()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        if not flags.get('session present', 0): 
            for topic in mqtt_topics:
                client.subscribe(topic)

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode('utf-8'))
    save_to_db(payload)
    state_changed = process_logic(payload)
    if state_changed:
        socketio.emit('state_update', state)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def save_to_db(data):
    write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
    point = (
        Point(data["measurement"])
        .tag("simulated", data["simulated"])
        .tag("runs_on", data["runs_on"])
        .tag("name", data["name"])
        .field("measurement", data["value"])
        .time(int(data["timestamp"]), WritePrecision.NS)
    )
    write_api.write(bucket=idb_bucket, org=idb_org, record=point)

def save_event_to_db(event_type, reason):
    write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
    point = (
        Point("events")
        .tag("type", event_type)
        .field("reason", reason)
        .time(int(time.time() * 1e9), WritePrecision.NS)
    )
    write_api.write(bucket=idb_bucket, org=idb_org, record=point)

def process_logic(data):
    global state
    name = data['name']
    val = data['value']

    # 1. DPIR1 & DL1 (ligth for 10s)
    if name == "DPIR1" and val == True:
        mqtt_client.publish("commands/PI1/DL", json.dumps({"value": True}))
        Timer(10, lambda: mqtt_client.publish("commands/PI1/DL", json.dumps({"value": False}))).start()
        
        # 2. Entry/Exit (DUS1)
        if len(state["last_dus1_values"]) > 1:
            first = state["last_dus1_values"][0]
            last = state["last_dus1_values"][-1]
            if first > last: # Person approaching (entering)
                state["people_count"] += 1
            else: # Person leaving
                state["people_count"] = max(0, state["people_count"] - 1)

    # 3. DUS1 buffering
    if name == "DUS1":
        state["last_dus1_values"].append(val)
        if len(state["last_dus1_values"]) > 5: state["last_dus1_values"].pop(0)

    # 4. DS1 (Vrata otvorena > 5s)
    if name == "DS1":
        if val == True: # Dugme pritisnuto (vrata otvorena)
            state["ds1_start_time"] = time.time()
        else:
            if state["ds1_start_time"] and (time.time() - state["ds1_start_time"] > 5):
                trigger_alarm("Door left open for more than 5 seconds!")
            state["ds1_start_time"] = None

    # 5. DMS (PIN check)
    if name == "DMS":
        # if alarm is active and enter pressed check last 4 digits
        state["inputed"].append(val)
        if len(state["inputed"]) > 4: state["inputed"].pop(0)
        if ''.join(map(str, state["inputed"])) == conf.get("pin", "1234"): # Primer ispravnog pina
            deactivate_alarm()
            return True

    return False

def trigger_alarm(reason):
    state["alarm_active"] = True
    mqtt_client.publish("commands/PI1/DB", json.dumps({"value": True}))
    mqtt_client.publish("commands/PI1/DL", json.dumps({"value": True}))
    socketio.emit('alarm_triggered', {"reason": reason})
    save_event_to_db("ALARM", reason)

def deactivate_alarm():
    state["alarm_active"] = False
    mqtt_client.publish("commands/PI1/DB", json.dumps({"value": False}))
    mqtt_client.publish("commands/PI1/DL", json.dumps({"value": False}))
    socketio.emit('alarm_stopped', {})
    save_event_to_db("ALARM_STOPPED", "Alarm deactivated by user.")

# --- SOCKET IO ENDPOINTS ---
@socketio.on('deactivate_alarm')
def handle_pin(data):
    if data['pin'] == conf.get("pin", "1234"):
        deactivate_alarm()

@socketio.on('trigger_scenario')
def handle_scenario(data):
    if data['scenario'] == 'entry':
        process_logic({"name": "DUS1", "value": 150})
        process_logic({"name": "DUS1", "value": 50})
        process_logic({"name": "DPIR1", "value": 1})

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, use_reloader=False)