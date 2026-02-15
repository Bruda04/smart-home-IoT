import threading
from settings.settings import load_settings
from components.ds2 import run_ds2
from components.dus2 import run_dus2
from components.dpir2 import run_dpir2
from components.btn import run_btn
from components.dht3 import run_dht3
from components.gsg import run_gsg
from components.sd import run_sd

from console.console import console_loop
from comm.listener import start_listener

from actuators.ActuatorRegistry import ActuatorRegistry
import time

try:
    import RPi.GPIO as GPIO # type: ignore
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
        run_ds2(settings['DS2'], threads, stop_event)
        run_dus2(settings['DUS2'], threads, stop_event)
        run_dpir2(settings['DPIR2'], threads, stop_event)
        run_btn(settings['BTN'], threads, stop_event)
        run_dht3(settings['DHT3'], threads, stop_event)
        run_gsg(settings['GSG'], threads, stop_event)

        actuator_registry = ActuatorRegistry()
        sw_actuator = run_sd(settings['4SD'])
        if sw_actuator:
            actuator_registry.register('SD', sw_actuator)


        console_thread = threading.Thread(target=console_loop, args=(actuator_registry, stop_event))
        console_thread.daemon = False
        console_thread.start()
        threads.append(console_thread)
        
        listener_thread = threading.Thread(target=start_listener, args=(settings['MQTT'], actuator_registry, stop_event))
        listener_thread.daemon = False
        listener_thread.start()
        threads.append(listener_thread)

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