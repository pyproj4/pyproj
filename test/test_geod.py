import itertools
import math
import os
import pickle
import shutil
import tempfile
from contextlib import contextmanager
from itertools import permutations

import numpy as np
import pytest
from numpy.testing import assert_almost_equal

from pyproj import Geod
from pyproj.geod import GeodIntermediateFlag

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
except ImportError:
    SHAPELY_LOADED = False


skip_shapely = pytest.mark.skipif(not SHAPELY_LOADED, reason="Missing shapely")


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
    true_az12 = -66.5305947876623
    true_az21 = 75.65363415556968
    print("from pyproj.Geod.inv:")
    az12, az21, dist = gg.inv(lon1pt, lat1pt, lon2pt, lat2pt)
    assert_almost_equal(
        (az12, az21, dist), (true_az12, true_az21, 4164192.708), decimal=3
    )

    print("forward transform")
    print("from proj.4 geod:")
    endlon, endlat, backaz = gg.fwd(lon1pt, lat1pt, az12, dist)
    assert_almost_equal(
        (endlon, endlat, backaz), (lon2pt, lat2pt, true_az21), decimal=3
    )

    inc_exc = ["excluding", "including"]
    res_az12_az21_dists_all = [
        (180.0, 0.0, 0.0),
        (-66.53059478766238, 106.79071710136431, 832838.5416198927),
        (-73.20928289863558, 99.32289055927389, 832838.5416198935),
        (-80.67710944072617, 91.36325611787134, 832838.5416198947),
        (-88.63674388212858, 83.32809401477382, 832838.5416198922),
        (-96.67190598522616, 75.65363415556973, 832838.5416198926),
    ]
    point_count = len(res_az12_az21_dists_all)
    for include_initial, include_terminus in itertools.product(
        (False, True), (False, True)
    ):
        initial_idx = int(not include_initial)
        terminus_idx = int(not include_terminus)

        npts = point_count - initial_idx - terminus_idx
        print("intermediate points:")
        print("from geod with +lat_1,+lon_1,+lat_2,+lon_2,+n_S:")
        print(f"{lat1pt:6.3f} {lon1pt:7.3f} {lat2pt:6.3f} {lon2pt:7.3f} {npts}")

        lonlats = gg.npts(
            lon1pt,
            lat1pt,
            lon2pt,
            lat2pt,
            npts,
            initial_idx=initial_idx,
            terminus_idx=terminus_idx,
        )
        assert len(lonlats) == npts

        npts1 = npts + initial_idx + terminus_idx - 1
        del_s = dist / npts1
        print(
            f"Total distnace is {dist}, "
            f"Points count: {npts}, "
            f"{inc_exc[include_initial]} initial point, "
            f"{inc_exc[include_terminus]} terminus point. "
            f"The distance between successive points is {dist}/{npts1} = {del_s}"
        )

        from_idx = initial_idx
        to_idx = point_count - terminus_idx
        res_az12_az21_dists = res_az12_az21_dists_all[from_idx:to_idx]

        lonprev = lon1pt
        latprev = lat1pt
        for (lon, lat), (res12, res21, resdist) in zip(lonlats, res_az12_az21_dists):
            o_az12, o_az21, o_dist = gg.inv(lonprev, latprev, lon, lat)
            if resdist == 0:
                assert_almost_equal(o_dist, 0)
            else:
                assert_almost_equal((o_az12, o_az21, o_dist), (res12, res21, resdist))
            latprev = lat
            lonprev = lon
        if not include_terminus:
            o_az12, o_az21, o_dist = gg.inv(lonprev, latprev, lon2pt, lat2pt)
            assert_almost_equal(
                (lat2pt, lon2pt, o_dist), (45.517, -123.683, 832838.542), decimal=3
            )

        if include_initial and include_terminus:
            lons, lats, azis12, azis21, dists = np.hstack(
                (lonlats, res_az12_az21_dists)
            ).transpose()

    del_s = dist / (point_count - 1)
    lons_a = np.empty(point_count)
    lats_a = np.empty(point_count)
    azis_a = np.empty(point_count)

    print("test inv_intermediate (by npts) with azi output")
    res = gg.inv_intermediate(
        out_lons=lons_a,
        out_lats=lats_a,
        out_azis=azis_a,
        lon1=lon1pt,
        lat1=lat1pt,
        lon2=lon2pt,
        lat2=lat2pt,
        npts=point_count,
        initial_idx=0,
        terminus_idx=0,
    )
    assert res.npts == point_count
    assert_almost_equal(res.del_s, del_s)
    assert_almost_equal(res.dist, dist)
    assert_almost_equal(res.lons, lons)
    assert_almost_equal(res.lats, lats)
    assert_almost_equal(res.azis[:-1], azis12[1:])
    assert res.lons is lons_a
    assert res.lats is lats_a
    assert res.azis is azis_a

    for flags in (GeodIntermediateFlag.AZIS_DISCARD, GeodIntermediateFlag.AZIS_KEEP):
        print("test inv_intermediate (by npts) without azi output, no buffers")
        res = gg.inv_intermediate(
            lon1=lon1pt,
            lat1=lat1pt,
            lon2=lon2pt,
            lat2=lat2pt,
            npts=point_count,
            initial_idx=0,
            terminus_idx=0,
            flags=flags,
        )
        assert res.npts == point_count
        assert_almost_equal(res.del_s, del_s)
        assert_almost_equal(res.dist, dist)
        assert_almost_equal(res.lons, lons_a)
        assert_almost_equal(res.lats, lats_a)
        if flags == GeodIntermediateFlag.AZIS_DISCARD:
            assert res.azis is None
        else:
            assert_almost_equal(res.azis, azis_a)

        lons_b = np.empty(point_count)
        lats_b = np.empty(point_count)
        azis_b = np.empty(point_count)

        print("test inv_intermediate (by npts) without azi output")
        res = gg.inv_intermediate(
            out_lons=lons_b,
            out_lats=lats_b,
            out_azis=None,
            lon1=lon1pt,
            lat1=lat1pt,
            lon2=lon2pt,
            lat2=lat2pt,
            npts=point_count,
            initial_idx=0,
            terminus_idx=0,
            flags=flags,
        )
        assert res.npts == point_count
        assert_almost_equal(res.del_s, del_s)
        assert_almost_equal(res.dist, dist)
        assert_almost_equal(res.lons, lons_a)
        assert_almost_equal(res.lats, lats_a)
        assert res.lons is lons_b
        assert res.lats is lats_b
        if flags == GeodIntermediateFlag.AZIS_DISCARD:
            assert res.azis is None
        else:
            assert_almost_equal(res.azis, azis_a)

    print("test fwd_intermediate")
    res = gg.fwd_intermediate(
        out_lons=lons_b,
        out_lats=lats_b,
        out_azis=azis_b,
        lon1=lon1pt,
        lat1=lat1pt,
        azi1=true_az12,
        npts=point_count,
        del_s=del_s,
        initial_idx=0,
        terminus_idx=0,
    )
    assert res.npts == point_count
    assert_almost_equal(res.del_s, del_s)
    assert_almost_equal(res.dist, dist)
    assert_almost_equal(res.lons, lons_a)
    assert_almost_equal(res.lats, lats_a)
    assert_almost_equal(res.azis, azis_a)
    assert res.lons is lons_b
    assert res.lats is lats_b
    assert res.azis is azis_b

    print("test inv_intermediate (by del_s)")
    for del_s_fact, flags in (
        (1, GeodIntermediateFlag.NPTS_ROUND),
        ((point_count - 0.5) / point_count, GeodIntermediateFlag.NPTS_TRUNC),
        ((point_count + 0.5) / point_count, GeodIntermediateFlag.NPTS_CEIL),
    ):
        res = gg.inv_intermediate(
            out_lons=lons_b,
            out_lats=lats_b,
            out_azis=azis_b,
            lon1=lon1pt,
            lat1=lat1pt,
            lon2=lon2pt,
            lat2=lat2pt,
            del_s=del_s * del_s_fact,
            initial_idx=0,
            terminus_idx=0,
            flags=flags,
        )
        assert res.npts == point_count
        assert_almost_equal(res.del_s, del_s)
        assert_almost_equal(res.dist, dist)
        assert_almost_equal(res.lons, lons_a)
        assert_almost_equal(res.lats, lats_a)
        assert_almost_equal(res.azis, azis_a)
        assert res.lons is lons_b
        assert res.lats is lats_b
        assert res.azis is azis_b


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


@pytest.mark.parametrize(
    "lons1,lats1,lons2", permutations([10.0, [10.0], (10.0,)])
)  # 6 test cases
def test_geod_inv_honours_input_types(lons1, lats1, lons2):
    # 622
    gg = Geod(ellps="clrk66")
    outx, outy, outz = gg.inv(lons1=lons1, lats1=lats1, lons2=lons2, lats2=0)
    assert isinstance(outx, type(lons1))
    assert isinstance(outy, type(lats1))
    assert isinstance(outz, type(lons2))


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
