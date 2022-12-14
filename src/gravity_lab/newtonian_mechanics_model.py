from cartesian_coordinate_system import CartesianCoordinateSystem
from gravity_model import GravityModel
from point_particle import PointParticle

class NewtonianMechanicsModel(GravityModel):
    def __init__(self, coordinate_system: CartesianCoordinateSystem, objects: list[PointParticle]):
        super().__init__(coordinate_system, objects)

    def step(delta: float):
        pass