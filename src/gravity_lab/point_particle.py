from gravity_model import Object

class PointParticle(Object):
    # mass in kg units
    def __init__(self, coordinate: list[int], mass: float):
        super().__init__(coordinate)
        self.mass = mass