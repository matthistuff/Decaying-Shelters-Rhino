import datetime

import rhinoscript as rs

from util import geoutil, weather, rsutil
from util.sun import SunVector
from shelter import hull, plan, color


class Shelter(object):
    def __init__(self, lat, lon, start=datetime.date.today(), end=None):
        self.lat = lat
        self.lon = lon
        self.start = start
        self.position = rsutil.create_point(*geoutil.latlon2coord(lat, lon))
        self.buildings = rsutil.objects_in_radius(self.position, 150, rs.selection.filter.extrusion)
        self.buildings_nurbs = [o.Geometry.ToNurbsSurface() for o in self.buildings]

        sun = SunVector(lat, lon, self.start)
        self.sun_positions = sun.get_positions()
        self.sun_vectors = [sun.sun_to_vec(p[0], p[1]) for p in self.sun_positions]

        self.forecast = weather.get_forecast(lat, lon, self.start)
        #self.forecast = []

        self.plan = plan.Plan(self)
        self.hull = hull.Hull(self)
        self.color = color.ColoredHull(self)

    def shoot_ray(self, p, v):
        return rs.surface.ShootRay(self.buildings_nurbs, p, v, 1)

    def create(self):
        self.plan.create()
        self.hull.create()
        self.color.create()