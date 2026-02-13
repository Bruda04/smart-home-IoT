class RGB_LEDSimulator:
    def __init__(self, callback):
        self.callback = callback
        self.current_color = [0, 0, 0]
        self.is_on = False
    def on(self):
        self.is_on = True
        print(f"RGB LED turned ON ({self.current_color})")
        self.callback(self.is_on, self.current_color)

    def off(self): 
        self.is_on = False
        self.callback(self.is_on, self.current_color)

    def set_color(self, r, g, b):
        self.current_color = [r, g, b]
        print(f"RGB LED color set to ({r}, {g}, {b})")
        self.callback(self.is_on, self.current_color)
