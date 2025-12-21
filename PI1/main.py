import threading
from settings.settings import load_settings
from components.ds1 import run_ds1
from components.db import run_db
from components.dus1 import run_dus1
from components.dms import run_dms

from console.console import console_loop

from actuators.ActuatorRegistry import ActuatorRegistry
import time

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    HAS_GPIO = True
except:
    HAS_GPIO = False


def cleanup_gpio():
    if HAS_GPIO:
        try:
            GPIO.cleanup()
            print("GPIO cleanup completed")
        except Exception as e:
            print(f"GPIO cleanup error: {e}")


if __name__ == "__main__":
    print('Starting app')
    settings = load_settings()
    threads = []
    stop_event = threading.Event()
    try:
        run_ds1(settings['DS1'], threads, stop_event)
        run_dus1(settings['DUS1'], threads, stop_event)
        run_dms(settings['DMS'], threads, stop_event)

        
        actuator_registry = ActuatorRegistry()
        db_actuator = run_db(settings['DB'])
        if db_actuator:
            actuator_registry.register('DB', db_actuator)

        console_thread = threading.Thread(target=console_loop, args=(actuator_registry, stop_event))
        console_thread.daemon = False
        console_thread.start()
        threads.append(console_thread)

        while not stop_event.is_set():
            time.sleep(1)

    except KeyboardInterrupt:
        print('\nKeyboard interrupt - stopping app')
        stop_event.set()
    
    finally:
        for t in threads:
            stop_event.set()
                
        cleanup_gpio()
        
        print("App stopped")