import rhinoscript as rs

from grid import solver, grid_modifiers
from util import rsutil, geoutil


def run():
    """ Analyses a given location for optimal shelters positions
    (x,y is converted to lat,lon, units are assumed to be meters) """
    reload(solver)
    reload(grid_modifiers)
    reload(rsutil)

    position = rs.userinterface.GetPoint('Pick position')
    if not position:
        return

    lat, lon = geoutil.xy2latlon(position.X, position.Y)

    s = solver.GridSolver(lat, lon)
    s.add_modifier(grid_modifiers.ShadowModifier)
    s.add_modifier(grid_modifiers.StreetModifier)
    s.run()
    s.display_results()


if __name__ == "__main__":
    run()