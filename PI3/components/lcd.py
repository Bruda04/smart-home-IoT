from simulators.lcd import LCDSimulator

def lcd_callback(text):
    print(f"[LCD] {text}")

def run_lcd(settings):
        if settings['simulated']:
            print("Starting LCD simulator")
            simulator = LCDSimulator(lcd_callback)
            print("LCD simulator started")
            return simulator
        else:
            from actuators.LCD import LCD
            lcd = LCD()
            return lcd


            