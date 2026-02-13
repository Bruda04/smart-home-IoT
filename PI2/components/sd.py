from simulators.sd import StopwatchDisplaySimulator

def run_sd(settings):
    def callback(value):
        print(f"[4SD] {value}")

    if settings['simulated']:
        print("Starting 4SD simulator")
        simulator = StopwatchDisplaySimulator(callback)
        return simulator
    else:
        from actuators.SegmentDisplay import StopwatchDisplay
        segments, digits = settings["segments"], settings["digits"]
        display = StopwatchDisplay(
            segments=segments, 
            digits=digits,
            add_delta_seconds=settings.get('delta', 10)
        )
        return display