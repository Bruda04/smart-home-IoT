class DLSimulator:
    def __init__(self, callback):
        self.callback = callback
        self.is_on = False

    def on(self):
        if not self.is_on:
            self.is_on = True
            print("DL simulator: ON")
            self.callback(True)

    def off(self):
        if self.is_on:
            self.is_on = False
            print("DL simulator: OFF")
            self.callback(False)
