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
        self.curve = curve
        self.extrusion = extrusion
        self.id = None
        self.rsobject = None
        self.bbox = None

    def get_bbox(self):
        if self.bbox is None:
            self.bbox = self.curve.GetBoundingBox(False)

        return self.bbox


    def add_to_doc(self):
        if self.id is None:
            self.id = sc.doc.Objects.AddExtrusion(self.extrusion)
            self.rsobject = rs.utility.coercerhinoobject(self.id)
        return self.id


class OSMObject(object):
    def __init__(self, tags=None, curve=None):
        self.tags = tags
        self.curve = curve
        self.id = None

    def add_to_doc(self):
        if self.id is None:
            self.id = sc.doc.Objects.AddCurve(self.curve)
        return self.id


class OSMData(object):
    def __init__(self):
        self.processed_shapes = dict()
        self.buildings = []
        self.highways = []

    def get_buildings_in_radius(self, location, radius=100, simple=True):
        location = rs.utility.coerce3dpoint(location)

        contain_bb = r.Geometry.BoundingBox(
            location.X - radius,
            location.Y - radius,
            location.Z - radius,
            location.X + radius,
            location.Y + radius,
            location.Z + radius
        )

        contained_objects = []

        def solve_parallel(building):
            if simple:
                if contain_bb.Contains(building.get_bbox()) is True:
                    contained_objects.append(building)
            else:
                intersection = r.Geometry.BoundingBox.Intersection(contain_bb, building.get_bbox())
                if intersection.IsValid:
                    contained_objects.append(building)

        tasks.Parallel.ForEach(self.buildings, solve_parallel)

        return contained_objects

    def load_data(self, lat, lon, radius):
        self.lat = lat
        self.lon = lon
        self.radius = radius

        self.__query_api()
        return self.raw_data

    def process_data(self, raw_data=None, add_to_doc=True, animate=False, filter_function=None):
        if raw_data is None:
            raw_data = self.raw_data

        if add_to_doc is True:
            current_layer = rs.layer.CurrentLayer()
            if not rs.layer.IsLayer('osm'):
                rs.layer.AddLayer('osm')
            rs.layer.CurrentLayer('osm')

        self.nodes = [node for node in raw_data['elements'] if node['type'] == 'node']
        self.ways = [node for node in raw_data['elements'] if node['type'] == 'way']

        self.loaded_buildings = []
        self.loaded_highways = []

        def solve_parallel(i):
            self.process_way(i)

        tasks.Parallel.ForEach(self.ways, solve_parallel)
        #[solve_parallel(i) for i in xrange(len(self.ways))]

        if add_to_doc is True:
            if not rs.group.IsGroup('highway'):
                rs.group.AddGroup('highway')
            if not rs.group.IsGroup('building'):
                rs.group.AddGroup('building')

            if not animate:
                for osmobject in self.loaded_highways:
                    self.highways.append(osmobject)
                    rs.group.AddObjectToGroup(osmobject.add_to_doc(), 'highway')

                for osmobject in self.loaded_buildings:
                    self.buildings.append(osmobject)
                    rs.group.AddObjectToGroup(osmobject.add_to_doc(), 'building')

            else:
                i = 0
                for osmobject in self.loaded_highways:
                    self.highways.append(osmobject)
                    rs.group.AddObjectToGroup(osmobject.add_to_doc(), 'highway')
                    filter_function(osmobject)
                    if i % 5 is 0:
                        rsutil.rdnd()
                    i += 1

                for osmobject in self.loaded_buildings:
                    self.buildings.append(osmobject)
                    rs.group.AddObjectToGroup(osmobject.add_to_doc(), 'building')
                    if i % 5 is 0:
                        rsutil.rdnd()
                    i += 1

                rsutil.rdnd()

            rs.layer.CurrentLayer(current_layer)

        else:
            [self.highways.append(osmobject) for osmobject in self.loaded_highways]
            [self.buildings.append(osmobject) for osmobject in self.loaded_buildings]


    def process_way(self, way):
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
            self.loaded_buildings.append(building)

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
            self.loaded_highways.append(OSMObject(way['tags'], curve))


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
        result = response.read().decode('utf-8')

        conn.close()

        self.raw_data = json.loads(result)