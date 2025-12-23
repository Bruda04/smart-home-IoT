from simulators.db import DBSimulator

def run_db(settings):
        if settings['simulated']:
            print("Starting DB simulator")
            simulator = DBSimulator()
            print("DB simulator started")
            return simulator
        else:
            if settings['type'] == 'active':
                from actuators.Buzzer import ActiveBuzzer
                buzzer = ActiveBuzzer(settings['pin'])
            elif settings['type'] == 'passive':
                from actuators.Buzzer import PassiveBuzzer
                buzzer = PassiveBuzzer(settings['pin'])

            return buzzer

            