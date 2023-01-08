from numbers import Number

class Object():
    def __init__(self, coordinate: list[int]):
        self.coordinate = coordinate

class CoordinateSystem():
    def __init__(self, dimension: int):
        self.dimension = dimension

    def at_coordinate(coordinate: list[int]) -> Object:
        pass

class GravityModel():
    def __init__(self, coordinate_system: CoordinateSystem, objects: list[Object] = []):
        self.coordinate_system = coordinate_system
        self.objects = objects

    def step(delta: Number):
        pass

class ModelRunner():
    def __init__(self, model: GravityModel):
        self.model = model

    def run(self, num_steps: int, delta: Number):
        for _ in range(num_steps):
            self.model.step(delta)