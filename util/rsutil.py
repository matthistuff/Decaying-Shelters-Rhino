import math

import rhinoscript as rs
import scriptcontext as sc

import Rhino as r
from util import geoutil
import System.Threading.Tasks as tasks


def rd(wait=False):
    rs.document.EnableRedraw(True)
    sc.doc.Views.Redraw()
    if wait is True:
        r.RhinoApp.Wait()


def nd():
    rs.document.EnableRedraw(False)


def rdnd():
    rd(True)
    nd()


def create_point(x, y=None, z=0):
    if y is None:
        return r.Geometry.Point3d(x[0], x[1], x[2])
    return r.Geometry.Point3d(x, y, z)


def objects_in_radius(point, radius, type_filter=rs.selection.filter.allobjects, simple=True):
    point = rs.utility.coerce3dpoint(point)
    contain_bb = r.Geometry.BoundingBox(
        point.X - radius,
        point.Y - radius,
        point.Z - radius,
        point.X + radius,
        point.Y + radius,
        point.Z + radius
    )

    objects = sc.doc.Objects.GetObjectList(rs.selection.__FilterHelper(type_filter))
    contained_objects = []

    def solve_parallel(obj):
        if simple:
            if contain_bb.Contains(obj.Geometry.GetBoundingBox(False)) is True:
                contained_objects.append(obj)
        else:
            intersection = r.Geometry.BoundingBox.Intersection(contain_bb, obj.Geometry.GetBoundingBox(False))
            if intersection.IsValid:
                contained_objects.append(obj)

    tasks.Parallel.ForEach(objects, solve_parallel)

    return contained_objects


def create_extrusion(profile, start_point, end_point):
    extrusion = r.Geometry.Extrusion()
    extrusion.SetOuterProfile(profile, True)
    extrusion.SetPathAndUp(start_point, end_point, r.Geometry.Vector3d.YAxis)
    return extrusion


def create_shadow(obj, vector):
    obj = rs.utility.coercemesh(obj)
    #obj = obj.Duplicate()

    vector = rs.utility.coerce3dvector(vector)
    ground_plane = rs.plane.WorldXYPlane()

    plane = r.Geometry.Plane(ground_plane.Origin, vector)
    outlines = obj.GetOutlines(plane)
    #obj.Dispose()

    if outlines:
        for i in range(len(outlines)):
            polyline = outlines[i]
            for j in range(polyline.Count):
                line = r.Geometry.Line(polyline[j], vector)
                rc, t = r.Geometry.Intersect.Intersection.LinePlane(line, ground_plane)
                if rc:
                    polyline[j] = line.PointAt(t)

            outlines[i] = polyline

        outline = outlines[0]

        return outline
    else:
        return outlines


def curve_midpoint(curve):
    rc, t = curve.NormalizedLengthParameter(0.5)
    return curve.PointAt(t)


def basic_mesh(obj):
    obj = rs.utility.coercerhinoobject(obj)
    mesh_type = r.Geometry.MeshType.Analysis
    obj.CreateMeshes(mesh_type, r.Geometry.MeshingParameters.Coarse, True)
    return obj.GetMeshes(mesh_type)


def mesh(obj):
    obj = rs.utility.coercerhinoobject(obj)
    mesh_type = r.Geometry.MeshType.Default
    rs.userinterface.MessageBox(obj.CreateMeshes(mesh_type, r.Geometry.MeshingParameters.Default, True))
    return obj.GetMeshes(mesh_type)


def rotated_uni_vector(angle):
    vec = r.Geometry.Vector3d(0, 1, 0)
    vec.Rotate(math.radians(angle), r.Geometry.Vector3d.ZAxis)
    vec.Unitize()
    return vec


def create_bbox(x, y, size):
    minX = x - size / 2.0
    minY = y - size / 2.0
    minZ = 0
    maxX = y + size / 2.0
    maxY = y + size / 2.0
    maxZ = 12

    return r.Geometry.BoundingBox(minX, minY, minZ, maxX, maxY, maxZ)


def look_at(position, bounds):
    if type(position) is r.Geometry.Point3d:
        x = position.X
        y = position.Y
        z = position.Z
    else:
        x = geoutil.lon2coord(position[0])
        y = geoutil.lat2coord(position[1])
        z = 0

    rs.view.ViewCameraTarget('Perspective', (x + bounds[0], y + bounds[1], z + bounds[2]), (x, y, z))


def render_preview_to(filename):
    rs.document.CreatePreviewImage(filename, None, (640, 480))