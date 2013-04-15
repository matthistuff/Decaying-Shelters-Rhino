from util import geoutil

lat = 54.088533
lon = 12.137555
radius = 300

bbox_str = '(' + geoutil.osm_bbox_str(lat, lon, radius) + ')'

data = '[out:json];'\
       '('\
       'way["building"~"."]'\
       '%s;'\
       'way["highway"~"."]'\
       '%s;'\
       ');' % (bbox_str, bbox_str)
data += '('\
        '._;'\
        'node(w);'\
        ');'
data += 'out;'

print data