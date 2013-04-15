import math

# This is in meters!
EARTH_RADIUS = 6378137.0


def lat2coord(lat):
    # Y
    global EARTH_RADIUS
    return EARTH_RADIUS * math.log(
        (math.sin(math.radians(lat)) + 1.0) / math.cos(math.radians(lat))
    )


def lat2y(lat):
    return lat2coord(lat)


def lon2coord(lon):
    # X
    global EARTH_RADIUS
    return EARTH_RADIUS * math.radians(lon)


def long2coord(lon):
    # X
    return lon2coord(lon)


def lon2x(lon):
    return lon2coord(lon)


def latlon2coord(lat, lon):
    return long2coord(lon), lat2coord(lat)


def latlon2xy(lat, lon):
    return latlon2coord(lat, lon)


def x2lon(x):
    global EARTH_RADIUS
    return math.degrees(x / EARTH_RADIUS)


def y2lat(y):
    global EARTH_RADIUS
    lat_radians = y / EARTH_RADIUS
    return math.degrees(2 * math.atan(math.exp(lat_radians)) - math.pi / 2)


def coord2latlon(x, y):
    return y2lat(y), x2lon(x)


def xy2latlon(x, y):
    return coord2latlon(x, y)


def ll_bbox(lat, lon, radius):
    global EARTH_RADIUS
    # http://www.d-mueller.de/blog/umkreissuche-latlong-und-der-radius/
    max_lat = lat + math.degrees(radius / EARTH_RADIUS)
    min_lat = lat - math.degrees(radius / EARTH_RADIUS)
    max_lon = lon + math.degrees(radius / EARTH_RADIUS / math.cos(math.radians(lat)))
    min_lon = lon - math.degrees(radius / EARTH_RADIUS / math.cos(math.radians(lat)))

    return (lat, lon), (max_lat, min_lon), (max_lat, max_lon), (min_lat, min_lon), (min_lat, max_lon)


def osm_bbox(lat, lon, radius):
    bbox = ll_bbox(lat, lon, radius)

    return bbox[3][0], bbox[1][1], bbox[1][0], bbox[2][1]


def osm_bbox_str(lat, lon, radius):
    return ','.join(str(item) for item in osm_bbox(lat, lon, radius))