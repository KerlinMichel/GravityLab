from gravity_lab.gravity_model import Object
from gravity_lab.math import Vector

class PointParticle(Object):
    # mass in kg units
    def __init__(self, mass: float, coordinate: Vector, velocity: Vector):
        super().__init__(coordinate)
        self.mass = mass
        self.velocity = velocity