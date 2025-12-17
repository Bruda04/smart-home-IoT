from components.ds1 import button_pressed_callback
from simulators.dus1 import run_dus1_simulator
import threading
import time

def distance_callback(distance):
   print(f"DUS1 distance: {distance:.2f} cm")


def run_dus1(settings, threads, stop_event):
        if settings['simulated']:
            print("Starting DUS1 simulator")
            dus1_thread = threading.Thread(target = run_dus1_simulator, args=(2, distance_callback, stop_event))
            dus1_thread.start()
            threads.append(dus1_thread)
            print("DUS1 simulator started")
        else:
            from sensors.Ultrasonic import Ultrasonic
            print("Starting DUS1 sensor")
            dus1_sensor = Ultrasonic(settings['trigger_pin'], settings['echo_pin'])

            def sensor_loop():
                while not stop_event.is_set():
                    distance = dus1_sensor.get_distance()
                    if distance is not None:
                        distance_callback(distance)
                    time.sleep(1)

            sensor_thread = threading.Thread(target=sensor_loop)
            sensor_thread.start()
            threads.append(sensor_thread)