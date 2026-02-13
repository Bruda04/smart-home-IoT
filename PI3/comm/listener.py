from time import time
import paho.mqtt.client as mqtt
import json

def start_listener(settings, actuator_registry, stop_event):
    hostname = settings.get('hostname', 'localhost')
    port = settings.get('port', 1883)
    
    client = mqtt.Client()

    def on_connect(client, userdata, flags, rc):
        client.subscribe("commands/PI3/#")
        print("[COMM] Listener connected and subscribed to PI3 commands")

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            topic = msg.topic
            
            actuator_name = topic.split('/')[-1].upper()
            actuator = actuator_registry.get(actuator_name)
            
            if actuator:
                if actuator_name == 'LCD':
                    action = payload.get('action', '')
                    if action == 'display':
                        text = payload.get('text', '')
                        actuator.display(text)
                    elif action == 'clear':
                        actuator.clear()
                elif actuator_name == 'BRGB':
                    action = payload.get('action', '')
                    if action == 'set_color':
                        color = payload.get('color', [0, 0, 0])
                        actuator.set_color(*color)
                    elif action == 'on':
                        actuator.on()
                    elif action == 'off':
                        actuator.off()
                    
                print(f"[COMM][{actuator_name}] Command received for {actuator_name}: {payload}")
        except Exception as e:
            print(f"[COMM] Error processing command: {e}")

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(hostname, port, 60)
    
    client.loop_start()
    
    while not stop_event.is_set():
        time.sleep(1)
    
    client.loop_stop()