from numpy.testing import assert_almost_equal

from pyproj import Proj, transform


def test_datum():
    p1 = Proj(proj="latlong", datum="WGS84")
    s_1 = -111.5
    s_2 = 45.25919444444
    p2 = Proj(proj="utm", zone=10, datum="NAD27")
    x2, y2 = transform(p1, p2, s_1, s_2)
    assert_almost_equal((x2, y2), (1402291.0833290431, 5076289.591846835))
