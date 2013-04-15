import math
import rhinoscript as rs
import scriptcontext as sc
import Rhino as r
from util import rsutil


class Hull(object):
    def __init__(self, shelter, section_count=16):
        self.shelter = shelter
        self.position = shelter.position
        self.sun_vectors = [rs.pointvector.VectorUnitize(v) for v in shelter.sun_vectors]
        self.sun_positions = shelter.sun_positions
        self.forecast = shelter.forecast
        self.plan = shelter.plan
        self.section_count = section_count
        self.layer_name = 'shelter ' + self.shelter.start.isoformat()

        self.max_deviation = 4.0

        self.modifiers = []

        if not rs.layer.IsLayer(self.layer_name):
            rs.layer.AddLayer(self.layer_name)

    def create(self):
        self.curve = self.plan.curve
        self.length = self.plan.curve.GetLength()
        self.center = rsutil.curve_midpoint(self.plan.curve)

        current_layer = rs.layer.CurrentLayer()
        rs.layer.CurrentLayer(self.layer_name)

        self.create_planes()
        self.create_sections()

        #self.add_sections('raw')

        self.transform_sections()

        #self.add_sections('transformed')

        self.__create_hull_volume()

        rs.layer.CurrentLayer(current_layer)

    def create_planes(self):
        self.planes = []
        curve_domain = self.curve.Domain
        step = (curve_domain.Max - curve_domain.Min) / (self.section_count - 1)

        for i in range(self.section_count):
            rc, plane = self.curve.PerpendicularFrameAt(curve_domain.Min + i * step)
            self.planes.append(plane)

    def create_sections(self):
        self.sections = []
        for i in range(len(self.planes)):
            self.sections.append(self.__create_section_shape(i))

    def add_sections(self, group=None):
        sections_ids = [sc.doc.Objects.AddCurve(section) for section in self.sections]

        if (group is not None):
            rs.group.AddGroup(group)
            rs.group.AddObjectsToGroup(sections_ids, group)


    def __create_section_shape(self, i):
        p1 = rs.transformation.XformCPlaneToWorld((-1.5, 0, 0), self.planes[i])
        p2 = rs.transformation.XformCPlaneToWorld((0, 3, 0), self.planes[i])
        p3 = rs.transformation.XformCPlaneToWorld((1.5, 0, 0), self.planes[i])
        arc = r.Geometry.Arc(p1, p2, p3)
        return arc.ToNurbsCurve()

    def transform_sections(self):
        [modifier.solve() for modifier in self.modifiers]

    def __create_hull_volume(self):
        self.guid = rs.surface.AddLoftSrf(self.sections, None, None, 1)

    def add_modifier(self, modifier, strength=1):
        self.modifiers.append(modifier(self, strength))


class HullRound(Hull):
    def __create_section_shape(self, i):
        radius = 1.5
        plane = r.Geometry.Plane(self.planes[i])
        plane.OriginZ += radius
        circle = r.Geometry.Circle(plane, radius)
        return circle.ToNurbsCurve()

    def __create_hull_volume(self):
        self.guid = rs.surface.AddLoftSrf(self.sections, None, None, 1, 0, 0, True)


class HullClosed(Hull):
    def __create_hull_volume(self):
        self.guid = rs.surface.AddLoftSrf(self.sections, None, None, 1, 0, 0, True)

