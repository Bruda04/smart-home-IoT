class ActuatorRegistry:
    def __init__(self):
        self._actuators = {}

    def register(self, name, actuator):
        self._actuators[name] = actuator

    def get(self, name):
        return self._actuators.get(name)

    def list(self):
        return self._actuators.keys()