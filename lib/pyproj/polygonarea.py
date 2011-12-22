# polygonarea.py
#
# This is a rather literal translation of the GeographicLib::PolygonArea
# class to python.  See the documentation for the C++ class for more
# information at
#
#    http://sourceforge.net/html/annotated.html
#
# Copyright (c) Charles Karney (2011) <charles@karney.com> and licensed
# under the MIT/X11 License.  For more information, see
# http://sourceforge.net/
#
# $Id: 994cf91b693942fc0efc2a9b1233d020015a7041 $
######################################################################

import math
from pyproj.geomath import Math
from pyproj.accumulator import Accumulator

class PolygonArea(object):
  """Area of a geodesic polygon"""

  def transit(lon1, lon2):
    # Return 1 or -1 if crossing prime meridian in east or west direction.
    # Otherwise return zero.
    from pyproj.geodesic import Geodesic
    lon1 = Geodesic.AngNormalize(lon1)
    lon2 = Geodesic.AngNormalize(lon2)
    # treat lon12 = -180 as an eastward geodesic, so convert to 180.
    lon12 = -Geodesic.AngNormalize(lon1 - lon2) # In (-180, 180]
    cross = (1 if lon1 < 0 and lon2 >= 0 and lon12 > 0
             else (-1 if lon2 < 0 and lon1 >= 0 and lon12 < 0 else 0))
    return cross
  transit = staticmethod(transit)

  def __init__(self, earth, polyline = False):
    from pyproj.geodesic import Geodesic
    self._earth = earth
    self._area0 = 4 * math.pi * earth._c2
    self._polyline = polyline
    self._mask = Geodesic.DISTANCE | (0 if self._polyline else Geodesic.AREA)
    if not self._polyline: self._areasum = Accumulator()
    self._perimetersum = Accumulator()
    self.Clear()

  def Clear(self):
    self._num = 0
    self._crossings = 0
    if not self._polyline: self._areasum.Set(0)
    self._perimetersum.Set(0)
    self._lat0 = self._lon0 = self._lat1 = self._lon1 = 0

  def AddPoint(self, lat, lon):
    if self._num == 0:
      self._lat0 = self._lat1 = lat
      self._lon0 = self._lon1 = lon
    else:
      t, s12, t, t, t, t, t, S12 = self._earth.GenInverse(
        self._lat1, self._lon1, lat, lon, self._mask)
      self._perimetersum.Add(s12)
      if not self._polyline:
        self._areasum.Add(S12)
        self._crossings += PolygonArea.transit(self._lon1, lon)
      self._lat1 = lat
      self._lon1 = lon
    self._num += 1

  # return number, perimeter, area
  def Compute(self, reverse, sign):
    if self._polyline: area = Math.nan
    if self._num < 2:
      perimeter = 0
      if not self._polyline: area = 0
      return self._num, perimeter, area

    if self._polyline:
      perimeter = self._perimetersum.Sum()
      return self._num, perimeter, area

    t, s12, t, t, t, t, t, S12 = self._earth.GenInverse(
      self._lat1, self._lon1, self._lat0, self._lon0, self._mask)
    perimeter = self._perimetersum.Sum(s12)
    tempsum = Accumulator(self._areasum)
    tempsum.Add(S12)
    crossings = self._crossings + PolygonArea.transit(self._lon1, self._lon0)
    if crossings & 1:
      tempsum.Add( (1 if tempsum < 0 else -1) * self._area0/2 )
    # area is with the clockwise sense.  If !reverse convert to
    # counter-clockwise convention.
    if not reverse: tempsum.Negate()
    # If sign put area in (-area0/2, area0/2], else put area in [0, area0)
    if sign:
      if tempsum.Sum() > self._area0/2:
        tempsum.Add( -self._area0 )
      elif tempsum.Sum() <= -self._area0/2:
        tempsum.Add( +self._area0 )
    else:
      if tempsum.Sum() >= self._area0:
        tempsum.Add( -self._area0 )
      elif tempsum.Sum() < 0:
        tempsum.Add( +self._area0 )

    area = 0 + tempsum.Sum()
    return self._num, perimeter, area

  # return number, perimeter, area
  def TestCompute(self, lat, lon, reverse, sign):
    if self._polyline: area = Math.nan
    if self._num == 0:
      perimeter = 0
      if not self._polyline: area = 0
      return 1, perimeter, area

    perimeter = self._perimetersum.Sum()
    tempsum = 0 if self._polyline else self._areasum.Sum()
    crossings = self._crossings; num = self._num + 1
    for i in ([0] if self._polyline else [0, 1]):
      t, s12, t, t, t, t, t, S12 = self._earth.GenInverse(
        self._lat1 if i == 0 else lat, self._lon1 if i == 0 else lon,
        self._lat0 if i != 0 else lat, self._lon0 if i != 0 else lon,
        self._mask)
      perimeter += s12
      if not self._polyline:
        tempsum += S12
        crossings += PolygonArea.transit(self._lon1 if i == 0 else lon,
                                         self._lon0 if i != 0 else lon)

    if self._polyline:
      return num, perimeter, area

    if crossings & 1:
      tempsum += (1 if tempsum < 0 else -1) * self._area0/2
    # area is with the clockwise sense.  If !reverse convert to
    # counter-clockwise convention.
    if not reverse: tempsum *= -1
    # If sign put area in (-area0/2, area0/2], else put area in [0, area0)
    if sign:
      if tempsum > self._area0/2:
        tempsum -= self._area0
      elif tempsum <= -self._area0/2:
        tempsum += self._area0
    else:
      if tempsum >= self._area0:
        tempsum -= self._area0
      elif tempsum < 0:
        tempsum += self._area0

    area = 0 + tempsum
    return num, perimeter, area

  def Area(earth, points, polyline):
    poly =  PolygonArea(earth, polyline)
    for p in points:
      poly.AddPoint(p['lat'], p['lon'])
    return poly.Compute(False, True)
  Area = staticmethod(Area)
