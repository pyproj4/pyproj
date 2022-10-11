import pytest
from numpy.testing import assert_almost_equal

from pyproj import CRS, Proj, transform
from test.conftest import grids_available


@pytest.mark.grid
@pytest.mark.parametrize("proj_class", [Proj, CRS])
def test_datum(proj_class):
    p1 = proj_class(proj="latlong", datum="WGS84")
    s_1 = -111.5
    s_2 = 45.25919444444
    p2 = proj_class(proj="utm", zone=10, datum="NAD27")
    with pytest.warns(FutureWarning):
        x2, y2 = transform(p1, p2, s_1, s_2)
    if grids_available("us_noaa_emhpgn.tif"):
        assert_almost_equal((x2, y2), (1402286.33, 5076292.30), decimal=2)
    elif grids_available("us_noaa_conus.tif"):
        assert_almost_equal((x2, y2), (1402285.98, 5076292.42), decimal=2)
    else:
        # https://github.com/OSGeo/PROJ/issues/1808
        assert_almost_equal((x2, y2), (1402288.54, 5076296.64), decimal=2)
