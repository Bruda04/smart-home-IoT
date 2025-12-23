from simulators.dl import DLSimulator


def run_dl(settings):
    if settings['simulated']:
        print("Starting DL simulator")
        simulator = DLSimulator()
        print("DL simulator started")
        return simulator
    else:
        from actuators.DoorLight import DoorLight
        dl = DoorLight(settings['pin'])
        return dl
