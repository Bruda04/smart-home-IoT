class LCDSimulator:
    def __init__(self, callback):
        self.callback = callback

    def display(self, text):
        print(f"LCD: {text}")
        self.callback(text)
    
    def clear(self):
        self.callback("")
    