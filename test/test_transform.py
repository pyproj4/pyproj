import numpy
import pytest
from numpy.testing import assert_allclose

from pyproj import Proj, __proj_version__, transform


def test_transform():
    # convert awips221 grid to awips218 coordinate system
    # (grids defined at http://www.nco.ncep.noaa.gov/pmb/docs/on388/tableb.html)
    nx = 614
    ny = 428
    dx = 12190.58
    dy = dx
    awips221 = Proj(proj="lcc", R=6371200, lat_1=50, lat_2=50, lon_0=-107)
    print("proj4 library version = ", __proj_version__)
    llcrnrx, llcrnry = awips221(-145.5, 1)
    awips221 = Proj(
        proj="lcc",
        R=6371200,
        lat_1=50,
        lat_2=50,
        lon_0=-107,
        x_0=-llcrnrx,
        y_0=-llcrnry,
    )
    assert_allclose(awips221(-145.5, 1), (0, 0), atol=1e-4)
    awips218 = Proj(proj="lcc", R=6371200, lat_1=25, lat_2=25, lon_0=-95)
    llcrnrx, llcrnry = awips218(-133.459, 12.19)
    awips218 = Proj(
        proj="lcc", R=6371200, lat_1=25, lat_2=25, lon_0=-95, x_0=-llcrnrx, y_0=-llcrnry
    )
    assert_allclose(awips218(-133.459, 12.19), (0, 0), atol=1e-4)
    x1 = dx * numpy.indices((ny, nx), "f")[1, :, :]
    y1 = dy * numpy.indices((ny, nx), "f")[0, :, :]
    print("max/min x and y for awips218 grid")
    print(numpy.minimum.reduce(numpy.ravel(x1)), numpy.maximum.reduce(numpy.ravel(x1)))
    print(numpy.minimum.reduce(numpy.ravel(y1)), numpy.maximum.reduce(numpy.ravel(y1)))
    with pytest.warns(DeprecationWarning):
        x2, y2 = transform(awips218, awips221, x1, y1)
    print("max/min x and y for awips218 grid in awips221 coordinates")
    print(numpy.minimum.reduce(numpy.ravel(x2)), numpy.maximum.reduce(numpy.ravel(x2)))
    print(numpy.minimum.reduce(numpy.ravel(y2)), numpy.maximum.reduce(numpy.ravel(y2)))
    with pytest.warns(DeprecationWarning):
        x3, y3 = transform(awips221, awips218, x2, y2)
    print("error for reverse transformation back to awips218 coords")
    print("(should be close to zero)")
    assert_allclose(numpy.minimum.reduce(numpy.ravel(x3 - x1)), 0, atol=1e-4)
    assert_allclose(numpy.maximum.reduce(numpy.ravel(x3 - x1)), 0, atol=1e-4)
    assert_allclose(numpy.minimum.reduce(numpy.ravel(y3 - y1)), 0, atol=1e-4)
    assert_allclose(numpy.maximum.reduce(numpy.ravel(y3 - y1)), 0, atol=1e-4)


def test_skip_equivalent():
    with pytest.warns(DeprecationWarning):
        xeq, yeq = transform(4326, 4326, 30, 60, skip_equivalent=True)
    assert (xeq, yeq) == (30, 60)
