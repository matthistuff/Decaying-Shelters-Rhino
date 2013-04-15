from datetime import date, timedelta
from util import weather

lat = 54.088533
lon = 12.137555
start = date.today()
end = start + timedelta(days=1)

data = weather.get_forecast(lat, lon, start, start)
print data