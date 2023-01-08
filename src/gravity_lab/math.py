from math import sqrt
from numbers import Number

class Vector():
    def __init__(self, components: list[Number] = []):
        if type(components) == str:
            components = [float(cmp_str) for cmp_str in components.split(',')]
        self.components = components
        self.dimension = len(components)

    def magnitude(self):
        return sqrt(sum(i*i for i in self.components))

    def __add__(self, other_vector):
        if self.dimension != other_vector.dimension:
            raise ValueError("Dimensions of vectors do not match")
        return Vector([self.components[i] + other_vector.components[i] for i in range(self.dimension)])

    def __sub__(self, other_vector):
        if self.dimension != other_vector.dimension:
            raise ValueError("Dimensions of vectors do not match")
        return Vector([self.components[i] - other_vector.components[i] for i in range(self.dimension)])

    def __mul__(self, scalar: Number):
        return Vector([self.components[i] * scalar for i in range(self.dimension)])

    def __truediv__(self, scalar: Number):
        return Vector([self.components[i] / scalar for i in range(self.dimension)])

    def __neg__(self):
        return self.__mul__(-1)

    def __str__(self) -> str:
        return "<" + ", ".join([str(cmp) for cmp in self.components]) + ">"

    def __getitem__(self, i: int):
        return self.components[i]