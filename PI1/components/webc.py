import threading

def run_webc(settings, threads, stop_event):
    if settings.get('simulated', True):
        return
    else:
        from sensors.WebCam import WebCam
        print("Starting WEBC sensor")
        web_cam = WebCam(stop_event=stop_event)

        sensor_thread = threading.Thread(target=web_cam.start_stream)
        sensor_thread.start()
        threads.append(sensor_thread)