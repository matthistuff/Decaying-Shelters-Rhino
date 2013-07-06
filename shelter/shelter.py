import datetime

import rhinoscript as rs

from util import geoutil, weather, rsutil
from util.sun import SunVector
import hull
import plan
import color


class Shelter(object):
    def __init__(self, position_or_lat, lon=None, start=datetime.date.today(), end=None):
        self.start = start

        if lon is not None:
            self.lat = position_or_lat
            self.lon = lon
            x, y = geoutil.latlon2coord(self.lat, self.lon)
            self.position = rsutil.create_point(x, y, 0)
        else:
            self.position = rs.utility.coerce3dpoint(position_or_lat)
            self.lat, self.lon = geoutil.coord2latlon(self.position.X, self.position.Y)

        self.buildings = rsutil.objects_in_radius(self.position, 150, rs.selection.filter.extrusion)
        self.buildings_nurbs = [o.Geometry.ToNurbsSurface() for o in self.buildings]

        sun = SunVector(self.lat, self.lon, self.start)
        self.sun_positions = sun.get_positions(60)
        self.sun_vectors = [sun.sun_to_vec(p[0], p[1]) for p in self.sun_positions]

        self.forecast = weather.get_forecast(self.lat, self.lon, self.start)
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