from threading import Timer
import time
from flask import Flask
from flask_socketio import SocketIO
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import paho.mqtt.client as mqtt
import json
from settings.settings import load_settings
import threading


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# System state
state = {
    "alarm_active": False,
    "armed": False,
    "people_count": 0,
}

saved_vals = {
    "last_DUS1_values": [],
    "last_DUS2_values": [],
    "ds1_pressed": False,
    "ds2_pressed": False,
    "ds1_start_time": None,
    "ds2_start_time": None,
    "dht": {
        "DHT1": {"temp": None, "hum": None},
        "DHT2": {"temp": None, "hum": None},
        "DHT3": {"temp": None, "hum": None},
    },
    "current_dht_index": 0,
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
    process_logic(payload)


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

# 2 When a dpir sees movement, check the distances (a, b)
def process_person_entering(name, val):
    sensor_map = {
        "DPIR1": "last_dus1_values",
        "DPIR2": "last_dus2_values",
    }

    dus_map = {
        "DUS1": "last_dus1_values",
        "DUS2": "last_dus2_values",
    }

    if name in sensor_map and val == True:
        values = saved_vals[sensor_map[name]]
        if len(values) > 1:
            if values[0] > values[-1]:
                state["people_count"] += 1
            else:
                state["people_count"] = max(0, state["people_count"] - 1)

    # updating the top 5 measurements
    if name in dus_map:
        last_dus_values = saved_vals[dus_map[name]]
        last_dus_values.append(val)

        if len(last_dus_values) > 5: last_dus_values.pop(0)


# 1. DPIR1 & DL1 (ligth for 10s)
def turn_on_light_for_10s(name, val):
    if name == "DPIR1" and val == True:
        mqtt_client.publish("commands/PI1/DL1", json.dumps({"value": True}))
        Timer(10, lambda: mqtt_client.publish("commands/PI1/DL1", json.dumps({"value": False}))).start()
        

#3 DS1/2 (Vrata otvorena > 5s)
def did_i_leave_the_door_open(name, val):
    sensor_map = {
        "DS1": "ds1_start_time",
        "DS2": "ds2_start_time",
    }

    pressed_map = {
        "DS1": "ds1_pressed",
        "DS2": "ds2_pressed",
    }
    
    ds_start_time = sensor_map[name]
    ds_pressed = pressed_map[name]

    saved_vals[ds_pressed] = not saved_vals[ds_pressed]

    if not saved_vals[ds_pressed]:  # Dugme pritisnuto (vrata otvorena) opened
        saved_vals[ds_start_time] = time.time()
    else:  
        if saved_vals[ds_start_time] and (time.time() - saved_vals[ds_start_time] > 5):
            trigger_alarm(f"{name} reported door left open for more than 5 seconds!")
        saved_vals[ds_start_time] = None



# 7 "measurement": "DHT1-Temperature", "measurement": "DHT1-Humidity",
def lcd_rotation_task():
    while True:
        sensors = ["DHT1", "DHT2", "DHT3"]

        current = sensors[saved_vals["current_dht_index"]]
        temp = saved_vals["dht"][current]["temp"]
        hum = saved_vals["dht"][current]["hum"]

        if temp is not None and hum is not None:
            text = f"{current}\nT:{temp:.1f}C H:{hum:.1f}%"

            mqtt_client.publish(
                "commands/PI3/LCD",
                json.dumps({
                    "action": "display",
                    "text": text
                })
            )

        # sledeći senzor
        saved_vals["current_dht_index"] = (saved_vals["current_dht_index"] + 1) % 3

        time.sleep(4)  

def update_dht_values(name, val):
    sensor_name = name.split("-")[0]  # DHT1
    measurement_type = name.split("-")[1]  # Temperature ili Humidity

    if measurement_type == "Temperature":
        saved_vals["dht"][sensor_name]["temp"] = val
    elif measurement_type == "Humidity":
        saved_vals["dht"][sensor_name]["hum"] = val

def update_keyboard_input(val):
    saved_vals["inputed"].append(val)
    if len(saved_vals["inputed"]) > 4: saved_vals["inputed"].pop(0)


def check_pin():
    if ''.join(map(str, saved_vals["inputed"])) == conf.get("pin", "1234"):
        return True
    return False

# consequences to the system from what pi reports
def process_logic(data):
    name = data['name']
    val = data['value']

    #1
    turn_on_light_for_10s(name,val)

    #2 ab
    if name in ["DPIR1", "DUS1","DPIR2", "DUS2"]: process_person_entering(name, val)

    #3
    if name in ["DS1", "DS2"]: did_i_leave_the_door_open(name, val)

    #4
    if name == "DMS":
        update_keyboard_input(val)
        is_pin_correct = check_pin()
        if is_pin_correct:
            if state["armed"]:
                #c 
                if state["alarm_active"]:
                    deactivate_alarm()
                else:
                    state["armed"] = False
            else:
                #a
                def arm_alarm():
                    # Alarm armed after 10 seconds!
                    state["armed"] = True
        
                Timer(10, arm_alarm).start()
    
    #4 b
    if name in ["DS1", "DS2"] and state["armed"]:
        pressed_map = {
            "DS1": "ds1_pressed",
            "DS2": "ds2_pressed",
        }
        ds_pressed = pressed_map[name]
        if saved_vals[ds_pressed]: 
            def alarm():
                trigger_alarm(f"{name} detected door opening while system is armed!")
            Timer(20, alarm).start()
            

    #5 
    if name.startswith("DPIR") and val == True and state["people_count"] == 0: trigger_alarm(f"{name} detected movement in empty house!")

    #6
    if name == "GSG" and val == True:  trigger_alarm(f"{name}")

    #7 update temp and humidity
    if name.startswith("DHT"): update_dht_values(name, val)

    #8 stoperica TO DO 

    #9 TO DO


def display_alarm_state():
    mqtt_client.publish("commands/PI1/DB", json.dumps({"value": True}))
    mqtt_client.publish("commands/PI1/DL", json.dumps({"value": True}))

def trigger_alarm(reason):
    if not state["armed"]: return 

    state["alarm_active"] = True

    # turn on the visuals
    display_alarm_state()
    
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
    rotation_thread = threading.Thread(target=lcd_rotation_task)
    rotation_thread.daemon = True
    rotation_thread.start()


    socketio.run(app, debug=True, port=5000, use_reloader=False)