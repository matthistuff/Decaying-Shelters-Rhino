import rhinoscript as rs
import scriptcontext as sc

import Rhino as r
from util import rsutil


class Plan(object):
    def __init__(self, shelter, point_count=16):
        self.shelter = shelter
        self.position = shelter.position
        self.sun_vectors = [rs.pointvector.VectorUnitize(v) for v in shelter.sun_vectors]
        self.sun_positions = shelter.sun_positions
        self.forecast = shelter.forecast
        self.layer_name = 'shelter_plan ' + self.shelter.start.isoformat()

        self.point_count = point_count

        self.max_deviation = 0.4

        self.modifiers = []
        self.points = []

        if not rs.layer.IsLayer(self.layer_name):
            rs.layer.AddLayer(self.layer_name)

    def create(self, ):
        current_layer = rs.layer.CurrentLayer()
        rs.layer.CurrentLayer(self.layer_name)

        self.create_base_curve()

        #self.add_curve()

        self.create_points()

        #self.add_points()

        self.transform_points()

        #self.add_points()

        #self.add_curve()

        rs.layer.CurrentLayer(current_layer)

    def create_base_curve(self):
        self.start = self.position + rsutil.create_point(2, 0)
        self.end = self.position - rsutil.create_point(2, 0)
        self.curve = r.Geometry.Curve.CreateControlPointCurve(rs.utility.coerce3dpointlist([self.start, self.end]), 1)
        self.base_length = self.curve.GetLength()
        self.base_center = rsutil.curve_midpoint(self.curve)

    def create_points(self):
        curve_domain = self.curve.Domain
        step = (curve_domain.Max - curve_domain.Min) / (self.point_count - 1)
        self.points = [self.curve.PointAt(curve_domain.Min + i * step) for i in range(0, self.point_count)]

    def add_points(self):
        rs.geometry.AddPointCloud(self.points)

    def transform_points(self):
        [modifier.solve() for modifier in self.modifiers]
        self.curve = r.Geometry.Curve.CreateControlPointCurve(self.points, 3)

    def add_curve(self):
        sc.doc.Objects.AddCurve(self.curve)

    def add_modifier(self, modifier):
        self.modifiers.append(modifier(self))


class PlanCircular(Plan):
    def create_base_curve(self):
        plane = r.Geometry.Plane.WorldXY
        plane.Origin = self.position
        self.curve = r.Geometry.Circle(plane, 3)
        self.curve = self.curve.ToNurbsCurve()
        self.base_length = self.curve.GetLength()
        self.base_center = self.position