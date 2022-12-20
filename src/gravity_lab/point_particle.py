from gravity_model import Object

class PointParticle(Object):
    # mass in kg units
    def __init__(self, mass: float, coordinate: list[int], velocity: list[int]):
        super().__init__(coordinate)
        self.mass = mass
        self.velocity = velocity