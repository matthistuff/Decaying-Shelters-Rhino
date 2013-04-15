from util import osmutil


def run():
    """ Retrieves OpenStreetMap Data for a given position """
    reload(osmutil)

    # Weimar
    lat = 50.974429
    lon = 11.329224

    # Radius in meters
    radius = 400

    osm = osmutil.OSMData()
    osm.load_data(lat, lon, radius)
    osm.process_data(None, True, True)


if __name__ == "__main__":
    run()