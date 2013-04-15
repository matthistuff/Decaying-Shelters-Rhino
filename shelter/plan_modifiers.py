import math
import rhinoscript as rs
import Rhino as r
import System.Threading.Tasks as tasks
from util import weather


class PlanModifier(object):
    def __init__(self, plan):
        self.plan = plan

    def solve(self):
        def solve_parallel(i):
            self.solve_item(i)

        tasks.Parallel.ForEach(xrange(self.get_count()), solve_parallel)
        #[solve_parallel(i) for i in xrange(self.get_count())]

    def get_count(self):
        return self.plan.point_count

    def solve_item(self, i):
        pass


class WindModifier(PlanModifier):
    def get_count(self):
        return 1

    def solve_item(self, i):
        self.plan.curve = r.Geometry.Curve.CreateControlPointCurve(self.plan.points, 3)

        wind_dir, speed = weather.mean_wind(self.plan.shelter.forecast)

        wind_strength = min(speed, 50) / 50
        rotation = wind_dir - 90
        rotation = math.radians(90 - rotation * wind_strength)

        rc, t = self.plan.curve.NormalizedLengthParameter(0.5)
        curve_midpoint = self.plan.curve.PointAt(t)

        self.plan.curve.Rotate(rotation, r.Geometry.Vector3d.ZAxis, curve_midpoint)
        self.plan.create_points()


class SunPlanModifier(PlanModifier):
    def get_count(self):
        return len(self.plan.sun_vectors)

    def solve_item(self, i):
        v = self.plan.sun_vectors[i]
        # Copy and flatten
        v = r.Geometry.Vector3d(v)
        v.Z = 0
        v.Unitize()

        alt, azi = self.plan.sun_positions[i]
        if alt < 0:
            return

        power = alt / 90 # General power based on altitude 90 = max power
        power = math.cos(power * math.pi / 2) # Favor obtuse angles
        #power = math.sin(power * math.pi / 2) # Favor acute angles

        #center = rsutil.curve_midpoint(self.curve)
        center = self.plan.base_center
        #length = self.curve.GetLength()
        length = self.plan.base_length

        #test_point_scaled = center + v * self.base_length * power
        #rs.curve.AddLine(center, test_point_scaled) # Display helper

        test_point = center + v * length
        distances = [rs.utility.Distance(p, test_point) for p in self.plan.points]
        min_distance = min(distances, key=int)
        max_distance = max(distances, key=int)
        distance_delta = max_distance - min_distance

        if distance_delta == 0:
            return

        for ip in range(self.plan.point_count):
            p = self.plan.points[ip]
            p_distance = distances[ip]
            rel_distance = (p_distance - min_distance) / distance_delta

            # The closer p is to the test point the greater the drag
            p_mag = 1 - rel_distance

            # Sum of sun power, distance from p to the test point and maximum deviation modifier
            p_new = p + v * (p_mag * power * self.plan.max_deviation)

            self.plan.points[ip] = p_new