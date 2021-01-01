#!/usr/bin/env python3
"""Terminus Tenebris: a sunrise/sunset utility."""

import datetime
from math import (
    sin, cos, tan,
    asin, acos, atan,
    radians, degrees)

# Number of leap seconds since 2000-01-01
LEAP_SECONDS = datetime.timedelta(seconds=5)
TIME_EPOCH = datetime.datetime(
    2000, 1, 1, hour=12, tzinfo=datetime.timezone.utc)

UTC_OFFSET = datetime.timedelta(hours=-6)
DST_OFFSET = datetime.timedelta(hours=1)
ZERO_OFFSET = datetime.timedelta(0)

deg_func = lambda f : lambda x : f(radians(x))
# sind = deg_func(sin)
# cosd = deg_func(cos)
# tand = deg_func(tan)
sind, cosd, tand = map(deg_func, (sin, cos, tan))
deg_afunc = lambda f : lambda x : degrees(f(x))
# asind = deg_afunc(asin)
# acosd = deg_afunc(acos)
# atand = deg_afunc(atan)
asind, acosd, atand = map(deg_afunc, (asin, acos, atan))

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

def get_day_minute(dt):
    return sum((
        dt.hour*60.0,
        dt.minute,
        dt.second/60.0,
        dt.microsecond/60e6))
    
def solar_elevation(latitude_deg, longitude_deg, dt):
    millenium_day = (dt-TIME_EPOCH+LEAP_SECONDS).total_seconds() / 86400.0
    local_time_min = get_day_minute(dt)
    tz_hours = dt.tzinfo.utcoffset(dt).total_seconds() / 3600.0
    julian_century = millenium_day / 36525.0 # G
    geom_mean_sun_lon_deg = ( # I
        280.466_460 + julian_century*(
            36_000.769_830 + julian_century*303.2e-6)) % 360
    geom_mean_sun_anom_deg = 357.529_110 + julian_century*( # J
        35_999.050_290 - 153.7e-6*julian_century)
    earth_orbit_ecc = 16.708_634e-3 - julian_century*( # K
        42.037e-6 + 126.7e-9*julian_century)
    sun_eq_center = ( # L
        sind(geom_mean_sun_anom_deg) * (
            1.914602 - julian_century * (4.817e-3 + 14e-6*julian_century))
        + sind(3*geom_mean_sun_anom_deg) * (19.993e-3 - 101e-6*julian_century)
        + sind(3*geom_mean_sun_anom_deg) * 289e-6)
    sun_true_lon_deg = geom_mean_sun_lon_deg - sun_eq_center # M
    sun_apparent_lon_deg = sun_true_lon_deg - 5.69e-3 - 4.78e-3*sind( # P
        125.04 - 1924.136 * julian_century)
    mean_ecliptic_obliquity_deg = 23+(26+( # Q
        21.448 - julian_century*(
            46.815 + julian_century*(
                590e-6 - julian_century*1.813e-3)))/60)/60
    obliquity_correction_deg = mean_ecliptic_obliquity_deg + 2.56e-3*cosd( # R
        125.04 - 1934.136*julian_century)
    sun_declination_deg = asind( # T
        sind(obliquity_correction_deg)*sind(sun_apparent_lon_deg))
    var_y = tand(obliquity_correction_deg/2)**2 # U
    eq_of_time_min = 4 * ( # V
        var_y*sind(2*geom_mean_sun_lon_deg)
        - 2*earth_orbit_ecc*sind(geom_mean_sun_anom_deg)
        + (
            4*earth_orbit_ecc*var_y
            *sind(geom_mean_sun_anom_deg)*cosd(2*geom_mean_sun_lon_deg))
        - 0.5*var_y**2*sind(4*geom_mean_sun_lon_deg)
        - 1.25*earth_orbit_ecc**2*sind(2*geom_mean_sun_anom_deg))
    true_solar_time_min = ( # AB
        local_time_min + eq_of_time_min + 4*longitude_deg - 60*tz_hours)%1440
    hour_angle_deg = true_solar_time_min/4 - 180 # AC
    solar_zenith_angle_deg = acosd( # AD
        sind(latitude_deg) * sind(sun_declination_deg) +
        cosd(latitude_deg) * cosd(sun_declination_deg) * cosd(hour_angle_deg))
    solar_elevation_angle_deg = 90 - solar_zenith_angle_deg # AE
    return solar_elevation_angle_deg
    
def main():
    dt = datetime.datetime(2020, 12, 31, 12, tzinfo=us_central())
    print(solar_elevation(32.5, -85.5, dt))
    
if __name__ == '__main__':
    main()
