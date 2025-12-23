class DLSimulator:
    def __init__(self):
        self.is_on = False

    def on(self):
        if not self.is_on:
            self.is_on = True
            print("DL simulator: ON")

    def off(self):
        if self.is_on:
            self.is_on = False
            print("DL simulator: OFF")
