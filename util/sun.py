import pytz
import datetime
from pysolar import solar
from pysolar.util import GetSunriseSunset
import math


class SunVector(object):
    def __init__(self, lat, lon, date=datetime.date.today(), tzinfo=pytz.timezone("Europe/Berlin")):
        self.lat = lat
        self.lon = lon
        self.date = date
        self.tzinfo = tzinfo

        now = tzinfo.localize(datetime.datetime.utcnow())
        utc_offset = now.utcoffset().seconds / 3600
        self.sunrise, self.sunset = GetSunriseSunset(lat, lon,
                                                     datetime.datetime.combine(self.date,
                                                                               datetime.datetime.utcnow().time()),
                                                     utc_offset)

    def get_position(self, time):
        time = time.astimezone(pytz.utc)
        alt = solar.GetAltitude(self.lat, self.lon, time)
        azi = solar.GetAzimuth(self.lat, self.lon, time)

        return alt, azi

    def get_positions(self, step=30):
        return [self.get_position(t) for t in self.times(step)]

    def get_vector(self, time):
        alt, azi = self.get_position(time)

        return self.sun_to_vec(alt, azi)

    def get_vectors(self, step=30):
        return [self.get_vector(t) for t in self.times(step)]

    def sun_to_vec(self, altitude, azimuth):
        altitude = math.radians(altitude)
        azimuth = math.radians(180 - azimuth)

        z = math.sin(altitude)
        hyp = math.cos(altitude)
        y = hyp * math.cos(azimuth)
        x = hyp * math.sin(azimuth)

        return [x, y, z]

    def times(self, step=30):
        # return date range from sunrise to sunset
        current = self.sunrise
        while current <= self.sunset:
            yield current.replace(tzinfo=self.tzinfo)
            current = current + datetime.timedelta(minutes=step)

    def tz_time(self, time):
        time = time.replace(tzinfo=self.tzinfo)
        return datetime.datetime.combine(self.date, time)

    def times_list(self, step=30):
        return [t for t in self.times(step)]