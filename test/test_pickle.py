"""run test.py first!"""
import os
import pickle
import shutil
import tempfile
from contextlib import contextmanager

import numpy
from numpy.testing import assert_allclose

from pyproj import Proj

try:
    from time import perf_counter
except ImportError:
    from time import clock as perf_counter


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


def test_pickle():
    nx = 349
    ny = 277
    dx = 32463.41
    dy = dx
    print("do it again, from pickled instance ...")
    # find 4 lon/lat crnrs of AWIPS grid 221.
    llcrnrx = 0.0
    llcrnry = 0.0
    urcrnrx = dx * (nx - 1)
    urcrnry = dy * (ny - 1)
    dx = (urcrnrx - llcrnrx) / (nx - 1)
    dy = (urcrnry - llcrnry) / (ny - 1)
    x = llcrnrx + dx * numpy.indices((ny, nx), "f")[1, :, :]
    y = llcrnry + dy * numpy.indices((ny, nx), "f")[0, :, :]
    awips221_pre_pickle = Proj(proj="lcc", R=6371200, lat_1=50, lat_2=50, lon_0=-107)
    with temporary_directory() as tmpdir:
        with open(os.path.join(tmpdir, "test.pickle"), "wb") as pfh:
            pickle.dump(awips221_pre_pickle, pfh, -1)
        with open(os.path.join(tmpdir, "test.pickle"), "rb") as prh:
            awips221 = pickle.load(prh)
    t1 = perf_counter()
    lons, lats = awips221(x, y, inverse=True)
    t2 = perf_counter()
    print("compute lats/lons for all points on AWIPS 221 grid (%sx%s)" % (nx, ny))
    print("max/min lons in radians")
    print(
        numpy.minimum.reduce(numpy.ravel(lons)), numpy.maximum.reduce(numpy.ravel(lons))
    )
    print("max/min lats in radians")
    print(
        numpy.minimum.reduce(numpy.ravel(lats)), numpy.maximum.reduce(numpy.ravel(lats))
    )
    print("took", t2 - t1, "secs")
    # reverse transformation.
    t1 = perf_counter()
    xx, yy = awips221(lons, lats)
    t2 = perf_counter()
    print("max abs error for x")
    max_abs_err_x = numpy.maximum.reduce(numpy.fabs(numpy.ravel(x - xx)))
    print(max_abs_err_x)
    assert_allclose(max_abs_err_x, 0, atol=1e-4)
    print("max abs error for y")
    max_abs_err_y = numpy.maximum.reduce(numpy.fabs(numpy.ravel(y - yy)))
    print(max_abs_err_y)
    assert_allclose(max_abs_err_y, 0, atol=1e-4)
    print("took", t2 - t1, "secs")
