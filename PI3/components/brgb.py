from simulators.brgb import RGB_LEDSimulator

def brgb_callback(is_on, color):
    pass

def run_brgb(settings):
        if settings['simulated']:
            print("Starting RGB LED simulator")
            simulator = RGB_LEDSimulator(brgb_callback)
            print("RGB LED simulator started")
            return simulator
        else:
            from actuators.RGBLed import RGB_LED
            rgb_led = RGB_LED(
                settings['red_pin'],
                settings['green_pin'],
                settings['blue_pin']
            )
            return rgb_led


            