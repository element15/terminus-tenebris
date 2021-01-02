#!/usr/bin/env python3
"""Terminus Tenebris: a sunrise/sunset utility."""

import datetime
from math import (
    sin, cos, tan,
    asin, acos, atan, atan2,
    radians, degrees)

import bottle

STYLE = '''\
<style type = text/css>
body {
  font-family: "SF Mono", "Monaco";
  font-size: 30pt;
  padding-top: 24pt;
  background-color: #333;
  color: #eee;
}
</style>
'''

# Number of leap seconds since 2000-01-01 as of 2021-01-01
LEAP_SECONDS = datetime.timedelta(seconds=5)
TIME_EPOCH = datetime.datetime(
    2000, 1, 1, hour=12, tzinfo=datetime.timezone.utc)

UTC_OFFSET = datetime.timedelta(hours=-6)
DST_OFFSET = datetime.timedelta(hours=1)
ZERO_OFFSET = datetime.timedelta(0)

deg_func = lambda f : lambda x : f(radians(x))
sind, cosd, tand = map(deg_func, (sin, cos, tan))

deg_afunc = lambda f : lambda x : degrees(f(x))
asind, acosd, atand = map(deg_afunc, (asin, acos, atan))
atan2d = lambda x, y : degrees(atan2(x, y))

class us_central(datetime.tzinfo):
    def utcoffset(self, dt):
        return UTC_OFFSET + self.dst(dt)
    def dst(self, dt):
        return DST_OFFSET if self._is_dst(dt) else ZERO_OFFSET
    def tzname(self, dt):
        return 'CDT' if self._is_dst(dt) else 'CST'

    def _is_dst(self, dt):
        # Since 2007 in the United States, DST has run from the second Sunday
        # in March through the first Sunday in November. The transition occurs
        # at 02:00 local time, but this function assumes that the entire day
        # is in the new time offset (effectively placing the transition at
        # midnight instead).
        if dt.month in (4, 5, 6, 7, 8, 9, 10):
            return True
        if dt.month in (1, 2, 12):
            return False
        wd = dt.isoweekday()%7 # Let Sunday be zero
        last_sunday = dt.day - wd # Month day of the previous Sunday
        if dt.month == 3: # DST begins in March
            return last_sunday > 7 # Second Sunday or later
        # DST ends in November
        return last_sunday > 0 # First Sunday or later
central_time = us_central()
    
def sun_times(latitude_deg, longitude_deg, dt):
    """Calculate sunrise/sunset parameters.

    These equations were adapted from Wikipedia:
    https://en.wikipedia.org/wiki/Sunrise_equation
    """
    # Julian date relative to 2000-01-01T12:00:00Z (days)
    n = (dt-TIME_EPOCH+LEAP_SECONDS).total_seconds() / 86400.0
    # Mean solar anomaly (degrees)
    M = (357.5291 + 985.600_280e-3*n) % 360
    # Equation of the center (degrees)
    C = 1.9148*sind(M) + 20e-3*sind(2*M) + 300e-6*sind(3*M)
    # Ecliptic longitude (degrees)
    lam = sum((M, C, 180.0, 102.9372)) % 360
    # Equation of time (days)
    eq_of_time_day = - 5.3e-3*sind(M) + 6.9e-3*sind(2*lam)
    # Declination of the sun (degrees)
    delta = asind(sind(lam)*sind(23.44))

    # Hour angle of the sun at the specified position above the horizon
    # given in hours either side of solar noon
    omega = lambda theta : acosd(
        (sind(theta) - sind(latitude_deg)*sind(delta))
        /(cosd(latitude_deg)*cosd(delta))) / 15.0
    sunset_deg = -0.83
    civil_twilight_deg = -6.0
    
    # Solar noon
    n_transit = int(n) - longitude_deg/360.0 - eq_of_time_day
    dt_transit = (
        TIME_EPOCH-LEAP_SECONDS
        + datetime.timedelta(days=n_transit)).astimezone(dt.tzinfo)

    out = {'noon': dt_transit}
    # Excludes civil twilight
    half_daylight_0 = datetime.timedelta(hours=omega(sunset_deg))
    out['sunrise'] = dt_transit - half_daylight_0
    out['sunset'] = dt_transit + half_daylight_0

    # Includes civil twilight
    half_daylight_1 = datetime.timedelta(hours=omega(civil_twilight_deg))
    out['dawn'] = dt_transit - half_daylight_1
    out['dusk'] = dt_transit + half_daylight_1
    
    return out

@bottle.route('/tenebris/<lat:float>/<lon:float>')
def index(lat, lon):
    dt = datetime.datetime.now(tz=central_time)
    times = sun_times(lat, lon, dt)
    times_fmt = {k: v.strftime(r'%H:%M:%S') for k, v in times.items()}
    return f'''\
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>Terminus Tenebris</title>
    {STYLE}
  </head>
  <body>
    <center>
      Dawn: <b>{times_fmt["dawn"]}</b><br />
      Dusk: <b>{times_fmt["dusk"]}</b>
    </center>
  </body>
</html>
'''

if __name__ == '__main__':
    bottle.run(host='0.0.0.0', port=8510, debug=True)
