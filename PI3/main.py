import threading
from settings.settings import load_settings
from components.brgb import run_brgb
from components.dpir3 import run_dpir3
from components.dht1 import run_dht1
from components.dht2 import run_dht2
from components.lcd import run_lcd
from components.ir import run_ir

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
        run_dpir3(settings['DPIR3'], threads, stop_event)
        run_dht1(settings['DHT1'], threads, stop_event)
        run_dht2(settings['DHT2'], threads, stop_event)
        run_ir(settings['IR'], threads, stop_event)

        actuator_registry = ActuatorRegistry()
        lcd_actuator = run_lcd(settings['LCD'])
        if lcd_actuator:
            actuator_registry.register('LCD', lcd_actuator)
        rgb_actuator = run_brgb(settings['BRGB'])
        if rgb_actuator:
            actuator_registry.register('BRGB', rgb_actuator)


        console_thread = threading.Thread(target=console_loop, args=(actuator_registry, stop_event))
        console_thread.daemon = False
        console_thread.start()
        threads.append(console_thread)
        
        listener_thread = threading.Thread(target=start_listener, args=(actuator_registry, stop_event))
        listener_thread.daemon = False
        listener_thread.start()
        threads.append(listener_thread)

        while not stop_event.is_set():
            time.sleep(1)

    except KeyboardInterrupt:
        print('\nKeyboard interrupt - stopping app')
        stop_event.set()
    
    finally:
        stop_event.set()
        for t in threads:
            t.join()
                
        cleanup_gpio()
        
        print("App stopped")