class RGB_LEDSimulator:
    def __init__(self, callback):
        self.callback = callback
        self.current_color = [0, 0, 0]
        self.is_on = False
    def on(self):
        self.is_on = True
        self.callback((self.is_on, self.current_color[0], self.current_color[1], self.current_color[2]))

    def off(self): 
        self.is_on = False
        self.callback((self.is_on, self.current_color[0], self.current_color[1], self.current_color[2]))

    def set_color(self, r, g, b):
        self.current_color = [r, g, b]
        self.callback((self.is_on, r, g, b))
