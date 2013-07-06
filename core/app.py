import random
import rhinoscript as rs

from animation import camera
from grid import solver, grid_modifiers
from util import rsutil, osmutil, geoutil
import loop
import time


class DSApp(object):
    def __init__(self):
        rsutil.nd()

        self.cam = camera.Camera()
        self.osm = osmutil.OSMData()
        self.loop = loop.Loop()
        self.loop.add_callback(self.cam.update_tween)

        self.solvers = []

        self.top = 50.9922
        self.left = 11.3063
        self.bottom = 50.9701
        self.right = 11.3415

        self.run_once()

    def run_once(self):
        self.lat, self.lon = self.random_coord()

        coords = rsutil.geoutil.latlon2coord(self.lat, self.lon)
        self.position = rsutil.create_point(coords[0], coords[1])
        self.cam.pan_to(self.position, 200, 150, self.load_data)
        self.loop.run()

    def load_data(self):
        self.loop.stop()
        self.osm.load_data(self.lat, self.lon, 200)
        self.osm.process_data(None, True, True)

        rs.utility.Sleep(800)

        self.cam.pan_to(self.position, 30, 20, self.create_grid)
        self.loop.run()

    def create_grid(self):
        self.loop.stop()

        objects = self.osm.get_buildings_in_radius(self.position, simple=False)
        s = solver.GridSolver(self.position, objects=[o.rsobject for o in objects])
        s.add_modifier(grid_modifiers.ShadowModifier)
        s.add_modifier(grid_modifiers.StreetModifier)
        s.run()
        s.display_results()

        rs.utility.Sleep(800)

        self.solvers.append(s)
        if len(self.solvers) > 25:
            self.solvers.pop(0).dispose()

        best_results = s.get_results(treshold=0.8)
        if len(best_results) > 0:
            self.cam.pan_to(random.choice(best_results).position, 10, on_complete=self.circle_shelter)
            self.loop.run()
        else:
            self.run_once()

    def create_shelter(self):
        self.loop.stop()

        rs.utility.Sleep(800)

        self.run_once()

    def circle_shelter(self):
        self.cam.circle_position(1, self.create_shelter)


    def random_coord(self):
        return random.uniform(self.top, self.bottom), random.uniform(self.left, self.right)