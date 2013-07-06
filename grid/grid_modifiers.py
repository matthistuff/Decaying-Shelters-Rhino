import rhinoscript as rs

import System.Threading.Tasks as tasks
from util.sun import SunVector
from util import rsutil
import Rhino as r


class GridModifier(object):
    def __init__(self, solver, weight=1.0):
        self.solver = solver
        self.length = 1
        self.weight = weight
        self.name = 'default'

    def solve(self):
        def solve_parallel(i):
            self.solve_item(i)

        #tasks.Parallel.ForEach(xrange(self.length), solve_parallel)
        [solve_parallel(i) for i in xrange(self.length)]

    def solve_item(self, i):
        pass

    def add_score(self, sub_box, value):
        sub_box.add_score(value, self.name)


class ShadowModifier(GridModifier):
    def __init__(self, solver, weight=1.0):
        super(ShadowModifier, self).__init__(solver, weight)

        self.name = 'shadows'

        self.sun = SunVector(self.solver.lat, self.solver.lon, self.solver.date)
        self.positions = self.sun.get_positions(60)
        self.vectors = [self.sun.sun_to_vec(alt, azi) for alt, azi in self.positions]

        self.length = len(self.positions)

    def solve_item(self, i):
        alt, azi = self.positions[i]
        if alt < 5:
            [self.add_score(box, 1) for box in self.solver.grid.sub_boxes]
            return

        vector = self.vectors[i]

        outlines = self.generate(vector)

        if len(outlines) > 0:
            self.check(outlines)
        else:
            [self.add_score(box, 1) for box in self.solver.grid.sub_boxes]

    def generate(self, vector):
        outlines = [rsutil.create_shadow(obj, vector) for obj in self.solver.objects]
        outlines = r.Geometry.Curve.CreateBooleanUnion(
            [outline.ToNurbsCurve() for outline in outlines if outline is not None])

        return [outline for outline in outlines if outline.IsValid]

    def check(self, outlines):
        for box in self.solver.grid.sub_boxes:
            differences = [r.Geometry.Curve.CreateBooleanIntersection(box.curve, outline) for outline in outlines]

            #check_curve = box.curve.Duplicate()
            #differences = [r.Geometry.Curve.CreateBooleanIntersection(check_curve, outline) for outline in outlines]
            #check_curve.Dispose()

            real_differences = []
            [real_differences.extend(difference) for difference in differences]

            if len(real_differences) == 0:
                self.add_score(box, 1)
                continue

            union_differences = r.Geometry.Curve.CreateBooleanUnion(real_differences)
            if len(union_differences) == 0:
                union_differences = real_differences

            sun_area = box.area
            for difference in union_differences:
                mp = r.Geometry.AreaMassProperties.Compute(difference)
                sun_area -= mp.Area

            self.add_score(box, min(1, max(0, sun_area / box.area)))


class StreetModifier(GridModifier):
    def __init__(self, solver, weight=1.0):
        super(StreetModifier, self).__init__(solver, weight)

        self.name = 'streets'
        self.streets = [street.Geometry for street in
                        rsutil.objects_in_radius(solver.position, 80, rs.selection.filter.curve, False)]
        self.length = len(self.streets)

        if self.length == 0:
            [self.add_score(box, 1) for box in self.solver.grid.sub_boxes]

    def solve_item(self, i):
        street = self.streets[i]

        for box in self.solver.grid.sub_boxes:
            rc, t = street.ClosestPoint(box.position, box.size / 2.0)
            if not rc:
                self.add_score(box, 1)
