import math

from cartesian_coordinate_system import CartesianCoordinateSystem
from gravity_model import GravityModel
from point_particle import PointParticle

gravitational_constant =  6.67430E-11

class NewtonianMechanicsModel(GravityModel):
    def __init__(self, coordinate_system: CartesianCoordinateSystem, objects: list[PointParticle]):
        super().__init__(coordinate_system, objects)

    def step(self, delta: float):
        # F = -G * (m1 * m2) / |r|^2 * r>
        # The equation above is the force of gravity between two objects
        # where r is the vector from the object exerting the force to the object experiencing the force,
        # v> is the unit vector of v, |v| is the magnitude of a vector, and m1 and m2 are the masses of the objects
        for object in self.objects:

            # translate object with velocity
            object.coordinate[0] += object.velocity[0] * delta
            object.coordinate[1] += object.velocity[1] * delta
            object.coordinate[2] += object.velocity[2] * delta

            G = gravitational_constant
            gravity_force = [0.0, 0.0, 0.0]
            for other_object in self.objects:
                if object != other_object:
                    r_x = object.coordinate[0] - other_object.coordinate[0]
                    r_y = object.coordinate[1] - other_object.coordinate[1]
                    r_z = object.coordinate[2] - other_object.coordinate[2]

                    r_vec = [r_x, r_y, r_z]
                    r_mag = math.sqrt(sum(i*i for i in r_vec))
                    r_unit_vec = list( i / r_mag for i in r_vec)
                    force = list((G * other_object.mass * object.mass / (r_mag*r_mag)) * -i for i in r_unit_vec)

                    gravity_force[0] += force[0]
                    gravity_force[1] += force[1]
                    gravity_force[2] += force[2]

            # F = ma
            # a = F / m
            # update the velocity of object by the acceleration that is calculated from the force of gravity
            object.velocity[0] += gravity_force[0] / object.mass * delta
            object.velocity[1] += gravity_force[1] / object.mass * delta
            object.velocity[2] += gravity_force[2] / object.mass * delta