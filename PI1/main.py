
import threading
from settings.settings import load_settings
import time

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except:
    pass


if __name__ == "__main__":
    print('Starting app')
    settings = load_settings()
    threads = []
    stop_event = threading.Event()
    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print('Stopping app')
        for t in threads:
            stop_event.set()
        try:
            GPIO.cleanup()
        except:
            pass
