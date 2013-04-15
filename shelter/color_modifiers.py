import rhinoscript as rs

import Rhino as r
import System.Threading.Tasks as tasks


class ColorModifier(object):
    def __init__(self, color, strength=1):
        self.color = color
        self.shelter = self.color.shelter
        self.strength = float(strength)

    def solve(self):
        def solve_parallel(i):
            self.solve_item(i)

        tasks.Parallel.ForEach(xrange(self.color.vertex_count), solve_parallel)
        #[solve_parallel(i) for i in xrange(self.color.vertex_count)]

    def shoot_ray(self, p, v):
        return self.shelter.shoot_ray(p, v)

    def solve_item(self, i):
        pass

    def incremented_power(self, value):
        return value * self.strength

    def set_color(self, index, r, g=None, b=None):
        if g is None:
            g = r
        if b is None:
            b = r
        self.color.mesh.VertexColors.SetColor(index, r, g, b)


class HeightModifier(ColorModifier):
    def solve_item(self, i):
        vertex = self.color.vertices[i]

        color = 255

        if vertex.Z <= 2:
            color = 0

        self.set_color(i, color, color, color)


class SunColorModifier(ColorModifier):
    def solve_item(self, i):
        vertex = self.color.vertices[i]

        color = 0
        increment = 255.0 / len(self.shelter.sun_vectors)

        for iv in range(len(self.shelter.sun_vectors)):
            v = self.shelter.sun_vectors[iv]
            reflections = self.shoot_ray(vertex, v)

            if reflections is None:
                continue

            color += increment * 2

        self.set_color(i, min(255, color))
