import math
import datetime

import rhinoscript as rs
import scriptcontext as sc

import Rhino as r
import System.Drawing

from util import rsutil, geoutil


class GridSolver(object):
    def __init__(self, position, lon=None, date=datetime.date.today(), objects=None):
        self.date = date

        if lon is not None:
            self.lat = position
            self.lon = lon
            x, y = geoutil.latlon2coord(self.lat, self.lon)
            self.position = rsutil.create_point(x, y, 0)
        else:
            self.position = rs.utility.coerce3dpoint(position)

        self.objects = []

        if objects is None:
            objects = rsutil.objects_in_radius(self.position, 100, rs.selection.filter.extrusion, False)

        for o in objects:
            self.objects.extend(rsutil.basic_mesh(o))

        if lon is None:
            self.lat, self.lon = geoutil.coord2latlon(self.position.X, self.position.Y)

        self.modifiers = []
        self.grid = Grid(self.position, 105, 15)

    def run(self):
        self.grid.reset()
        [modifier.solve() for modifier in self.modifiers]

    def add_modifier(self, modifier, weight=1.0):
        self.modifiers.append(modifier(self, float(weight)))

    def get_results(self, count=None, treshold=None):
        [box.compute_score(self.modifiers) for box in self.grid.sub_boxes]

        result = sorted(self.grid.sub_boxes, key=lambda box: box.score, reverse=True)

        if treshold is not None:
            result = [box for box in result if box.score > treshold]

        if count is not None:
            result = result[:count]

        return result

    def display_results(self):
        self.get_results()
        self.grid.display_results()

    def dispose(self):
        self.grid.dispose()


class GridBox(object):
    def __init__(self, x, y, size):
        self.x = x + size / 2.0
        self.y = y - size / 2.0
        self.position = rsutil.create_point(self.x, self.y)
        self.size = size
        self.area = float(size ** 2)

        self.reset()

        points = [rsutil.create_point(x, y), rsutil.create_point(x + self.size, y),
                  rsutil.create_point(x + self.size, y - self.size),
                  rsutil.create_point(x, y - self.size)]
        points.append(points[0])
        self.curve = r.Geometry.Curve.CreateControlPointCurve(points, 1)

    def add_score(self, value, name='default'):
        if not name in self.scores:
            self.scores[name] = value
        else:
            self.scores[name] += value

    def get_score(self, name='default'):
        if not name in self.scores:
            return 0
        else:
            return self.scores[name]

    def compute_score(self, modifiers):
        final_score = 0
        weight_sum = 0
        for modifier in modifiers:
            if modifier.length > 0:
                weight_sum += modifier.weight
                final_score += (self.get_score(modifier.name) / modifier.length) * modifier.weight

        self.score = final_score / weight_sum

    def reset(self):
        self.scores = {}
        self.score = 0


class Grid(object):
    def __init__(self, position, size, resolution):
        self.position = position
        self.resolution = resolution
        self.size = size
        self.rcs = []

        if not rs.layer.IsLayer('analysis'):
            rs.layer.AddLayer('analysis')

        self.create_bbox_from_position()
        self.create_sub_boxes()

    def create_bbox_from_position(self, ):
        minX = self.position.X - self.size / 2.0
        minY = self.position.Y - self.size / 2.0
        minZ = 0
        maxX = self.position.X + self.size / 2.0
        maxY = self.position.Y + self.size / 2.0
        maxZ = 12

        self.bbox = r.Geometry.BoundingBox(minX, minY, minZ, maxX, maxY, maxZ)

        self.tl, self.tr, self.br, self.bl = self.get_bbox_corners(self.bbox)

        self.width = self.size
        self.height = self.size


    def create_bbox_from_objects(self, objects):
        self.bbox = r.Geometry.BoundingBox.Empty

        for o in objects:
            self.bbox.Union(o.GetBoundingBox(True))

        self.tl, self.tr, self.br, self.bl = self.get_bbox_corners(self.bbox)

        self.width = rs.utility.Distance(self.tl, self.tr)
        self.height = rs.utility.Distance(self.tl, self.bl)

    def create_sub_boxes(self):
        x_res = int(math.ceil(self.width / self.resolution))
        x_off = (self.width - x_res * self.resolution) / 2
        y_res = int(math.ceil(self.height / self.resolution))
        y_off = (self.height - y_res * self.resolution) / 2

        self.sub_boxes = []
        for i in range(x_res):
            x = self.tl.X + x_off + (i * self.resolution)
            for j in range(y_res):
                y = self.tl.Y - y_off - (j * self.resolution)
                box = GridBox(x, y, self.resolution)
                self.sub_boxes.append(box)


    def get_bbox_corners(self, bbox):
        tl = bbox.Corner(True, False, True)
        tr = bbox.Corner(False, False, True)
        br = bbox.Corner(False, True, True)
        bl = bbox.Corner(True, True, True)

        return tl, tr, br, bl

    def lerp_color(self, c1, c2, p):
        r1, g1, b1 = c1
        r2, g2, b2 = c2
        rd = r2 - r1
        gd = g2 - g1
        bd = b2 - b1

        rn = int(r1 + (rd * p))
        gn = int(g1 + (gd * p))
        bn = int(b1 + (bd * p))

        return rn, gn, bn


    def display_results(self):
        current_layer = rs.layer.CurrentLayer()
        rs.layer.CurrentLayer('analysis')

        for i in range(len(self.sub_boxes)):
            sub_box = self.sub_boxes[i]

            grid_box = r.Geometry.Brep.CreatePlanarBreps(sub_box.curve)
            guid = sc.doc.Objects.AddBrep(grid_box[0])
            self.rcs.append(guid)
            rhino_object = sc.doc.Objects.Find(guid)
            attr = rhino_object.Attributes
            rc, gc, bc = self.lerp_color((0, 60, 100), (255, 153, 0), sub_box.score)
            attr.ObjectColor = System.Drawing.Color.FromArgb(1, rc, gc, bc)
            attr.ColorSource = r.DocObjects.ObjectColorSource.ColorFromObject
            sc.doc.Objects.ModifyAttributes(rhino_object, attr, True)

            rsutil.rdnd()
            rs.utility.Sleep(15)

        rs.layer.CurrentLayer(current_layer)
        rsutil.rdnd()

    def reset(self):
        [box.reset() for box in self.sub_boxes]

    def dispose(self):
        if len(self.rcs) > 0:
            rs.object.DeleteObjects(self.rcs)