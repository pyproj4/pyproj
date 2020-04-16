from distutils.version import LooseVersion

import pytest
from numpy.testing import assert_almost_equal

from pyproj import CRS, Proj, __proj_version__, transform
from test.conftest import grids_available


@pytest.mark.parametrize("proj_class", [Proj, CRS])
def test_datum(proj_class):
    p1 = proj_class(proj="latlong", datum="WGS84")
    s_1 = -111.5
    s_2 = 45.25919444444
    p2 = proj_class(proj="utm", zone=10, datum="NAD27")
    with pytest.warns(DeprecationWarning):
        x2, y2 = transform(p1, p2, s_1, s_2)
    if LooseVersion(__proj_version__) < LooseVersion("6.3.0"):
        assert_almost_equal(
            (x2, y2), (1402291.0833290431, 5076289.591846835), decimal=2
        )
    else:
        if grids_available("ca_nrc_ntv2_0.tif"):
            assert_almost_equal((x2, y2), (1402286.3333203, 5076292.2955777), decimal=2)
        else:
            # https://github.com/OSGeo/PROJ/issues/1808
            assert_almost_equal((x2, y2), (1402285.9829252, 5076292.4212746), decimal=2)
