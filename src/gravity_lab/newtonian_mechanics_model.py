from gravity_lab.cartesian_coordinate_system import CartesianCoordinateSystem
from gravity_lab.gravity_model import GravityModel
from gravity_lab.math import Vector
from gravity_lab.point_particle import PointParticle

gravitational_constant =  6.67430E-11

class NewtonianMechanicsModel(GravityModel):
    def __init__(self, coordinate_system: CartesianCoordinateSystem, objects: list[PointParticle] = []):
        super().__init__(coordinate_system, objects)

    def step(self, delta: float):
        # F = -G * (m1 * m2) / |r|^2 * r>
        # The equation above is the force of gravity between two objects
        # where r is the vector from the object exerting the force to the object experiencing the force,
        # v> is the unit vector of v, |v| is the magnitude of a vector, and m1 and m2 are the masses of the objects
        for object in self.objects:

            # translate object with velocity
            object.coordinate += object.velocity * delta

            G = gravitational_constant
            gravity_force = Vector([0.0] * self.coordinate_system.dimension)
            for other_object in self.objects:
                if object != other_object:
                    r_vec: Vector = object.coordinate - other_object.coordinate
                    r_mag = r_vec.magnitude()
                    r_unit_vec = r_vec / r_mag
                    force = -r_unit_vec * (G * other_object.mass * object.mass / (r_mag*r_mag))

                    gravity_force += force

            # F = ma
            # a = F / m
            # update the velocity of object by the acceleration that is calculated from the force of gravity            
            object.velocity += gravity_force / object.mass * delta