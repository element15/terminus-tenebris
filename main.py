#!/usr/bin/env python3
"""Terminus Tenebris: a sunrise/sunset utility."""

import datetime as dt
import math as ma

UTC_OFFSET = dt.timedelta(hours=-6)
DST_OFFSET = dt.timedelta(hours=1)
ZERO_OFFSET = dt.timedelta(0)

class us_central(dt.tzinfo):
    def utcoffset(self, dt):
        return UTC_OFFSET + self.dst(dt)
    def dst(self, dt):
        return DST_OFFSET if self._is_dst(dt) else ZERO_OFFSET
    def tzname(self, dt):
        return 'CDT' if self._is_dst(dt) else 'CST'

    def _is_dst(self, dt):
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

now = dt.datetime.now(us_central())
print(now)
