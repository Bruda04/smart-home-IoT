class DBSimulator:
    def __init__(self, callback):
        self.callback = callback

    def on(self):
        self.callback(True)
    
    def off(self):
        self.callback(False)
    