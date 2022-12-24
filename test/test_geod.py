import math
import pickle
from contextlib import nullcontext
from itertools import permutations

import numpy
import pytest
from numpy.testing import assert_almost_equal

from pyproj import Geod
from pyproj.geod import GeodIntermediateFlag, reverse_azimuth

try:
    from shapely.geometry import (
        LinearRing,
        LineString,
        MultiLineString,
        MultiPoint,
        MultiPolygon,
        Point,
        Polygon,
    )
    from shapely.geometry.polygon import orient

    SHAPELY_LOADED = True
except (ImportError, OSError):
    SHAPELY_LOADED = False


skip_shapely = pytest.mark.skipif(not SHAPELY_LOADED, reason="Missing shapely")


# BOSTON
_BOSTON_LAT = 42.0 + (15.0 / 60.0)
_BOSTON_LON = -71.0 - (7.0 / 60.0)
# PORTLAND
_PORTLAND_LAT = 45.0 + (31.0 / 60.0)
_PORTLAND_LON = -123.0 - (41.0 / 60.0)


@pytest.mark.parametrize("return_back_azimuth", [True, False])
@pytest.mark.parametrize(
    "ellipsoid,true_az12,true_az21,expected_distance",
    [
        ("clrk66", -66.5305947876623, 75.65363415556968, 4164192.708),
        ("WGS84", -66.5305947876623, 75.65363415556968, 4164074.239),
    ],
)
def test_geodesic_inv(
    ellipsoid,
    true_az12,
    true_az21,
    expected_distance,
    return_back_azimuth,
    scalar_and_array,
):
    geod = Geod(ellps=ellipsoid)
    az12, az21, dist = geod.inv(
        scalar_and_array(_BOSTON_LON),
        scalar_and_array(_BOSTON_LAT),
        scalar_and_array(_PORTLAND_LON),
        scalar_and_array(_PORTLAND_LAT),
        return_back_azimuth=return_back_azimuth,
    )
    if not return_back_azimuth:
        az21 = reverse_azimuth(az21)
    assert_almost_equal(
        (az12, az21, dist),
        (
            scalar_and_array(true_az12),
            scalar_and_array(true_az21),
            scalar_and_array(expected_distance),
        ),
        decimal=3,
    )


@pytest.mark.parametrize(
    "lon_start,lat_start,lon_end,lat_end,res12,res21,resdist",
    [
        (_BOSTON_LON, _BOSTON_LAT, _BOSTON_LON, _BOSTON_LAT, 180.0, 0.0, 0.0),
        (
            _BOSTON_LON,
            _BOSTON_LAT,
            -80.79664651607472,
            44.83744724383204,
            -66.53059478766238,
            106.79071710136431,
            832838.5416198927,
        ),
        (
            -80.79664651607472,
            44.83744724383204,
            -91.21816704002396,
            46.536201500764776,
            -73.20928289863558,
            99.32289055927389,
            832838.5416198935,
        ),
        (
            -91.21816704002396,
            46.536201500764776,
            -102.10621593474447,
            47.236494630072166,
            -80.67710944072617,
            91.36325611787134,
            832838.5416198947,
        ),
        (
            -102.10621593474447,
            47.236494630072166,
            -113.06616309750775,
            46.88821539471925,
            -88.63674388212858,
            83.32809401477382,
            832838.5416198922,
        ),
        (
            -113.06616309750775,
            46.88821539471925,
            _PORTLAND_LON,
            _PORTLAND_LAT,
            -96.67190598522616,
            75.65363415556973,
            832838.5416198926,
        ),
    ],
)
def test_geodesic_inv__multiple_points(
    lon_start, lat_start, lon_end, lat_end, res12, res21, resdist, scalar_and_array
):
    geod = Geod(ellps="clrk66")
    o_az12, o_az21, o_dist = geod.inv(
        scalar_and_array(lon_start),
        scalar_and_array(lat_start),
        scalar_and_array(lon_end),
        scalar_and_array(lat_end),
    )
    assert_almost_equal(
        (o_az12, o_az21, o_dist),
        (scalar_and_array(res12), scalar_and_array(res21), scalar_and_array(resdist)),
    )


@pytest.mark.parametrize(
    "flag", [GeodIntermediateFlag.AZIS_DISCARD, GeodIntermediateFlag.AZIS_KEEP]
)
def test_geodesic_inv_intermediate__azis_flag(flag):
    geod = Geod(ellps="clrk66")
    point_count = 7
    res = geod.inv_intermediate(
        lon1=_BOSTON_LON,
        lat1=_BOSTON_LAT,
        lon2=_PORTLAND_LON,
        lat2=_PORTLAND_LAT,
        npts=point_count,
        initial_idx=0,
        terminus_idx=0,
        flags=flag,
        return_back_azimuth=False,
    )
    assert res.npts == point_count
    assert_almost_equal(res.del_s, 694032.1180165777)
    assert_almost_equal(res.dist, 4164192.7080994663)
    assert_almost_equal(
        res.lons,
        [
            _BOSTON_LON,
            -79.12667425528419,
            -87.67579185665936,
            -96.62666097960022,
            -105.7727853838606,
            -114.86985739838673,
            _PORTLAND_LON,
        ],
    )
    assert_almost_equal(
        res.lats,
        [
            _BOSTON_LAT,
            44.46434542986116,
            46.07643938331146,
            47.0159762562249,
            47.23724050253994,
            46.72890509939583,
            _PORTLAND_LAT,
        ],
    )
    if flag == GeodIntermediateFlag.AZIS_DISCARD:
        assert res.azis is None
    else:
        assert_almost_equal(
            res.azis,
            [
                -66.5305947876623,
                -72.03560255472611,
                -78.11540731053181,
                -84.61959820187617,
                -91.32904268899453,
                -97.98697931255812,
                -104.34636584443031,
            ],
        )


@pytest.mark.parametrize(
    "flag", [GeodIntermediateFlag.AZIS_DISCARD, GeodIntermediateFlag.AZIS_KEEP]
)
def test_geodesic_inv_intermediate__azis_flag__numpy(flag):
    geod = Geod(ellps="clrk66")
    point_count = 3
    lons_b = numpy.empty(point_count)
    lats_b = numpy.empty(point_count)
    res = geod.inv_intermediate(
        out_lons=lons_b,
        out_lats=lats_b,
        lon1=_BOSTON_LON,
        lat1=_BOSTON_LAT,
        lon2=_PORTLAND_LON,
        lat2=_PORTLAND_LAT,
        npts=point_count,
        initial_idx=0,
        terminus_idx=0,
        flags=flag,
        return_back_azimuth=False,
    )
    assert res.npts == point_count
    assert_almost_equal(res.del_s, 2082096.3540497331)
    assert_almost_equal(res.dist, 4164192.7080994663)
    assert_almost_equal(res.lons, [_BOSTON_LON, -96.62666098, _PORTLAND_LON])
    assert_almost_equal(
        res.lats,
        [_BOSTON_LAT, 47.01597626, _PORTLAND_LAT],
    )
    if flag == GeodIntermediateFlag.AZIS_DISCARD:
        assert res.azis is None
    else:
        assert_almost_equal(
            res.azis,
            [-66.5305947876623, -84.61959820187617, -104.34636584443031],
        )
    assert res.lons is lons_b
    assert res.lats is lats_b


@pytest.mark.parametrize("return_back_azimuth", [True, False])
def test_geodesic_inv_intermediate__numpy(return_back_azimuth):
    geod = Geod(ellps="clrk66")
    point_count = 5
    lons = numpy.empty(point_count)
    lats = numpy.empty(point_count)
    azis = numpy.empty(point_count)

    with pytest.warns(UserWarning) if return_back_azimuth is None else nullcontext():
        res = geod.inv_intermediate(
            out_lons=lons,
            out_lats=lats,
            out_azis=azis,
            lon1=_BOSTON_LON,
            lat1=_BOSTON_LAT,
            lon2=_PORTLAND_LON,
            lat2=_PORTLAND_LAT,
            npts=point_count,
            initial_idx=0,
            terminus_idx=0,
            return_back_azimuth=return_back_azimuth,
        )
    assert res.npts == point_count
    assert_almost_equal(res.del_s, 1041048.1770248666)
    assert_almost_equal(res.dist, 4164192.7080994663)
    assert_almost_equal(
        res.lons,
        [_BOSTON_LON, -83.34061499, -96.62666098, -110.34292364, _PORTLAND_LON],
    )
    assert_almost_equal(
        res.lats, [_BOSTON_LAT, 45.35049848, 47.01597626, 47.07350417, _PORTLAND_LAT]
    )
    out_azis = res.azis[:-1]
    if return_back_azimuth in [True, None]:
        out_azis = reverse_azimuth(out_azis)
    assert_almost_equal(
        out_azis, [-66.53059479, -75.01125433, -84.6195982, -94.68069764]
    )
    assert res.lons is lons
    assert res.lats is lats
    assert res.azis is azis


@pytest.mark.parametrize(
    "del_s_fact,flag",
    [
        (1, GeodIntermediateFlag.NPTS_ROUND),
        (4.5 / 5, GeodIntermediateFlag.NPTS_TRUNC),
        (5.5 / 5, GeodIntermediateFlag.NPTS_CEIL),
    ],
)
def test_geodesic_inv_intermediate__del_s__numpy(del_s_fact, flag):
    geod = Geod(ellps="clrk66")
    point_count = 5
    lons = numpy.empty(point_count)
    lats = numpy.empty(point_count)
    azis = numpy.empty(point_count)
    dist = 4164192.7080994663
    del_s = dist / (point_count - 1)
    res = geod.inv_intermediate(
        out_lons=lons,
        out_lats=lats,
        out_azis=azis,
        lon1=_BOSTON_LON,
        lat1=_BOSTON_LAT,
        lon2=_PORTLAND_LON,
        lat2=_PORTLAND_LAT,
        del_s=del_s * del_s_fact,
        initial_idx=0,
        terminus_idx=0,
        flags=flag,
        return_back_azimuth=False,
    )
    assert res.npts == point_count
    assert_almost_equal(res.del_s, del_s)
    assert_almost_equal(res.dist, dist)
    assert_almost_equal(
        res.lons,
        [_BOSTON_LON, -83.34061499, -96.62666098, -110.34292364, _PORTLAND_LON],
    )
    assert_almost_equal(
        res.lats, [_BOSTON_LAT, 45.35049848, 47.01597626, 47.07350417, _PORTLAND_LAT]
    )
    assert_almost_equal(
        res.azis[:-1], [-66.53059479, -75.01125433, -84.6195982, -94.68069764]
    )
    assert res.lons is lons
    assert res.lats is lats
    assert res.azis is azis


@pytest.mark.parametrize("return_back_azimuth", [True, False])
def test_geodesic_fwd_intermediate__numpy(return_back_azimuth):
    geod = Geod(ellps="clrk66")
    point_count = 5
    lons = numpy.empty(point_count)
    lats = numpy.empty(point_count)
    azis = numpy.empty(point_count)
    true_az12 = -66.5305947876623
    dist = 4164192.7080994663
    del_s = dist / (point_count - 1)
    with pytest.warns(UserWarning) if return_back_azimuth is None else nullcontext():
        res = geod.fwd_intermediate(
            out_lons=lons,
            out_lats=lats,
            out_azis=azis,
            lon1=_BOSTON_LON,
            lat1=_BOSTON_LAT,
            azi1=true_az12,
            npts=point_count,
            del_s=del_s,
            initial_idx=0,
            terminus_idx=0,
            return_back_azimuth=return_back_azimuth,
        )
    assert res.npts == point_count
    assert res.lons is lons
    assert res.lats is lats
    assert res.azis is azis
    assert_almost_equal(res.del_s, del_s)
    assert_almost_equal(res.dist, dist)
    assert_almost_equal(
        res.lons,
        [-71.11666667, -83.34061499, -96.62666098, -110.34292364, -123.68333333],
    )
    assert_almost_equal(
        res.lats, [42.25, 45.35049848, 47.01597626, 47.07350417, 45.51666667]
    )
    if return_back_azimuth in [True, None]:
        azis = reverse_azimuth(azis)
    assert_almost_equal(
        azis, [-66.53059479, -75.01125433, -84.6195982, -94.68069764, -104.34636584]
    )


@pytest.mark.parametrize("return_back_azimuth", [True, False])
@pytest.mark.parametrize(
    "ellipsoid,true_az12,true_az21,expected_distance",
    [
        ("clrk66", -66.5305947876623, 75.65363415556968, 4164192.708),
        ("WGS84", -66.5305947876623, 75.65363415556968, 4164074.239),
    ],
)
def test_geodesic_fwd(
    ellipsoid,
    true_az12,
    true_az21,
    expected_distance,
    return_back_azimuth,
    scalar_and_array,
):
    geod = Geod(ellps=ellipsoid)
    endlon, endlat, backaz = geod.fwd(
        scalar_and_array(_BOSTON_LON),
        scalar_and_array(_BOSTON_LAT),
        scalar_and_array(true_az12),
        scalar_and_array(expected_distance),
        return_back_azimuth=return_back_azimuth,
    )
    if not return_back_azimuth:
        backaz = reverse_azimuth(backaz)
    assert_almost_equal(
        (endlon, endlat, backaz),
        (
            scalar_and_array(_PORTLAND_LON),
            scalar_and_array(_PORTLAND_LAT),
            scalar_and_array(true_az21),
        ),
        decimal=3,
    )


@pytest.mark.parametrize("include_initial", [True, False])
@pytest.mark.parametrize("include_terminus", [True, False])
def test_geodesic_npts(include_initial, include_terminus):
    geod = Geod(ellps="clrk66")
    initial_idx = int(not include_initial)
    terminus_idx = int(not include_terminus)
    lonlats = geod.npts(
        _BOSTON_LON,
        _BOSTON_LAT,
        _PORTLAND_LON,
        _PORTLAND_LAT,
        npts=6 - initial_idx - terminus_idx,
        initial_idx=initial_idx,
        terminus_idx=terminus_idx,
    )
    expected_lonlats = [
        (-80.797, 44.837),
        (-91.218, 46.536),
        (-102.106, 47.236),
        (-113.066, 46.888),
    ]
    if include_initial:
        expected_lonlats.insert(0, (_BOSTON_LON, _BOSTON_LAT))
    if include_terminus:
        expected_lonlats.append((_PORTLAND_LON, _PORTLAND_LAT))
    assert_almost_equal(lonlats, expected_lonlats, decimal=3)


@pytest.mark.parametrize(
    "ellipsoid,expected_azi12,expected_az21,expected_dist",
    [("clrk66", -66.531, 75.654, 4164192.708), ("WGS84", -66.530, 75.654, 4164074.239)],
)
def test_geodesic_inv__pickle(
    ellipsoid, expected_azi12, expected_az21, expected_dist, tmp_path, scalar_and_array
):
    geod = Geod(ellps=ellipsoid)
    az12, az21, dist = geod.inv(
        scalar_and_array(_BOSTON_LON),
        scalar_and_array(_BOSTON_LAT),
        scalar_and_array(_PORTLAND_LON),
        scalar_and_array(_PORTLAND_LAT),
    )
    assert_almost_equal(
        (az12, az21, dist),
        (
            scalar_and_array(expected_azi12),
            scalar_and_array(expected_az21),
            scalar_and_array(expected_dist),
        ),
        decimal=3,
    )
    pickle_file = tmp_path / "geod1.pickle"
    with open(pickle_file, "wb") as gp1w:
        pickle.dump(geod, gp1w, -1)
    with open(pickle_file, "rb") as gp1:
        geod_pickle = pickle.load(gp1)
    pickle_az12, pickle_az21, pickle_dist = geod_pickle.inv(
        scalar_and_array(_BOSTON_LON),
        scalar_and_array(_BOSTON_LAT),
        scalar_and_array(_PORTLAND_LON),
        scalar_and_array(_PORTLAND_LAT),
    )
    assert_almost_equal(
        (pickle_az12, pickle_az21, pickle_dist),
        (
            scalar_and_array(expected_azi12),
            scalar_and_array(expected_az21),
            scalar_and_array(expected_dist),
        ),
        decimal=3,
    )


def test_geodesic_inv__string_init(scalar_and_array):
    geod = Geod("+ellps=clrk66")
    az12, az21, dist = geod.inv(
        scalar_and_array(_BOSTON_LON),
        scalar_and_array(_BOSTON_LAT),
        scalar_and_array(_PORTLAND_LON),
        scalar_and_array(_PORTLAND_LAT),
    )
    assert_almost_equal(
        (az12, az21, dist),
        (
            scalar_and_array(-66.531),
            scalar_and_array(75.654),
            scalar_and_array(4164192.708),
        ),
        decimal=3,
    )


def test_line_length__single_point():
    geod = Geod(ellps="WGS84")
    assert geod.line_length(1, 1) == 0


def test_line_length__radians():
    geod = Geod(ellps="WGS84")
    total_length = geod.line_length([1, 2], [0.5, 1], radians=True)
    assert_almost_equal(total_length, 5426061.32197463, decimal=3)


def test_line_lengths__single_point():
    geod = Geod(ellps="WGS84")
    assert geod.line_lengths(1, 1) == 0


def test_line_lengths__radians():
    geod = Geod(ellps="WGS84")
    line_lengths = geod.line_lengths([1, 2], [0.5, 1], radians=True)
    assert_almost_equal(line_lengths, [5426061.32197463], decimal=3)


def test_polygon_area_perimeter__single_point():
    geod = Geod(ellps="WGS84")
    area, perimeter = geod.polygon_area_perimeter(1, 1)
    assert area == 0
    assert perimeter == 0


@skip_shapely
def test_geometry_length__point():
    geod = Geod(ellps="WGS84")
    assert geod.geometry_length(Point(1, 2)) == 0


@skip_shapely
def test_geometry_length__linestring():
    geod = Geod(ellps="WGS84")
    assert_almost_equal(
        geod.geometry_length(LineString([Point(1, 2), Point(3, 4)])),
        313588.39721259556,
        decimal=2,
    )


@skip_shapely
def test_geometry_length__linestring__radians():
    geod = Geod(ellps="WGS84")
    assert_almost_equal(
        geod.geometry_length(
            LineString(
                [
                    Point(math.radians(1), math.radians(2)),
                    Point(math.radians(3), math.radians(4)),
                ]
            ),
            radians=True,
        ),
        313588.39721259556,
        decimal=2,
    )


@skip_shapely
def test_geometry_length__linearring():
    geod = Geod(ellps="WGS84")
    assert_almost_equal(
        geod.geometry_length(
            LinearRing(LineString([Point(1, 2), Point(3, 4), Point(5, 2)]))
        ),
        1072185.2103813463,
        decimal=2,
    )


@skip_shapely
def test_geometry_length__polygon():
    geod = Geod(ellps="WGS84")
    assert_almost_equal(
        geod.geometry_length(
            Polygon(LineString([Point(1, 2), Point(3, 4), Point(5, 2)]))
        ),
        1072185.2103813463,
        decimal=2,
    )


@skip_shapely
def test_geometry_length__polygon__radians():
    geod = Geod(ellps="WGS84")
    assert_almost_equal(
        geod.geometry_length(
            Polygon(
                LineString(
                    [
                        Point(math.radians(1), math.radians(2)),
                        Point(math.radians(3), math.radians(4)),
                        Point(math.radians(5), math.radians(2)),
                    ]
                )
            ),
            radians=True,
        ),
        1072185.2103813463,
        decimal=2,
    )


@skip_shapely
def test_geometry_length__multipolygon():
    geod = Geod(ellps="WGS84")
    polygon = Polygon(LineString([Point(1, 2), Point(3, 4), Point(5, 2)]))
    assert_almost_equal(
        geod.geometry_length(MultiPolygon([polygon, polygon])),
        2 * 1072185.2103813463,
        decimal=2,
    )


@skip_shapely
def test_geometry_length__multipolygon__radians():
    geod = Geod(ellps="WGS84")
    polygon = Polygon(
        LineString(
            [
                Point(math.radians(1), math.radians(2)),
                Point(math.radians(3), math.radians(4)),
                Point(math.radians(5), math.radians(2)),
            ]
        )
    )
    assert_almost_equal(
        geod.geometry_length(MultiPolygon([polygon, polygon]), radians=True),
        2 * 1072185.2103813463,
        decimal=2,
    )


@skip_shapely
def test_geometry_length__multilinestring():
    geod = Geod(ellps="WGS84")
    line_string = LineString([Point(1, 2), Point(3, 4), Point(5, 2)])
    assert_almost_equal(
        geod.geometry_length(MultiLineString([line_string, line_string])),
        1254353.5888503822,
        decimal=2,
    )


@skip_shapely
def test_geometry_length__multipoint():
    geod = Geod(ellps="WGS84")
    assert (
        geod.geometry_length(MultiPoint([Point(1, 2), Point(3, 4), Point(5, 2)])) == 0
    )


@skip_shapely
def test_geometry_area_perimeter__point():
    geod = Geod(ellps="WGS84")
    assert geod.geometry_area_perimeter(Point(1, 2)) == (0, 0)


@skip_shapely
def test_geometry_area_perimeter__linestring():
    geod = Geod(ellps="WGS84")
    assert_almost_equal(
        geod.geometry_area_perimeter(LineString([Point(1, 2), Point(3, 4)])),
        (0.0, 627176.7944251911),
        decimal=2,
    )


@skip_shapely
def test_geometry_area_perimeter__linestring__radians():
    geod = Geod(ellps="WGS84")
    assert_almost_equal(
        geod.geometry_area_perimeter(
            LineString(
                [
                    Point(math.radians(1), math.radians(2)),
                    Point(math.radians(3), math.radians(4)),
                ]
            ),
            radians=True,
        ),
        (0.0, 627176.7944251911),
        decimal=2,
    )


@skip_shapely
def test_geometry_area_perimeter__linearring():
    geod = Geod(ellps="WGS84")
    assert_almost_equal(
        geod.geometry_area_perimeter(
            LinearRing(LineString([Point(1, 2), Point(3, 4), Point(5, 2)]))
        ),
        (-49187690467.58623, 1072185.2103813463),
        decimal=2,
    )


@skip_shapely
def test_geometry_area_perimeter__polygon():
    geod = Geod(ellps="WGS84")
    assert_almost_equal(
        geod.geometry_area_perimeter(
            Polygon(LineString([Point(1, 2), Point(3, 4), Point(5, 2)]))
        ),
        (-49187690467.58623, 1072185.2103813463),
        decimal=2,
    )


@skip_shapely
def test_geometry_area_perimeter__polygon__radians():
    geod = Geod(ellps="WGS84")
    assert_almost_equal(
        geod.geometry_area_perimeter(
            Polygon(
                LineString(
                    [
                        Point(math.radians(1), math.radians(2)),
                        Point(math.radians(3), math.radians(4)),
                        Point(math.radians(5), math.radians(2)),
                    ]
                )
            ),
            radians=True,
        ),
        (-49187690467.58623, 1072185.2103813463),
        decimal=2,
    )


@skip_shapely
def test_geometry_area_perimeter__polygon__holes():
    geod = Geod(ellps="WGS84")

    polygon = Polygon(
        LineString([Point(1, 1), Point(1, 10), Point(10, 10), Point(10, 1)]),
        holes=[LineString([Point(1, 2), Point(3, 4), Point(5, 2)])],
    )

    assert_almost_equal(
        geod.geometry_area_perimeter(orient(polygon, 1)),
        (944373881400.3394, 3979008.0359657984),
        decimal=2,
    )

    assert_almost_equal(
        geod.geometry_area_perimeter(orient(polygon, -1)),
        (-944373881400.3394, 3979008.0359657984),
        decimal=2,
    )


@skip_shapely
def test_geometry_area_perimeter__multipolygon():
    geod = Geod(ellps="WGS84")
    polygon = Polygon(LineString([Point(1, 2), Point(3, 4), Point(5, 2)]))
    assert_almost_equal(
        geod.geometry_area_perimeter(MultiPolygon([polygon, polygon])),
        (-98375380935.17245, 2144370.4207626926),
        decimal=2,
    )


@skip_shapely
def test_geometry_area_perimeter__multipolygon__radians():
    geod = Geod(ellps="WGS84")
    polygon = Polygon(
        LineString(
            [
                Point(math.radians(1), math.radians(2)),
                Point(math.radians(3), math.radians(4)),
                Point(math.radians(5), math.radians(2)),
            ]
        )
    )
    assert_almost_equal(
        geod.geometry_area_perimeter(MultiPolygon([polygon, polygon]), radians=True),
        (-98375380935.17245, 2144370.4207626926),
        decimal=2,
    )


@skip_shapely
def test_geometry_area_perimeter__multilinestring():
    geod = Geod(ellps="WGS84")
    line_string = LineString([Point(1, 2), Point(3, 4), Point(5, 2)])
    assert_almost_equal(
        geod.geometry_area_perimeter(MultiLineString([line_string, line_string])),
        (-98375380935.17245, 2144370.4207626926),
        decimal=2,
    )


@skip_shapely
def test_geometry_area_perimeter__multipoint():
    geod = Geod(ellps="WGS84")
    assert geod.geometry_area_perimeter(
        MultiPoint([Point(1, 2), Point(3, 4), Point(5, 2)])
    ) == (0, 0)


@pytest.mark.parametrize(
    "lon,lat,az", permutations([10.0, [10.0], (10.0,)])
)  # 6 test cases
def test_geod_fwd_honours_input_types(lon, lat, az):
    # 622
    gg = Geod(ellps="clrk66")
    outx, outy, outz = gg.fwd(lons=lon, lats=lat, az=az, dist=0)
    assert isinstance(outx, type(lon))
    assert isinstance(outy, type(lat))
    assert isinstance(outz, type(az))


def test_geod_fwd_radians():
    g = Geod(ellps="clrk66")
    lon1 = 1
    lat1 = 1
    az1 = 1
    dist = 1
    assert_almost_equal(
        numpy.rad2deg(g.fwd(lon1, lat1, az1, dist, radians=True)),
        g.fwd(lon1 * 180 / numpy.pi, lat1 * 180 / numpy.pi, az1 * 180 / numpy.pi, dist),
    )


def test_geod_inv_radians():
    g = Geod(ellps="clrk66")
    lon1 = 0
    lat1 = 0
    lon2 = 1
    lat2 = 1
    # the third output is in distance, so we don't want to change from deg-rad there
    out_rad = list(g.inv(lon1, lat1, lon2, lat2, radians=True))
    out_rad[0] *= 180 / numpy.pi
    out_rad[1] *= 180 / numpy.pi
    assert_almost_equal(
        out_rad,
        g.inv(
            lon1 * 180 / numpy.pi,
            lat1 * 180 / numpy.pi,
            lon2 * 180 / numpy.pi,
            lat2 * 180 / numpy.pi,
        ),
    )


@pytest.mark.parametrize("func_name", ("fwd", "inv"))
@pytest.mark.parametrize("radians", (True, False))
def test_geod_scalar_array(func_name, radians):
    # verify two singlepoint calculations match an array of length two
    g = Geod(ellps="clrk66")
    func = getattr(g, func_name)
    assert_almost_equal(
        numpy.transpose([func(0, 0, 1, 1, radians=radians) for i in range(2)]),
        func([0, 0], [0, 0], [1, 1], [1, 1], radians=radians),
    )


@pytest.mark.parametrize(
    "lons1,lats1,lons2", permutations([10.0, [10.0], (10.0,), numpy.array([10.0])], 3)
)  # 6 test cases
def test_geod_inv_honours_input_types(lons1, lats1, lons2):
    # 622
    gg = Geod(ellps="clrk66")
    outx, outy, outz = gg.inv(lons1=lons1, lats1=lats1, lons2=lons2, lats2=0)
    assert isinstance(outx, type(lons1))
    assert isinstance(outy, type(lats1))
    assert isinstance(outz, type(lons2))


def test_geodesic_fwd_inv_inplace():
    gg = Geod(ellps="clrk66")
    _BOSTON_LON = numpy.array([0], dtype=numpy.float64)
    _BOSTON_LAT = numpy.array([0], dtype=numpy.float64)
    _PORTLAND_LON = numpy.array([1], dtype=numpy.float64)
    _PORTLAND_LAT = numpy.array([1], dtype=numpy.float64)

    az12, az21, dist = gg.inv(
        _BOSTON_LON, _BOSTON_LAT, _PORTLAND_LON, _PORTLAND_LAT, inplace=True
    )
    assert az12 is _BOSTON_LON
    assert az21 is _BOSTON_LAT
    assert dist is _PORTLAND_LON

    endlon, endlat, backaz = gg.fwd(_BOSTON_LON, _BOSTON_LAT, az12, dist, inplace=True)
    assert endlon is _BOSTON_LON
    assert endlat is _BOSTON_LAT
    assert backaz is az12


@pytest.mark.parametrize("kwarg", ["b", "f", "es", "rf", "e"])
def test_geod__build_kwargs(kwarg):
    gg = Geod(ellps="clrk66")
    if kwarg == "rf":
        value = 1.0 / gg.f
    elif kwarg == "e":
        value = math.sqrt(gg.es)
    else:
        value = getattr(gg, kwarg)
    gg2 = Geod(a=gg.a, **{kwarg: value})
    assert_almost_equal(gg.a, gg2.a)
    assert_almost_equal(gg.b, gg2.b)
    assert_almost_equal(gg.f, gg2.f)
    assert_almost_equal(gg.es, gg2.es)


@pytest.mark.parametrize("radians", [False, True])
def test_geod__reverse_azimuth(radians):
    f = math.pi / 180 if radians else 1
    xy = numpy.array(
        [
            [0, 0 + 180],
            [180, 180 - 180],
            [-180, -180 + 180],
            [10, 10 - 180],
            [20, 20 - 180],
            [-10, -10 + 180],
        ]
    )
    for x, y in xy:
        assert_almost_equal(reverse_azimuth(x * f, radians=radians), y * f)

    xx = xy.T[0]
    yy = xy.T[1]
    assert_almost_equal(reverse_azimuth(xx * f, radians=radians), yy * f)
