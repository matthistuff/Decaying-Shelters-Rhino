from BaseHTTPServer import HTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler
from urlparse import urlparse, parse_qs
import json

from grid import solver, grid_modifiers
from shelter import plan_modifiers, hull_modifiers
from util import osmutil, geoutil, rsutil


class DSServer(HTTPServer):
    def __init__(self):
        HTTPServer.__init__(self, ('192.168.178.50', 8080), DSRequestHandler)

        self.osm = osmutil.OSMData()


class DSRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        args = parse_qs(urlparse(self.path).query)
        message = dict()
        do_exit = False

        if args.has_key('method'):
            method = args.get('method')[0]
            message['method'] = method
            if method == 'exit':
                do_exit = True
                message['response'] = 'ok'
            elif method == 'checkPosition':
                lat = float(args.get('lat')[0])
                lon = float(args.get('lon')[0])

                self.server.osm.load_data(lat, lon, 200)
                self.server.osm.process_data()

                rsutil.rdnd()

                solver_instance = solver.GridSolver(lat, lon)
                solver_instance.add_modifier(grid_modifiers.ShadowModifier)
                solver_instance.add_modifier(grid_modifiers.StreetModifier)
                solver_instance.run()
                result = solver_instance.get_results()

                message['response'] = [{'lat': geoutil.y2lat(r.y), 'lon': geoutil.x2lon(r.x), 'score': r.score} for r in
                                       result]
            elif method == 'createShelter':
                lat = float(args.get('lat')[0])
                lon = float(args.get('lon')[0])

                shelter = shelter.Shelter(lat, lon)
                shelter.plan.add_modifier(plan_modifiers.WindModifier)
                shelter.plan.add_modifier(plan_modifiers.SunPlanModifier)
                shelter.hull.add_modifier(hull_modifiers.SunHullModifier, 1)
                shelter.hull.add_modifier(hull_modifiers.BuildingShapeModifier, 4)
                shelter.create()

                rsutil.look_at(rsutil.create_point(geoutil.lon2x(lon), geoutil.lat2y(lat), 2), (10, 20, 3))
                rsutil.rdnd()

            elif method == 'test':
                message['response'] = 'test'

            self.send_headers()
            self.wfile.write(json.dumps(message))

            rsutil.rdnd()

            if do_exit:
                try:
                    self.server.socket.close()
                except:
                    pass


    def send_headers(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()