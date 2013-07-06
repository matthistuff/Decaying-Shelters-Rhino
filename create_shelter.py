import rhinoscript as rs
from util import rsutil
from shelter import hull_modifiers, plan_modifiers, hull, plan, shelter, color, color_modifiers


def run():
    """ Creates a shelter at a given position
    (x,y is converted to lat,lon, units are assumed to be meters) """
    reload(rsutil)
    reload(hull)
    reload(hull_modifiers)
    reload(plan)
    reload(plan_modifiers)
    reload(color)
    reload(color_modifiers)
    reload(shelter)

    position = rs.userinterface.GetPoint('Pick position')
    if not position: return

    s = shelter.Shelter(position)

    #
    # Modifiers for the plan
    #
    #shelter.plan.add_modifier(plan_modifiers.WindModifier)
    s.plan.add_modifier(plan_modifiers.SunPlanModifier)

    #
    # Modifiers for the hull
    #
    s.hull.add_modifier(hull_modifiers.SunHullModifier, 1)
    s.hull.add_modifier(hull_modifiers.BuildingShapeModifier, 3)
    s.hull.add_modifier(hull_modifiers.SphericalHullModifier)

    #
    # Modifiers for the hull coloring
    #
    #shelter.color.add_modifier(color_modifiers.HeightModifier)
    #shelter.color.add_modifier(color_modifiers.SunColorModifier)

    rsutil.nd()
    s.create()
    rsutil.look_at(rsutil.create_point(position.X, position.Y, 2), (10, 20, 3))


if __name__ == "__main__":
    run()