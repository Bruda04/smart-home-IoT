import threading
from simulators.dpir1 import run_dpir1_simulator


def dpir_callback(event):
    print("DPIR1 motion detected")


def run_dpir1(settings, threads, stop_event):
    if settings.get('simulated', True):
        print("Starting DPIR1 simulator")
        dpir_thread = threading.Thread(target=run_dpir1_simulator, args=(settings.get('poll_delay', 1), dpir_callback, stop_event))
        dpir_thread.start()
        threads.append(dpir_thread)
        print("DPIR1 simulator started")
    else:
        from PI1.sensors.PIRSensor import PIRSensor
        print("Starting DPIR1 PIR sensor")
        pir = PIRSensor(pin=settings['pin'], callback=dpir_callback, bouncetime=settings.get('bouncetime', 200))
