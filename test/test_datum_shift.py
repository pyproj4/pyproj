import pytest
from numpy.testing import assert_almost_equal

from pyproj import Proj, transform

# illustrates the use of the transform function to
# perform coordinate transformations with datum shifts.
#
#  This example is from Roberto Vidmar
#
#        Test point is Trieste, Molo Sartorio
#
#  This data come from the Istituto Geografico Militare (IGM), as well as
#  the 7 parameters to transform from Gauss-Boaga (our reference frame)
#  to WGS84
#
#                WGS84 Lat:  45d38'49.879" (45.647188611)
#                WGS84 Lon:  13d45'34.397" (13.759554722)
#                WGS84 z:    52.80;
#                UTM 33:     403340.97   5055597.17
#                GB:         2423346.99  5055619.87

UTM_x = 403340.9672367854
UTM_y = 5055597.175553089
GB_x = 2423346.99
GB_y = 5055619.87
WGS84_lat = 45.647188611  # Degrees
WGS84_lon = 13.759554722  # Degrees
UTM_z = WGS84_z = 52.8  # Ellipsoidical height in meters
WGS84_PROJ = Proj(proj="latlong", datum="WGS84")
UTM_33_PROJ = Proj(proj="utm", zone="33")
GAUSSSB_PROJ = Proj(
    init="epsg:26592", towgs84="-122.74,-34.27,-22.83,-1.884,-3.400,-3.030,-15.62"
)
print("proj4 library version = ", WGS84_PROJ.proj_version)


def test_shift_wgs84_to_utm33():
    xutm33, yutm33, zutm33 = transform(
        WGS84_PROJ, UTM_33_PROJ, WGS84_lon, WGS84_lat, WGS84_z
    )
    assert_almost_equal((xutm33, yutm33, zutm33), (UTM_x, UTM_y, UTM_z))


def test_shift_utm33_to_wgs84():
    back_lon, back_lat, back_z = transform(UTM_33_PROJ, WGS84_PROJ, UTM_x, UTM_y, UTM_z)
    assert_almost_equal((back_lon, back_lat, back_z), (WGS84_lon, WGS84_lat, WGS84_z))


@pytest.mark.xfail
def test_shift_wgs84_to_gaussb_no_ellisoidal_height():
    xgb, ygb, zgb = transform(WGS84_PROJ, GAUSSSB_PROJ, WGS84_lon, WGS84_lat, 0)
    assert_almost_equal((xgb, ygb, zgb), (GB_x, GB_y, 0))
    # 1.9.6
    # (2423346.995008026, 5055619.899023423, 0.16683581471443176)
    # 2.1.3
    # (1453270.7157727296, 5146884.706783104, 0.0)


@pytest.mark.xfail
def test_shift_gaussb_to_wgs84_no_ellisoidal_height():
    back_lon, back_lat, back_z = transform(GAUSSSB_PROJ, WGS84_PROJ, GB_x, GB_y, 0)
    assert_almost_equal((back_lon, back_lat, back_z), (WGS84_lon, WGS84_lat, 0))
    # 1.9.6
    # (13.759554641526984, 45.64718834776721, -0.16560534108430147)
    # 2.1.3
    # (26.21239770046797, 45.64699807457936, 0.0)
