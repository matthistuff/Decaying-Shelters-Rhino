import urllib2
import urllib
import json
from datetime import date


def get_forecast(lat, lon, start=date.today(), end=None):
    if end is None:
        end = start

    url = "http://api.aerisapi.com/forecasts/closest"
    data = {
        "client_id": "suNwAuXAa8Yk62f4dvRyl",
        "client_secret": "pcWGbFJlkVcsYPdaxtG3hUWYjO58R0mSFahpwHbZ",
        "p": str(lat) + "," + str(lon),
        "from": start.isoformat(),
        "to": end.isoformat(),
        "filter": "day"
    }

    request = urllib2.urlopen(url, urllib.urlencode(data))
    response = request.read()
    request.close()
    response = json.loads(response)

    if response["success"]:
        return response["response"][0]["periods"]
    else:
        return False


def mean_wind(forecast):
    vec = float(forecast[0]["windDirDEG"])
    speed = float(forecast[0]["windSpeedKPH"])
    if len(forecast) > 1:
        for i in range(1, len(forecast)):
            vec += (vec - float(forecast[i]["windDirDEG"])) / 2
            speed = (float(forecast[i]["windSpeedKPH"]) + speed) / 2
    return vec, speed