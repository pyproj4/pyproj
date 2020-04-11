import array

import numpy
from numpy.testing import assert_allclose

from pyproj import Proj, __proj_version__

try:
    from time import perf_counter
except ImportError:
    from time import clock as perf_counter


def test_awips221():
    params = {}
    params["proj"] = "lcc"
    params["R"] = 6371200
    params["lat_1"] = 50
    params["lat_2"] = 50
    params["lon_0"] = -107
    nx = 349
    ny = 277
    dx = 32463.41
    dy = dx
    # can either use a dict
    # awips221 = Proj(params)
    # or keyword args
    awips221 = Proj(proj="lcc", R=6371200, lat_1=50, lat_2=50, lon_0=-107)
    print("proj4 library version = ", __proj_version__)
    # AWIPS grid 221 parameters
    # (from http://www.nco.ncep.noaa.gov/pmb/docs/on388/tableb.html)
    llcrnrx, llcrnry = awips221(-145.5, 1.0)
    params["x_0"] = -llcrnrx
    params["y_0"] = -llcrnry
    awips221 = Proj(params)
    llcrnrx, llcrnry = awips221(-145.5, 1.0)
    # find 4 lon/lat crnrs of AWIPS grid 221.
    llcrnrx = 0.0
    llcrnry = 0.0
    lrcrnrx = dx * (nx - 1)
    lrcrnry = 0.0
    ulcrnrx = 0.0
    ulcrnry = dy * (ny - 1)
    urcrnrx = dx * (nx - 1)
    urcrnry = dy * (ny - 1)
    llcrnrlon, llcrnrlat = awips221(llcrnrx, llcrnry, inverse=True)
    lrcrnrlon, lrcrnrlat = awips221(lrcrnrx, lrcrnry, inverse=True)
    urcrnrlon, urcrnrlat = awips221(urcrnrx, urcrnry, inverse=True)
    ulcrnrlon, ulcrnrlat = awips221(ulcrnrx, ulcrnry, inverse=True)
    print("4 crnrs of AWIPS grid 221:")
    print(llcrnrlon, llcrnrlat)
    print(lrcrnrlon, lrcrnrlat)
    print(urcrnrlon, urcrnrlat)
    print(ulcrnrlon, ulcrnrlat)
    print("from GRIB docs")
    print("(see http://www.nco.ncep.noaa.gov/pmb/docs/on388/tableb.html)")
    print("   -145.5  1.0")
    print("   -68.318 0.897")
    print("   -2.566 46.352")
    print("   148.639 46.635")
    # compute lons and lats for the whole AWIPS grid 221 (377x249).
    dx = (urcrnrx - llcrnrx) / (nx - 1)
    dy = (urcrnry - llcrnry) / (ny - 1)
    x = llcrnrx + dx * numpy.indices((ny, nx), "f")[1, :, :]
    y = llcrnry + dy * numpy.indices((ny, nx), "f")[0, :, :]
    t1 = perf_counter()
    lons, lats = awips221(
        numpy.ravel(x).tolist(), numpy.ravel(y).tolist(), inverse=True
    )
    t2 = perf_counter()
    print("data in lists:")
    print("compute lats/lons for all points on AWIPS 221 grid (%sx%s)" % (nx, ny))
    print("max/min lons")
    print(min(lons), max(lons))
    print("max/min lats")
    print(min(lats), max(lats))
    print("took", t2 - t1, "secs")
    xa = array.array("f", numpy.ravel(x).tolist())
    ya = array.array("f", numpy.ravel(y).tolist())
    t1 = perf_counter()
    lons, lats = awips221(xa, ya, inverse=True)
    t2 = perf_counter()
    print("data in python arrays:")
    print("compute lats/lons for all points on AWIPS 221 grid (%sx%s)" % (nx, ny))
    print("max/min lons")
    print(min(lons), max(lons))
    print("max/min lats")
    print(min(lats), max(lats))
    print("took", t2 - t1, "secs")
    t1 = perf_counter()
    lons, lats = awips221(x, y, inverse=True)
    t2 = perf_counter()
    print("data in a numpy array:")
    print("compute lats/lons for all points on AWIPS 221 grid (%sx%s)" % (nx, ny))
    print("max/min lons")
    print(
        numpy.minimum.reduce(numpy.ravel(lons)), numpy.maximum.reduce(numpy.ravel(lons))
    )
    print("max/min lats")
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
    print("compare output with sample.out")
