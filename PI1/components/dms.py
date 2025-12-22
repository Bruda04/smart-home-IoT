import threading
from simulators.dms import run_dms_simulator


def keypad_callback(key):
    print(f"DMS (keypad) detected key: {key}")


def run_dms(settings, threads, stop_event):
    if 'rows' not in settings or 'cols' not in settings:
        raise ValueError("DMS requires 'rows' and 'cols' in settings to function as keypad")

    if settings['simulated']:
        print("Starting DMS (keypad) simulator")
        kp_thread = threading.Thread(target=run_dms_simulator, args=(settings.get('poll_delay', 0.2), keypad_callback, stop_event))
        kp_thread.start()
        threads.append(kp_thread)
        print("DMS (keypad) simulator started")
    else:
        #it will scream at the RPi import if i dont do the import here
        from sensors.Keypad import Keypad

        print("Starting DMS keypad sensor")
        kp_sensor = Keypad(rows=tuple(settings.get('rows')), cols=tuple(settings.get('cols')), callback=keypad_callback, poll_delay=settings.get('poll_delay', 0.2))
        sensor_thread = threading.Thread(target=kp_sensor.start_loop, args=(stop_event,))
        sensor_thread.start()
        threads.append(sensor_thread)