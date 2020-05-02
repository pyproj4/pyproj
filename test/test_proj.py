# -*- coding: utf-8 -*-
import math
import sys
import unittest

import numpy as np
import pytest
from numpy.testing import assert_almost_equal

from pyproj import Geod, Proj, pj_ellps, pj_list, transform
from pyproj.exceptions import CRSError, ProjError


class BasicTest(unittest.TestCase):
    def testInitWithBackupString4(self):
        # this fails unless backup of to_string(4) is used
        pj = Proj(
            "+proj=merc +a=6378137.0 +b=6378137.0 +nadgrids=@null "
            "+lon_0=0.0 +x_0=0.0 +y_0=0.0 +units=m +no_defs"
        )
        assert pj.crs.name == "unknown"

    def testProjAwips221(self):
        # AWIPS is Advanced Weather Interactive Processing System
        params = {"proj": "lcc", "R": 6371200, "lat_1": 50, "lat_2": 50, "lon_0": -107}
        awips221 = Proj(
            proj=params["proj"],
            R=params["R"],
            lat_1=params["lat_1"],
            lat_2=params["lat_2"],
            lon_0=params["lon_0"],
            preserve_units=False,
        )
        awips221_from_dict = Proj(params, preserve_units=False)

        items = sorted(val for val in awips221.crs.srs.split() if val)
        items_dict = sorted(val for val in awips221_from_dict.crs.srs.split() if val)
        self.assertEqual(items, items_dict)

        expected = sorted(
            [
                "+proj=lcc",
                "+R=6371200",
                "+lat_1=50",
                "+lat_2=50",
                "+lon_0=-107",
                "+type=crs",
            ]
        )
        self.assertEqual(items, expected)

        point = awips221(-145.5, 1.0)
        x, y = -5632642.22547495, 1636571.4883145525
        self.assertAlmostEqual(point[0], x)
        self.assertAlmostEqual(point[1], y)

        pairs = [
            [(-45, 45), (4351601.20766915, 7606948.029327129)],
            [(45, 45), (5285389.07739382, 14223336.17467613)],
            [(45, -45), (20394982.466924712, 21736546.456803113)],
            [(-45, -45), (16791730.756976362, -3794425.4816524936)],
        ]
        for point_geog, expected in pairs:
            point = awips221(*point_geog)
            self.assertAlmostEqual(point[0], expected[0])
            self.assertAlmostEqual(point[1], expected[1])
            point_geog2 = awips221(*point, inverse=True)
            self.assertAlmostEqual(point_geog[0], point_geog2[0])
            self.assertAlmostEqual(point_geog[1], point_geog2[1])

    def test_from_dict_with_bool(self):
        # issue #183
        p_d = {
            "proj": "omerc",
            "lat_2": 80.27942,
            "lat_0": 62.87671,
            "lat_1": 42.751232,
            "ellps": "WGS84",
            "no_rot": True,
            "lon_1": 33.793186,
            "lon_2": -18.374414,
        }
        p = Proj(p_d)
        self.assertTrue("+no_rot" in p.srs.split())
        p_d = {
            "proj": "omerc",
            "lat_2": 80.27942,
            "lat_0": 62.87671,
            "lat_1": 42.751232,
            "ellps": "WGS84",
            "no_rot": False,
            "lon_1": 33.793186,
            "lon_2": -18.374414,
        }
        p = Proj(p_d)
        self.assertFalse("+no_rot" in p.srs.split())


class InverseHammerTest(unittest.TestCase):
    # This is a unit test of the inverse of the hammer projection, which
    # was added in the 4.9.3 version of PROJ (then PROJ.4).
    @classmethod
    def setUpClass(self):
        self.p = Proj(proj="hammer")  # hammer proj
        self.x, self.y = self.p(-30, 40)

    def test_forward(self):
        self.assertAlmostEqual(self.x, -2711575.083, places=3)
        self.assertAlmostEqual(self.y, 4395506.619, places=3)

    def test_inverse(self):
        lon, lat = self.p(self.x, self.y, inverse=True)
        self.assertAlmostEqual(lon, -30.0, places=3)
        self.assertAlmostEqual(lat, 40.0, places=3)


class TypeError_Transform_Issue8_Test(unittest.TestCase):
    # Test for "Segmentation fault on pyproj.transform #8"
    # https://github.com/jswhit/pyproj/issues/8

    def setUp(self):
        with pytest.warns(FutureWarning):
            self.p = Proj(init="epsg:4269")

    def test_tranform_none_1st_parmeter(self):
        # test should raise Type error if projections are not of Proj classes
        # version 1.9.4 produced AttributeError, now should raise TypeError
        with pytest.warns(DeprecationWarning), pytest.raises(CRSError):
            transform(None, self.p, -74, 39)

    def test_tranform_none_2nd_parmeter(self):
        # test should raise Type error if projections are not of Proj classes
        # version 1.9.4 has a Segmentation Fault, now should raise TypeError
        with pytest.warns(DeprecationWarning), pytest.raises(CRSError):
            transform(self.p, None, -74, 39)


class Geod_NoDefs_Issue22_Test(unittest.TestCase):
    # Test for Issue #22, Geod with "+no_defs" in initstring
    # Before PR #23 merged 2015-10-07, having +no_defs in the
    # initstring would result in a ValueError
    def test_geod_nodefs(self):
        Geod("+a=6378137 +b=6378137 +no_defs")


class ProjLatLongTypeErrorTest(unittest.TestCase):
    # .latlong() using in transform raised a TypeError in release 1.9.5.1
    # reported in issue #53, resolved in #73.
    def test_latlong_typeerror(self):
        p = Proj("+proj=stere +lon_0=-39 +lat_0=90 +lat_ts=71.0 +ellps=WGS84")
        self.assertTrue(isinstance(p, Proj))
        # if not patched this line raises a "TypeError: p2 must be a Proj class"
        with pytest.warns(DeprecationWarning):
            lon, lat = transform(p, p.to_latlong(), 200000, 400000)


@unittest.skipIf(
    sys.version_info < (3, 4), "Python 3.4 or newer required for subTest()"
)
class ForwardInverseTest(unittest.TestCase):
    def test_fwd_inv(self):
        for pj in pj_list.keys():
            with self.subTest(pj=pj):
                try:
                    p = Proj(proj=pj)
                    x, y = p(-30, 40)
                    # note, for proj 4.9.2 or before the inverse projection
                    # may be missing and pyproj 1.9.5.1 or before does not
                    # test for this and will
                    # give a segmentation fault at this point:
                    lon, lat = p(x, y, inverse=True)
                except RuntimeError:
                    pass


# Tests for shared memory between Geod objects
class GeodSharedMemoryBugTestIssue64(unittest.TestCase):
    def setUp(self):
        self.g = Geod(ellps="clrk66")
        self.ga = self.g.a
        self.mercury = Geod(a=2439700)  # Mercury 2000 ellipsoid
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
        # note calculated distance was not an issue with #64,
        # but it still a shared memory test
        boston_lat = 42.0 + (15.0 / 60.0)
        boston_lon = -71.0 - (7.0 / 60.0)
        portland_lat = 45.0 + (31.0 / 60.0)
        portland_lon = -123.0 - (41.0 / 60.0)

        az12, az21, dist_g = self.g.inv(
            boston_lon, boston_lat, portland_lon, portland_lat
        )

        az12, az21, dist_mercury = self.mercury.inv(
            boston_lon, boston_lat, portland_lon, portland_lat
        )
        self.assertLess(dist_mercury, dist_g)


class ReprTests(unittest.TestCase):
    # test __repr__ for Proj object
    def test_repr(self):
        p = Proj(proj="latlong", preserve_units=True)
        expected = "Proj('+proj=longlat +datum=WGS84 +no_defs', preserve_units=True)"
        self.assertEqual(repr(p), expected)

    # test __repr__ for Geod object
    def test_sphere(self):
        # ellipse is Venus 2000 (IAU2000:29900), which is a sphere
        g = Geod("+a=6051800 +b=6051800")
        self.assertEqual(repr(g), "Geod('+a=6051800 +f=0')")

    # test __repr__ for Geod object
    def test_ellps_name_round_trip(self):
        # this could be done in a parameter fashion
        for ellps_name in pj_ellps:
            # skip tests, these ellipses NWL9D and WGS66 are the same
            if ellps_name in ("NWL9D", "WGS66"):
                continue
            p = Geod(ellps=ellps_name)
            expected = "Geod(ellps='{0}')".format(ellps_name)
            self.assertEqual(repr(p), expected)


class TestRadians(unittest.TestCase):
    """Tests issue #84"""

    def setUp(self):
        self.g = Geod(ellps="clrk66")
        self.boston_d = (-71.0 - (7.0 / 60.0), 42.0 + (15.0 / 60.0))
        self.boston_r = (math.radians(self.boston_d[0]), math.radians(self.boston_d[1]))
        self.portland_d = (-123.0 - (41.0 / 60.0), 45.0 + (31.0 / 60.0))
        self.portland_r = (
            math.radians(self.portland_d[0]),
            math.radians(self.portland_d[1]),
        )

    def test_inv_radians(self):

        # Get bearings and distance from Boston to Portland in degrees
        az12_d, az21_d, dist_d = self.g.inv(
            self.boston_d[0],
            self.boston_d[1],
            self.portland_d[0],
            self.portland_d[1],
            radians=False,
        )

        # Get bearings and distance from Boston to Portland in radians
        az12_r, az21_r, dist_r = self.g.inv(
            self.boston_r[0],
            self.boston_r[1],
            self.portland_r[0],
            self.portland_r[1],
            radians=True,
        )

        # Check they are equal
        self.assertAlmostEqual(az12_d, math.degrees(az12_r))
        self.assertAlmostEqual(az21_d, math.degrees(az21_r))
        self.assertAlmostEqual(dist_d, dist_r)

    def test_fwd_radians(self):
        # Get bearing and distance to Portland
        az12_d, az21_d, dist = self.g.inv(
            self.boston_d[0],
            self.boston_d[1],
            self.portland_d[0],
            self.portland_d[1],
            radians=False,
        )

        # Calculate Portland's lon/lat from bearing and distance in degrees
        endlon_d, endlat_d, backaz_d = self.g.fwd(
            self.boston_d[0], self.boston_d[1], az12_d, dist, radians=False
        )

        # Calculate Portland's lon/lat from bearing and distance in radians
        endlon_r, endlat_r, backaz_r = self.g.fwd(
            self.boston_r[0], self.boston_r[1], math.radians(az12_d), dist, radians=True
        )

        # Check they are equal
        self.assertAlmostEqual(endlon_d, math.degrees(endlon_r))
        self.assertAlmostEqual(endlat_d, math.degrees(endlat_r))
        self.assertAlmostEqual(backaz_d, math.degrees(backaz_r))

        # Check to make sure we're back in Portland
        self.assertAlmostEqual(endlon_d, self.portland_d[0])
        self.assertAlmostEqual(endlat_d, self.portland_d[1])

    def test_npts_radians(self):
        # Calculate 10 points between Boston and Portland in degrees
        points_d = self.g.npts(
            lon1=self.boston_d[0],
            lat1=self.boston_d[1],
            lon2=self.portland_d[0],
            lat2=self.portland_d[1],
            npts=10,
            radians=False,
        )

        # Calculate 10 points between Boston and Portland in radians
        points_r = self.g.npts(
            lon1=self.boston_r[0],
            lat1=self.boston_r[1],
            lon2=self.portland_r[0],
            lat2=self.portland_r[1],
            npts=10,
            radians=True,
        )

        # Check they are equal
        for index, dpoint in enumerate(points_d):
            self.assertAlmostEqual(dpoint[0], math.degrees(points_r[index][0]))
            self.assertAlmostEqual(dpoint[1], math.degrees(points_r[index][1]))


class Geod_NaN_Issue112_Test(unittest.TestCase):
    # Test for Issue #112; Geod should silently propagate NaNs in input
    # to the output.
    def test_geod_nans(self):
        g = Geod(ellps="clrk66")
        (azi1, azi2, s12) = g.inv(43, 10, float("nan"), 20)
        self.assertTrue(azi1 != azi1)
        self.assertTrue(azi2 != azi2)
        self.assertTrue(s12 != s12)
        (azi1, azi2, s12) = g.inv(43, 10, 53, float("nan"))
        self.assertTrue(azi1 != azi1)
        self.assertTrue(azi2 != azi2)
        self.assertTrue(s12 != s12)
        # Illegal latitude is treated as NaN
        (azi1, azi2, s12) = g.inv(43, 10, 53, 91)
        self.assertTrue(azi1 != azi1)
        self.assertTrue(azi2 != azi2)
        self.assertTrue(s12 != s12)
        (lon2, lat2, azi2) = g.fwd(43, 10, float("nan"), 1e6)
        self.assertTrue(lon2 != lon2)
        self.assertTrue(lat2 != lat2)
        self.assertTrue(azi2 != azi2)
        (lon2, lat2, azi2) = g.fwd(43, 10, 20, float("nan"))
        self.assertTrue(lon2 != lon2)
        self.assertTrue(lat2 != lat2)
        self.assertTrue(azi2 != azi2)
        (lon2, lat2, azi2) = g.fwd(43, float("nan"), 20, 1e6)
        self.assertTrue(lon2 != lon2)
        self.assertTrue(lat2 != lat2)
        self.assertTrue(azi2 != azi2)
        # Illegal latitude is treated as NaN
        (lon2, lat2, azi2) = g.fwd(43, 91, 20, 1e6)
        self.assertTrue(lon2 != lon2)
        self.assertTrue(lat2 != lat2)
        self.assertTrue(azi2 != azi2)
        # Only lon2 is NaN
        (lon2, lat2, azi2) = g.fwd(float("nan"), 10, 20, 1e6)
        self.assertTrue(lon2 != lon2)
        self.assertTrue(lat2 == lat2)
        self.assertTrue(azi2 == azi2)


def test_proj_equals():
    assert Proj(4326) == Proj("epsg:4326")
    assert Proj(4326) != Proj("epsg:3857")
    with pytest.warns(UserWarning):
        assert Proj(4326) == Proj(Proj("epsg:4326").crs.to_proj4())


def test_initialize_proj_crs_no_proj4():
    proj = Proj(
        {
            "a": 6371229.0,
            "b": 6371229.0,
            "lon_0": -10.0,
            "o_lat_p": 30.0,
            "o_lon_p": 0.0,
            "o_proj": "longlat",
            "proj": "ob_tran",
        }
    )
    assert proj.srs.startswith("+proj=ob_tran")


def test_initialize_proj_crs_no_plus():
    proj = Proj("proj=lonlat")
    assert proj.crs.srs == "proj=lonlat type=crs"


def test_initialize_projparams_with_kwargs():
    proj_mixed_args = Proj("+proj=utm +zone=10", ellps="WGS84")
    proj_positional = Proj("+proj=utm +zone=10 +ellps=WGS84")
    assert proj_mixed_args.is_exact_same(proj_positional)


def test_equals_different_type():
    assert Proj("epsg:4326") != ""


def test_is_exact_same_different_type():
    assert not Proj("epsg:4326").is_exact_same(None)


def test_reset_errno():
    proj = Proj(
        {"proj": "laea", "lat_0": -90, "lon_0": 0, "a": 6371228.0, "units": "m"}
    )
    assert not proj.crs.is_geographic
    assert proj(0, 0, inverse=True, errcheck=True) == (0.0, -90.0)


@pytest.mark.parametrize("radians", [False, True])
def test_get_factors__2d_input(radians):
    transformer = Proj(3857)
    longitude = np.array([[0, 1], [2, 3]])
    latitude = np.array([[1, 2], [3, 4]])
    if radians:
        longitude = np.radians(longitude)
        latitude = np.radians(latitude)
    factors = transformer.get_factors(
        longitude=longitude, latitude=latitude, radians=radians
    )
    assert_almost_equal(
        factors.meridional_scale, [[1.0001523, 1.0006095], [1.0013723, 1.0024419]],
    )
    assert_almost_equal(
        factors.parallel_scale, [[1.0001523, 1.0006095], [1.0013723, 1.0024419]],
    )
    assert_almost_equal(
        factors.areal_scale, [[1.00030468, 1.00121946], [1.00274658, 1.00488976]],
    )
    assert_almost_equal(factors.angular_distortion, [[0, 0], [0, 0]], decimal=5)
    assert_almost_equal(
        factors.meridian_parallel_angle, [[89.99, 90], [90, 90]], decimal=2
    )
    assert_almost_equal(factors.meridian_convergence, [[0, 0], [0, 0]])
    assert_almost_equal(
        factors.tissot_semimajor, [[1.00015234, 1.00060955], [1.00137235, 1.0024419]],
    )
    assert_almost_equal(
        factors.tissot_semiminor, [[1.00015232, 1.00060953], [1.00137235, 1.0024419]],
    )
    assert_almost_equal(
        factors.dx_dlam, [[1, 1], [1, 1]],
    )
    assert_almost_equal(factors.dx_dphi, [[0, 0], [0, 0]])
    assert_almost_equal(factors.dy_dlam, [[0, 0], [0, 0]])
    assert_almost_equal(
        factors.dy_dphi, [[1.00015233, 1.00060954], [1.00137235, 1.0024419]],
    )


def test_get_factors():
    transformer = Proj(3717)
    factors = transformer.get_factors(-120, 34)
    assert_almost_equal(factors.meridional_scale, 1.0005466)
    assert_almost_equal(factors.parallel_scale, 1.0005466)
    assert_almost_equal(factors.areal_scale, 1.00109349)
    assert_almost_equal(factors.angular_distortion, 0)
    assert_almost_equal(factors.meridian_parallel_angle, 90)
    assert_almost_equal(factors.meridian_convergence, 1.67864770)
    assert_almost_equal(factors.tissot_semimajor, 1.00055, decimal=5)
    assert_almost_equal(factors.tissot_semiminor, 1.00055, decimal=5)
    assert_almost_equal(factors.dx_dlam, 0.8300039)
    assert_almost_equal(factors.dx_dphi, -0.0292052)
    assert_almost_equal(factors.dy_dlam, 0.0243244)
    assert_almost_equal(factors.dy_dphi, 0.9965495)


def test_get_factors__nan_inf():
    transformer = Proj(3857)
    factors = transformer.get_factors(
        longitude=[0, np.nan, np.inf, 0], latitude=[np.nan, 2, 2, np.inf]
    )
    assert_almost_equal(factors.meridional_scale, [np.inf, np.inf, np.inf, np.inf])
    assert_almost_equal(factors.parallel_scale, [np.inf, np.inf, np.inf, np.inf])
    assert_almost_equal(factors.areal_scale, [np.inf, np.inf, np.inf, np.inf])
    assert_almost_equal(factors.angular_distortion, [np.inf, np.inf, np.inf, np.inf])
    assert_almost_equal(
        factors.meridian_parallel_angle, [np.inf, np.inf, np.inf, np.inf]
    )
    assert_almost_equal(factors.meridian_convergence, [np.inf, np.inf, np.inf, np.inf])
    assert_almost_equal(factors.tissot_semimajor, [np.inf, np.inf, np.inf, np.inf])
    assert_almost_equal(factors.tissot_semiminor, [np.inf, np.inf, np.inf, np.inf])
    assert_almost_equal(factors.dx_dlam, [np.inf, np.inf, np.inf, np.inf])
    assert_almost_equal(factors.dx_dphi, [np.inf, np.inf, np.inf, np.inf])
    assert_almost_equal(factors.dy_dlam, [np.inf, np.inf, np.inf, np.inf])
    assert_almost_equal(factors.dy_dphi, [np.inf, np.inf, np.inf, np.inf])


def test_get_factors__errcheck():
    transformer = Proj(3857)
    with pytest.raises(ProjError):
        transformer.get_factors(longitude=40, latitude=70, errcheck=True, radians=True)


def test_numpy_bool_kwarg_false():
    # Issue 564
    south = np.array(50) < 0
    proj = Proj(
        proj="utm", zone=32, ellipsis="WGS84", datum="WGS84", units="m", south=south
    )
    assert "south" not in proj.srs


def test_numpy_bool_kwarg_true():
    # Issue 564
    south = np.array(50) > 0
    proj = Proj(
        proj="utm", zone=32, ellipsis="WGS84", datum="WGS84", units="m", south=south
    )
    assert "+south " in proj.srs


def test_proj_radians_warning():
    proj = Proj("epsg:4326")
    with pytest.warns(UserWarning, match="radian"):
        proj(1, 2, radians=True)
