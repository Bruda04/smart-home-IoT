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
    "inputed": [],
    "brgb": {
        "is_on": False,
        "color": (255, 255, 255)
    },
    "sw_time": "0000"
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
        "DPIR1": "last_DUS1_values",
        "DPIR2": "last_DUS2_values",
    }

    dus_map = {
        "DUS1": "last_DUS1_values",
        "DUS2": "last_DUS2_values",
    }

    if name in sensor_map and val == True:
        values = saved_vals[sensor_map[name]]
        if len(values) > 1:
            if values[0] > values[-1]:
                state["people_count"] += 1
            else:
                state["people_count"] = max(0, state["people_count"] - 1)
                try:
                    socketio.emit('state_update', state)
                except Exception:
                    pass

    # updating the top 5 measurements
    if name in dus_map:
        last_dus_values = saved_vals[dus_map[name]]
        last_dus_values.append(val)

        if len(last_dus_values) > 5: last_dus_values.pop(0)


# 1. DPIR1 & DL (ligth for 10s)
def turn_on_light_for_10s(name, val):
    if name == "DPIR1" and val == True:
        mqtt_client.publish("commands/PI1/DL", json.dumps({"value": True}))
        Timer(10, lambda: mqtt_client.publish("commands/PI1/DL", json.dumps({"value": False}))).start()
        

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

#8 Stoperica
def extend_sw():
    mqtt_client.publish(
        "commands/PI2/4SD",
        json.dumps({
            "action": "add_seconds"
        })
    )

def update_sw_time(val):
    saved_vals["sw_time"] = val
    socketio.emit('sw_time_update', {"time": val})

def set_sw_time(minutes, seconds):
    saved_vals["sw_time"] = f"{minutes}{seconds}"
    mqtt_client.publish(
        "commands/PI2/SD",
        json.dumps({
            "action": "set_time",
            "minutes": minutes,
            "seconds": seconds
        })
    )

def set_add_seconds(n):
    mqtt_client.publish(
        "commands/PI2/SD",
        json.dumps({
            "action": "set_add_seconds",
            "delta": n
        })
    )

# 9 RGB
def set_color(val):
    saved_vals["brgb"]["color"] = val
    mqtt_client.publish(
        "commands/PI3/BRGB",
        json.dumps({
            "action": "set_color",
            "color": val
        })
    )

def rgb_off():
    saved_vals["brgb"]["is_on"] = False
    mqtt_client.publish(
        "commands/PI3/BRGB",
        json.dumps({
            "action": "off"
        })
    )

def rgb_on():
    saved_vals["brgb"]["is_on"] = True
    mqtt_client.publish(
        "commands/PI3/BRGB",
        json.dumps({
            "action": "on"
        })
    )

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
                    save_event_to_db("DISARMED", "System disarmed by user.")
            else:
                #a
                def arm_alarm():
                    # Alarm armed after 10 seconds!
                    state["armed"] = True
                    save_event_to_db("ARMED", "System armed by user.")
                    socketio.emit('state_update', state)
        
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
            Timer(4, alarm).start()
            

    #5 
    if name.startswith("DPIR") and val == True and state["people_count"] == 0: 
        trigger_alarm(f"{name} detected movement in empty house!")

    #6
    if name == "GSG" and val == True:  
        trigger_alarm(f"{name}")

    #7 update temp and humidity
    if name.startswith("DHT"): 
        update_dht_values(data["measurement"], val)

    #8 stoperica TO DO 
    if name == "BTN" and val == True:
        extend_sw()
    if name == "SD":
        update_sw_time(val)

    #9 BRGB
    if name == "IR":
        button_color_map = {
            "2": (255, 0, 0),  # Red
            "3": (0, 255, 0),  # Green
            "4": (0, 0, 255),  # Blue
            "5": (255, 255, 0),# Yellow
            "6": (255, 0, 255),# Magenta
            "7": (255, 255, 255), # White
            "8": (0, 255, 255), # Cyan
            "9": (255, 165, 0) # Orange
        }
        if val in button_color_map:
            set_color(button_color_map[val])
        elif val == "0":
            rgb_off()
        elif val == "1":
            rgb_on()

        socketio.emit('brgb_update', saved_vals["brgb"])



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

    try:
        socketio.emit('state_update', state)
    except Exception:
        pass

def deactivate_alarm():
    state["alarm_active"] = False
    mqtt_client.publish("commands/PI1/DB", json.dumps({"value": False}))
    mqtt_client.publish("commands/PI1/DL", json.dumps({"value": False}))
    socketio.emit('alarm_stopped', {})
    save_event_to_db("ALARM_STOPPED", "Alarm deactivated by user.")

    try:
        socketio.emit('state_update', state)
    except Exception:
        pass

# --- SOCKET IO ENDPOINTS ---
@socketio.on('connect')
def handle_connect():
    # send current system state when a client connects
    try:
        socketio.emit('state_update', state)
        # also send current stopwatch time so frontends show it immediately
        try:
            socketio.emit('sw_time_update', {"time": saved_vals.get("sw_time", "0000")})
        except Exception:
            pass
    except Exception:
        pass




@socketio.on('deactivate_alarm')
def handle_pin(data):
    if data['pin'] == conf.get("pin", "1234"):
        deactivate_alarm()

@socketio.on('rgb_control')
def brgb(data):
    action = data.get("command")
    if action == "set":
        color = data.get("color")
        set_color(color)
    elif action == "on":
        rgb_on()
    elif action == "off":
        rgb_off()

@socketio.on('sw_command')
def sw(data):
    action = data.get("command")
    if action == "set_add_seconds":
        n = data.get("delta")
        print(f"[SW] Received set_add_seconds -> delta={n}")
        set_add_seconds(n)
    elif action == "set_time":
        minutes = data.get("minutes")
        seconds = data.get("seconds")
        print(f"[SW] Received set_time -> minutes={minutes}, seconds={seconds}")
        set_sw_time(minutes, seconds)

@socketio.on('trigger_scenario')
def handle_scenario(data):
    if data['scenario'] == 'alarm_on':
        print("sc: alarm on")
        process_logic({"name": "GSG", "value": True})
    

    if data["scenario"] == "correct_pin":
        print("sc: correct pin -> arm after 10")
        process_logic({"name": "DMS", "value": "1"})
        process_logic({"name": "DMS", "value": "2"})
        process_logic({"name": "DMS", "value": "3"})
        process_logic({"name": "DMS", "value": "4"})

    if data["scenario"] == "dpir1_detects":
        print("sc: dpir1 -> DL on for 10")
        process_logic({"name": "DPIR1", "value": True})

    if data["scenario"] == "ds12_detected":
        print("sc: ds12 detected -> 20s for pin")
        saved_vals["ds1_pressed"] = False
        saved_vals["ds1_start_time"] = time.time() - 2
        process_logic({"name": "DS1", "value": True})

    if data["scenario"] == "empty_house_movement":
        state["people_count"] = 0
        socketio.emit('state_update', state)
        process_logic({"name": "DPIR1", "value": True})

        

if __name__ == '__main__':
    rotation_thread = threading.Thread(target=lcd_rotation_task)
    rotation_thread.daemon = True
    rotation_thread.start()


    socketio.run(app, debug=False, port=5000, use_reloader=False)