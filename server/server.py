from flask import Flask, jsonify, request
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import paho.mqtt.client as mqtt
import json
from settings.settings import load_settings


app = Flask(__name__)

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
    for topic in mqtt_topics:
        client.subscribe(topic)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = lambda client, userdata, msg: save_to_db(json.loads(msg.payload.decode('utf-8')))


def save_to_db(data):
    write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
    point = (
        Point(data["measurement"])
        .tag("simulated", data["simulated"])
        .tag("runs_on", data["runs_on"])
        .tag("name", data["name"])
        .field("measurement", data["value"])
    )
    write_api.write(bucket=idb_bucket, org=idb_org, record=point)


@app.route('/store_data', methods=['POST'])
def store_data():
    try:
        data = request.get_json()
        store_data(data)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=False)
