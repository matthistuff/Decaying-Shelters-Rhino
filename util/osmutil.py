import httplib
import urllib
import json
import re

import rhinoscript as rs
import scriptcontext as sc

import Rhino as r
import System.Threading.Tasks as tasks

from util import geoutil, rsutil


class OSMBuilding(object):
    def __init__(self, curve=None, extrusion=None):
        self.curve = None
        self.extrusion = None
        self.id = 0

    def add_to_doc(self):
        self.id = sc.doc.Objects.AddExtrusion(self.extrusion)
        return self.id


class OSMObject(object):
    def __init__(self, curve=None):
        self.curve = curve
        self.id = 0

    def add_to_doc(self):
        self.id = sc.doc.Objects.AddCurve(self.curve)
        return self.id


class OSMData(object):
    def __init__(self):
        self.processed_shapes = dict()

    def load_data(self, lat, lon, radius):
        self.lat = lat
        self.lon = lon
        self.radius = radius

        x, y = geoutil.latlon2coord(self.lat, self.lon)
        offset = self.radius * 5
        rs.view.ViewCameraTarget('Perspective', (x + offset, y - offset, offset), (x, y, 0))

        self.__query_api()
        return self.raw_data

    def process_data(self, raw_data=None, add_to_doc=True, animate=False):
        if raw_data is None:
            raw_data = self.raw_data

        self.add_to_doc = add_to_doc
        self.animate = animate
        self.animate = False

        self.buildings = []
        self.highways = []

        current_layer = rs.layer.CurrentLayer()
        if not rs.layer.IsLayer('osm'):
            rs.layer.AddLayer('osm')
        rs.layer.CurrentLayer('osm')

        self.nodes = [node for node in raw_data['elements'] if node['type'] == 'node']
        self.ways = [node for node in raw_data['elements'] if node['type'] == 'way']

        def solve_parallel(i):
            self.process_way(i)

        tasks.Parallel.ForEach(xrange(len(self.ways)), solve_parallel)
        #[solve_parallel(i) for i in xrange(len(self.ways))]

        if self.add_to_doc is True:
            rs.group.AddGroup('highway')
            rs.group.AddGroup('building')

            if not animate:
                building_ids = [osmobject.add_to_doc() for osmobject in self.buildings]
                rs.group.AddObjectsToGroup(building_ids, 'building')

                highway_ids = [osmobject.add_to_doc() for osmobject in self.highways]
                rs.group.AddObjectsToGroup(highway_ids, 'highway')

            else:
                i = 0
                for osmobject in self.highways:
                    rs.group.AddObjectToGroup(osmobject.add_to_doc(), 'highway')
                    rsutil.rdnd()

                for osmobject in self.buildings:
                    rs.group.AddObjectToGroup(osmobject.add_to_doc(), 'building')
                    if i % 5 is 0:
                        rsutil.rdnd()
                    i += 1

        rs.layer.CurrentLayer(current_layer)


    def process_way(self, i):
        way = self.ways[i]

        if self.processed_shapes.has_key(way['id']):
            return

        self.processed_shapes[way['id']] = True

        curve_points = []
        for way_node in way['nodes']:
            node_item = [node for node in self.nodes if node['id'] == way_node]
            if len(node_item) < 1:
                continue
            node_item = node_item[0]
            x, y = geoutil.latlon2coord(node_item['lat'], node_item['lon'])
            curve_points.append(rsutil.create_point(x, y))

        if len(curve_points) == 0:
            return

        curve = r.Geometry.Curve.CreateControlPointCurve(curve_points, 1)

        if way['tags'].has_key('building'):
            curve.MakeClosed(0)

            building = OSMBuilding(curve)
            self.buildings.append(building)

            height = 12
            min_height = 0
            if way['tags'].has_key('height'):
                # TODO parse units
                height = float(re.sub(r'[^\d.]+', '', way['tags']['height']))
            elif way['tags'].has_key('building:height'):
                # TODO parse units
                height = float(re.sub(r'[^\d.]+', '', way['tags']['building:height']))
            elif way['tags'].has_key('building:levels'):
                height = float(way['tags']['building:levels']) * 3

            if way['tags'].has_key('min_height'):
                # TODO parse units
                min_height = float(re.sub(r'[^\d.]+', '', way['tags']['min_height']))
            elif way['tags'].has_key('building:min_height'):
                # TODO parse units
                min_height = float(re.sub(r'[^\d.]+', '', way['tags']['building:min_height']))
            elif way['tags'].has_key('building:min_level'):
                min_height = float(way['tags']['building:min_level']) * 3

            extrusion = rsutil.create_extrusion(curve, rsutil.create_point(0, 0, min_height),
                                                rsutil.create_point(0, 0, height))
            building.extrusion = extrusion

        elif way['tags'].has_key('highway'):
            self.highways.append(OSMObject(curve))


    def __query_api(self):
        url = "www.overpass-api.de"
        query = "/api/interpreter"

        bbox_str = '(' + geoutil.osm_bbox_str(self.lat, self.lon, self.radius) + ')'

        data = '[out:json];' \
               '(' \
               'way["building"~"."]' \
               '%s;' \
               'way["highway"~"."]' \
               '%s;' \
               ');' % (bbox_str, bbox_str)
        data += '(' \
                '._;' \
                'node(w);' \
                ');'
        data += 'out;'

        params = urllib.urlencode({"data": data})

        conn = httplib.HTTPConnection(url)
        conn.request("GET", query, params)

        response = conn.getresponse()
        result = response.read()

        conn.close()

        self.raw_data = json.loads(result)