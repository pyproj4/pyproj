"""Rewrite part of test.py in pyproj in the form of unittests."""
import unittest
from pyproj import Proj


class BasicTest(unittest.TestCase):

  def testProj4Version(self):
    awips221 = Proj(proj='lcc',R=6371200,lat_1=50,lat_2=50,lon_0=-107)
    #self.assertEqual(awips221.proj_version, 4.9)

  def testProjAwips221(self):
    # AWIPS is Advanced Weather Interactive Processing System
    params = {'proj': 'lcc', 'R': 6371200, 'lat_1': 50, 'lat_2': 50,
              'lon_0': -107}
    nx = 349
    ny = 277
    awips221 = Proj(proj=params['proj'], R=params['R'],
                    lat_1=params['lat_1'], lat_2=params['lat_2'],
                    lon_0=params['lon_0'])
    awips221_from_dict = Proj(params)

    items = sorted([val for val in awips221.srs.split() if val])
    items_dict = sorted([val for val in awips221_from_dict.srs.split() if val])
    self.assertEqual(items, items_dict)

    expected = sorted(('+units=m', '+proj=lcc', '+lat_2=50', '+lat_1=50',
                      '+lon_0=-107','+R=6371200'))
    self.assertEqual(items, expected)

    point = awips221(-145.5,1.)
    x, y = -5632642.22547495, 1636571.4883145525
    self.assertAlmostEqual(point[0], x)
    self.assertAlmostEqual(point[1], y)

    pairs = [
        [(-45,45), (4351601.20766915, 7606948.029327129)],
        [(45,45), (5285389.07739382, 14223336.17467613)],
        [(45,-45), (20394982.466924712, 21736546.456803113)],
        [(-45,-45), (16791730.756976362, -3794425.4816524936)]
        ]
    for point_geog, expected in pairs:
      point = awips221(*point_geog)
      self.assertAlmostEqual(point[0], expected[0])
      self.assertAlmostEqual(point[1], expected[1])
      point_geog2 = awips221(*point, inverse=True)
      self.assertAlmostEqual(point_geog[0], point_geog2[0])
      self.assertAlmostEqual(point_geog[1], point_geog2[1])


if __name__ == '__main__':
  unittest.main()
