import rhinoscript as rs
import scriptcontext as sc
import Rhino as r


class ColoredHull:
    def __init__(self, shelter):
        self.shelter = shelter

        self.layer_name = 'shelter_colored ' + self.shelter.start.isoformat()
        self.modifiers = []

        if not rs.layer.IsLayer(self.layer_name):
            rs.layer.AddLayer(self.layer_name)

    def create(self):
        if len(self.modifiers) is 0:
            return

        hull = rs.utility.coercerhinoobject(self.shelter.hull.guid)
        self.mesh = r.Geometry.Mesh.CreateFromBrep(hull.Geometry, r.Geometry.MeshingParameters.Coarse)[0]
        self.vertices = self.mesh.Vertices
        self.vertex_count = self.vertices.Count
        self.mesh.VertexColors.CreateMonotoneMesh(rs.utility.coercecolor([175] * 3))

        current_layer = rs.layer.CurrentLayer()
        rs.layer.CurrentLayer(self.layer_name)

        [modifier.solve() for modifier in self.modifiers]

        sc.doc.Objects.AddMesh(self.mesh)

        rs.layer.CurrentLayer(current_layer)

    def add_modifier(self, modifier, strength=1):
        self.modifiers.append(modifier(self, strength))