import random
from datetime import date
import math

import rhinoscript as rs

import Rhino as r

from animation import camera, loop
from grid import solver, grid_modifiers
from shelter import hull_modifiers, plan_modifiers, shelter
from util import rsutil, osmutil


class DSSim(object):
    def __init__(self):
        rsutil.nd()

        self.cam = camera.Camera()
        self.osm = osmutil.OSMData()
        self.loop = loop.Loop(30)
        self.loop.add_callback(self.cam.update_tween)

        self.shelters = []
        self.text = []

        self.text_height = 3.5

        #
        # WEIMAR
        #
        self.top = 50.9922
        self.left = 11.3063
        self.bottom = 50.9701
        self.right = 11.3415

        #
        # ROSTOCK
        #
        #self.top = 54.1077
        #self.left = 12.0656
        #self.bottom = 54.0625
        #self.right = 12.1511

        self.run_once()

    def run_once(self):
        # Safety net
        self.loop.stop()

        if len(self.shelters) > 30:
            self.reset()

        self.lat, self.lon = self.random_coord()
        self.date = self.random_date()

        coords = rsutil.geoutil.latlon2coord(self.lat, self.lon)
        self.position = rsutil.create_point(coords[0], coords[1])
        self.cam.pan_to(self.position, distance=200, hop=150, tween_type=self.cam.tweener.IN_OUT_CUBIC,
                        on_complete=self.load_data)
        self.loop.start()

    def reset(self):
        [s.dispose() for s in self.shelters]
        self.shelters = []
        [rs.object.DeleteObject(t) for t in self.text]
        self.text = []
        self.osm.dispose()

    def load_data(self):
        self.loop.stop()
        self.osm.load_data(self.lat, self.lon, 200)
        self.osm.process_data(None, True, True, self.create_text)

        rs.utility.Sleep(800)

        self.cam.pan_to(self.position, distance=30, hop=20, on_complete=self.create_grid)
        self.loop.start()

    def create_grid(self):
        self.loop.stop()

        objects = self.osm.get_buildings_in_radius(self.position, simple=False)
        self.solver_instance = solver.GridSolver(self.position, date=self.date, objects=[o.rsobject for o in objects])
        self.solver_instance.add_modifier(grid_modifiers.ShadowModifier, 2)
        self.solver_instance.add_modifier(grid_modifiers.StreetModifier)
        self.solver_instance.run()
        self.solver_instance.display_results()

        rs.utility.Sleep(800)

        best_results = self.solver_instance.get_results(treshold=0.8)
        if len(best_results) > 0:
            self.position = random.choice(best_results).position
            self.cam.pan_to(self.position, distance=10, on_complete=self.create_shelter)
            self.loop.start()
        else:
            self.solver_instance.dispose()
            self.run_once()

    def create_shelter(self):
        self.loop.stop()

        shelter_instance = shelter.Shelter(self.position, start=self.date)
        self.shelters.append(shelter_instance)

        #
        # Modifiers for the plan
        #
        #shelter_instance.plan.add_modifier(plan_modifiers.WindModifier)
        shelter_instance.plan.add_modifier(plan_modifiers.SunPlanModifier)

        #
        # Modifiers for the hull
        #
        shelter_instance.hull.add_modifier(hull_modifiers.SunHullModifier, 1)
        shelter_instance.hull.add_modifier(hull_modifiers.BuildingShapeModifier, 3)
        shelter_instance.hull.add_modifier(hull_modifiers.SphericalHullModifier)

        #
        # Modifiers for the hull coloring
        #
        #shelter_instance.color.add_modifier(color_modifiers.HeightModifier)
        #shelter_instance.color.add_modifier(color_modifiers.SunColorModifier)

        shelter_instance.create()
        rsutil.rdnd()

        self.solver_instance.dispose()

        self.circle_shelter()

    def circle_shelter(self):
        self.cam.circle_position(cycles=1.5, duration=12, tween_type=self.cam.tweener.LINEAR,
                                 on_complete=self.after_circle_shelter)
        self.loop.start()

    def after_circle_shelter(self):
        self.loop.stop()
        self.run_once()

    def create_text(self, osm_object):
        skinny_chars = ['i', 'l', 't', 'j', 'f', 'r']
        wide_chars = ['m', 'w']

        if osm_object.tags.has_key('name'):
            name = list(osm_object.tags['name'].lower())
            curve_length = osm_object.curve.GetLength()
            current_position = self.text_height * 2
            name_index = 0

            while current_position < curve_length:
                rc, t = osm_object.curve.LengthParameter(current_position)
                rc, plane = osm_object.curve.FrameAt(t)

                if plane.ZAxis.Z < 0:
                    plane.Rotate(math.pi, plane.XAxis)

                self.text.append(
                    rs.geometry.AddText(name[name_index], plane, self.text_height, 'Alte DIN 1451 Mittelschrift'))

                if name[name_index] in skinny_chars:
                    current_position += self.text_height * 0.5
                elif name[name_index] in wide_chars:
                    current_position += self.text_height * 1.2
                else:
                    current_position += self.text_height * 0.8

                name_index += 1
                if not name_index < len(name):
                    name_index = 0
                    current_position += self.text_height * 20


    def random_coord(self):
        return random.uniform(self.top, self.bottom), random.uniform(self.left, self.right)

    def random_date(self):
        start_date = date.today().replace(day=1, month=1).toordinal()
        end_date = date.today().replace(day=31, month=12).toordinal()
        return date.fromordinal(random.randint(start_date, end_date))