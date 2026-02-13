import os

class WebCam:
    def __init__(self, stop_event=None):
        self.stop_event = stop_event
        self.command = 'mjpg_streamer -i "input_uvc.so" -o "output_http.so -p 8080 -w /usr/local/share/mjpg-streamer/www"'
        ip = os.popen('hostname -I').read().strip()
        self.link = f'http://{ip}:8080/?action=stream'

    def start_stream(self):
        os.system(self.command)
        
        print(f'WEBC stream available at: {self.link}')

        while not self.stop_event.is_set():
            pass

        self._stop_stream()

    def _stop_stream(self):
        os.system('pkill mjpg_streamer')