"""Rewrite part of test.py in pyproj in the form of unittests."""
from __future__ import with_statement

from sys import version_info as sys_version_info

if sys_version_info[:2] < (2 ,7):
    # for Python 2.4 - 2.6 use the backport of unittest from Python 2.7 and onwards
    import unittest2 as unittest
else:
    import unittest

from pyproj import Geod, Proj, transform
from pyproj import pj_list, pj_ellps

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

class TypeError_Transform_Issue8_Test(unittest.TestCase):
    # Test for "Segmentation fault on pyproj.transform #8"
    # https://github.com/jswhit/pyproj/issues/8

    def setUp(self):
       self.p = Proj(init='epsg:4269')
    
    def test_tranform_none_1st_parmeter(self):
    # test should raise Type error if projections are not of Proj classes
    # version 1.9.4 produced AttributeError, now should raise TypeError
       with self.assertRaises(TypeError):
          transform(None, self.p, -74, 39)

    def test_tranform_none_2nd_parmeter(self):
    # test should raise Type error if projections are not of Proj classes
    # version 1.9.4 has a Segmentation Fault, now should raise TypeError
       with self.assertRaises(TypeError):
          transform(self.p, None, -74, 39)

class Geod_NoDefs_Issue22_Test(unittest.TestCase):
   # Test for Issue #22, Geod with "+no_defs" in initstring 
   # Before PR #23 merged 2015-10-07, having +no_defs in the initstring would result in a ValueError
   def test_geod_nodefs(self):
       Geod("+a=6378137 +b=6378137 +no_defs")

class ForwardInverseTest(unittest.TestCase):
  pass

def testcase(pj):
  # print 'defining: ', pj
  def TestOneProjection(self):
    # print 'testing: ', pj
    try:
      p = Proj(proj=pj)
      x,y = p(-30,40)
      # note, for proj 4.9.2 or before the inverse projection may be missing
      # and pyproj 1.9.5.1 or before does not test for this and will
      # give a segmentation fault at this point:
      lon,lat = p(x,y,inverse=True)
    except RuntimeError:
      pass
  return TestOneProjection

# maybe also add tests for pj_ellps?
for pj in sorted(pj_list):
  testname = 'test_'+pj
  setattr(ForwardInverseTest, testname, testcase(pj))


# test __repr__ for Proj object
class ProjReprTest(unittest.TestCase):
    def test_repr(self):
        p = Proj(proj='latlong', preserve_units=True)
        self.assertEqual(repr(p), "pyproj.Proj('+proj=latlong ', preserve_units=True)")

# test __repr__ for Geod object
class GeodReprTest(unittest.TestCase):
    def test_sphere(self):
        g = Geod('+a=6051800 +b=6051800')   # ellipse is Venus 2000, IAU2000:29900
        self.assertEqual(repr(g), "pyproj.Geod('+a=6051800.0 +f=0.0')")
    
    def test_ellps_name_round_trip(self):
        # this could be done in a parameter fashion
        for ellps_name in pj_ellps:
            if ellps_name in ('NWL9D', 'WGS66'): # skip tests, these ellipses are the same
                continue
            p = Geod(ellps=ellps_name)
            self.assertEqual(repr(p), "pyproj.Geod(ellps='{0}')".format(ellps_name))

  

# Tests for shared memory between Geod objects
class GeodSharedMemoryBugTestIssue64(unittest.TestCase):
    def setUp(self):
        self.g = Geod(ellps='clrk66')
        self.ga = self.g.a
        self.mercury = Geod(a=2439700) # Mercury 2000 ellipsoid
                                       # Mercury is much smaller than earth.
    
    def test_not_shared_memory(self):
        self.assertEqual(self.ga, self.g.a)
        # mecury must have a different major axis from earth
        self.assertNotEqual(self.g.a, self.mercury.a)
        self.assertNotEqual(self.g.b, self.mercury.b)
        self.assertNotEqual(self.g.sphere, self.mercury.sphere)
        self.assertNotEqual(self.g.f, self.mercury.f)
        self.assertNotEqual(self.g.es, self.mercury.es)
        
        # initstrings were not shared in issue #64
        self.assertNotEqual(self.g.initstring, self.mercury.initstring)

    def test_distances(self):
        # note calculated distance was not an issue with #64, but it still a shared memory test
        boston_lat = 42.+(15./60.); boston_lon = -71.-(7./60.)
        portland_lat = 45.+(31./60.); portland_lon = -123.-(41./60.)
        
        az12,az21,dist_g = self.g.inv(boston_lon,boston_lat,portland_lon,portland_lat)
        
        az12,az21,dist_mercury = self.mercury.inv(boston_lon,boston_lat,portland_lon,portland_lat)
        self.assertLess(dist_mercury, dist_g)
        
        
if __name__ == '__main__':
  unittest.main()
