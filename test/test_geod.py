import os
import pickle
import shutil
import tempfile
from contextlib import contextmanager

from numpy.testing import assert_almost_equal

from pyproj import Geod


@contextmanager
def temporary_directory():
    """
    Get a temporary directory
    """
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


def test_geod_inverse_transform():
    gg = Geod(ellps="clrk66")
    lat1pt = 42.0 + (15.0 / 60.0)
    lon1pt = -71.0 - (7.0 / 60.0)
    lat2pt = 45.0 + (31.0 / 60.0)
    lon2pt = -123.0 - (41.0 / 60.0)
    """
    distance between boston and portland, clrk66:
    -66.531 75.654  4164192.708
    distance between boston and portland, WGS84:
    -66.530 75.654  4164074.239
    testing pickling of Geod instance
    distance between boston and portland, clrk66 (from pickle):
    -66.531 75.654  4164192.708
    distance between boston and portland, WGS84 (from pickle):
    -66.530 75.654  4164074.239
    inverse transform
    from proj.4 invgeod:
    b'-66.531\t75.654\t4164192.708\n'

    """
    print("from pyproj.Geod.inv:")
    az12, az21, dist = gg.inv(lon1pt, lat1pt, lon2pt, lat2pt)
    assert_almost_equal((az12, az21, dist), (-66.531, 75.654, 4164192.708), decimal=3)

    print("forward transform")
    print("from proj.4 geod:")
    endlon, endlat, backaz = gg.fwd(lon1pt, lat1pt, az12, dist)
    assert_almost_equal((endlon, endlat, backaz), (-123.683, 45.517, 75.654), decimal=3)
    print("intermediate points:")
    print("from geod with +lat_1,+lon_1,+lat_2,+lon_2,+n_S:")
    npts = 4
    lonlats = gg.npts(lon1pt, lat1pt, lon2pt, lat2pt, npts)
    lonprev = lon1pt
    latprev = lat1pt
    print(dist / (npts + 1))
    print("%6.3f  %7.3f" % (lat1pt, lon1pt))
    result_dists = (
        (-66.53059478766238, 106.79071710136431, 832838.5416198927),
        (-73.20928289863558, 99.32289055927389, 832838.5416198935),
        (-80.67710944072617, 91.36325611787134, 832838.5416198947),
        (-88.63674388212858, 83.32809401477382, 832838.5416198922),
    )
    for (lon, lat), (res12, res21, resdist) in zip(lonlats, result_dists):
        az12, az21, dist = gg.inv(lonprev, latprev, lon, lat)
        assert_almost_equal((az12, az21, dist), (res12, res21, resdist))
        latprev = lat
        lonprev = lon
    az12, az21, dist = gg.inv(lonprev, latprev, lon2pt, lat2pt)
    assert_almost_equal(
        (lat2pt, lon2pt, dist), (45.517, -123.683, 832838.542), decimal=3
    )


def test_geod_cities():
    # specify the lat/lons of some cities.
    boston_lat = 42.0 + (15.0 / 60.0)
    boston_lon = -71.0 - (7.0 / 60.0)
    portland_lat = 45.0 + (31.0 / 60.0)
    portland_lon = -123.0 - (41.0 / 60.0)
    g1 = Geod(ellps="clrk66")
    g2 = Geod(ellps="WGS84")
    az12, az21, dist = g1.inv(boston_lon, boston_lat, portland_lon, portland_lat)
    print("distance between boston and portland, clrk66:")
    print("%7.3f %6.3f %12.3f" % (az12, az21, dist))
    assert_almost_equal((az12, az21, dist), (-66.531, 75.654, 4164192.708), decimal=3)
    print("distance between boston and portland, WGS84:")
    az12, az21, dist = g2.inv(boston_lon, boston_lat, portland_lon, portland_lat)
    assert_almost_equal((az12, az21, dist), (-66.530, 75.654, 4164074.239), decimal=3)
    print("%7.3f %6.3f %12.3f" % (az12, az21, dist))
    print("testing pickling of Geod instance")
    with temporary_directory() as tmpdir:
        with open(os.path.join(tmpdir, "geod1.pickle"), "wb") as gp1w:
            pickle.dump(g1, gp1w, -1)
        with open(os.path.join(tmpdir, "geod2.pickle"), "wb") as gp2w:
            pickle.dump(g2, gp2w, -1)
        with open(os.path.join(tmpdir, "geod1.pickle"), "rb") as gp1:
            g3 = pickle.load(gp1)
        with open(os.path.join(tmpdir, "geod2.pickle"), "rb") as gp2:
            g4 = pickle.load(gp2)
    az12, az21, dist = g3.inv(boston_lon, boston_lat, portland_lon, portland_lat)
    assert_almost_equal((az12, az21, dist), (-66.531, 75.654, 4164192.708), decimal=3)
    print("distance between boston and portland, clrk66 (from pickle):")
    print("%7.3f %6.3f %12.3f" % (az12, az21, dist))
    az12, az21, dist = g4.inv(boston_lon, boston_lat, portland_lon, portland_lat)
    print("distance between boston and portland, WGS84 (from pickle):")
    print("%7.3f %6.3f %12.3f" % (az12, az21, dist))
    assert_almost_equal((az12, az21, dist), (-66.530, 75.654, 4164074.239), decimal=3)
    g3 = Geod("+ellps=clrk66")  # proj4 style init string
    print("inverse transform")
    lat1pt = 42.0 + (15.0 / 60.0)
    lon1pt = -71.0 - (7.0 / 60.0)
    lat2pt = 45.0 + (31.0 / 60.0)
    lon2pt = -123.0 - (41.0 / 60.0)
    az12, az21, dist = g3.inv(lon1pt, lat1pt, lon2pt, lat2pt)
    print("%7.3f %6.3f %12.3f" % (az12, az21, dist))
    assert_almost_equal((az12, az21, dist), (-66.531, 75.654, 4164192.708), decimal=3)
