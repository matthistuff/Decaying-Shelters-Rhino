import math
import rhinoscript as rs
import Rhino as r
import System.Threading.Tasks as tasks


class HullModifier(object):
    def __init__(self, hull, strength=1):
        self.hull = hull
        self.strength = float(strength)
        self.increment = self.hull.max_deviation / self.hull.section_count

    def solve(self):
        def solve_parallel(i):
            self.solve_item(i)

        tasks.Parallel.ForEach(xrange(self.hull.section_count), solve_parallel)
        #[solve_parallel(i) for i in xrange(self.hull.section_count)]

    def solve_item(self, i):
        pass

    def shoot_ray(self, p, v):
        return self.hull.shelter.shoot_ray(p, v)

    def incremented_power(self, value):
        return value * self.increment * self.strength

    def section_points(self, section_index):
        section = self.hull.sections[section_index]
        step = (section.Domain.Max - section.Domain.Min) / (self.hull.section_count - 1)
        return [section.PointAt(ipc * step) for ipc in range(0, self.hull.section_count)]


class SunHullModifier(HullModifier):
    def solve(self):
        self.increment = self.hull.max_deviation / len(self.hull.sun_vectors)

        super(SunHullModifier, self).solve()

    def solve_item(self, i):
        section_base = rs.transformation.XformCPlaneToWorld((0, 0, 0), self.hull.planes[i])
        section_points = self.section_points(i)

        for iv in range(len(self.hull.sun_vectors)):
            v = self.hull.sun_vectors[iv]
            v_transform = r.Geometry.Vector3d(v)
            v_transform.Y = -v_transform.Y
            v_transform.X = -v_transform.X

            alt, azi = self.hull.sun_positions[iv]

            if alt < 0:
                continue

            power = min(1, alt / 90) # General power based on altitude 90 = max power
            power = math.cos(power * math.pi / 2) # Favor obtuse angles
            #power = math.sin(power * math.pi / 2) # Favor acute angles

            test_point = section_base + v * 100

            distances = [rs.utility.Distance(p, test_point) for p in section_points]
            min_distance = min(distances, key=int)
            max_distance = max(distances, key=int)
            distance_delta = max_distance - min_distance

            if distance_delta == 0:
                continue

            for ip in range(self.hull.section_count):
                p = section_points[ip]

                on_ground = (ip == 0) or (ip == self.hull.section_count - 1)

                p_distance = distances[ip]
                rel_distance = (p_distance - min_distance) / distance_delta

                p_mag = rel_distance

                reflections = self.shoot_ray(p, v)

                if reflections is not None:
                    continue

                p_new = p + v_transform * self.incremented_power(power * p_mag)
                if on_ground:
                    p_new.Z = 0
                section_points[ip] = p_new

        self.hull.sections[i] = r.Geometry.Curve.CreateControlPointCurve(section_points, 3)


class BuildingShapeModifier(HullModifier):
    def solve_item(self, i):
        section_base = rs.transformation.XformCPlaneToWorld((0, 0, 0), self.hull.planes[i])
        section_points = self.section_points(i)

        directions = [None] * self.hull.section_count
        sides = [None] * self.hull.section_count
        distances_left = [None] * self.hull.section_count
        distances_right = [None] * self.hull.section_count

        for ip in range(self.hull.section_count):
            p = section_points[ip]
            p_plane = rs.transformation.XformWorldToCPlane(p, self.hull.planes[i])
            sides[ip] = p_plane.X <= 0

            direction = rs.pointvector.VectorCreate(p, section_base)
            direction.Unitize()

            reflections = self.shoot_ray(p, direction)

            if reflections is None:
                continue

            directions[ip] = rs.pointvector.VectorCreate(reflections[1], p)
            if sides[ip]:
                distances_left[ip] = rs.utility.Distance(reflections[1], p)
            else:
                distances_right[ip] = rs.utility.Distance(reflections[1], p)

        try:
            min_distance_left = min(d for d in distances_left if d is not None)
        except:
            min_distance_left = 0
        try:
            min_distance_right = min(d for d in distances_right if d is not None)
        except:
            min_distance_right = 0

        for ip in range(self.hull.section_count):
            p = section_points[ip]

            if directions[ip] is None:
                continue

            direction = directions[ip]
            if sides[ip]:
                distance = distances_left[ip]
                min_distance = min_distance_left
            else:
                distance = distances_right[ip]
                min_distance = min_distance_right

            p_new = p + direction * self.incremented_power(1 - min_distance / distance)
            section_points[ip] = p_new

        self.hull.sections[i] = r.Geometry.Curve.CreateControlPointCurve(section_points, 3)


class SphericalHullModifier(HullModifier):
    def solve_item(self, i):
        radius = 3.0
        section_points = self.section_points(i)

        for ip in range(self.hull.section_count):
            p = section_points[ip]
            dist = rs.utility.Distance(p, self.hull.center)
            if dist < radius:
                v = rs.pointvector.VectorCreate(p, self.hull.center)
                v.Unitize()
                dist_mag = radius - dist

                p_new = p + v * dist_mag
                section_points[ip] = self.hull.planes[i].ClosestPoint(p_new)

        self.hull.sections[i] = r.Geometry.Curve.CreateControlPointCurve(section_points, 3)