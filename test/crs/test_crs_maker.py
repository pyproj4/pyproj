from distutils.version import LooseVersion

import pytest

from pyproj import __proj_version__
from pyproj.crs import (
    BoundCRS,
    CompoundCRS,
    DerivedGeographicCRS,
    GeographicCRS,
    ProjectedCRS,
    VerticalCRS,
)
from pyproj.crs.coordinate_operation import (
    AlbersEqualAreaConversion,
    LambertConformalConic2SPConversion,
    RotatedLatitudeLongitudeConversion,
    ToWGS84Transformation,
    TransverseMercatorConversion,
    UTMConversion,
)
from pyproj.crs.coordinate_system import Cartesian2DCS, Ellipsoidal3DCS, VerticalCS
from pyproj.crs.datum import CustomDatum
from pyproj.crs.enums import VerticalCSAxis


def test_make_projected_crs():
    aeaop = AlbersEqualAreaConversion(0, 0)
    pc = ProjectedCRS(conversion=aeaop, name="Albers")
    assert pc.name == "Albers"
    assert pc.type_name == "Projected CRS"
    assert pc.coordinate_operation == aeaop


def test_make_geographic_crs():
    gc = GeographicCRS(name="WGS 84")
    assert gc.name == "WGS 84"
    assert gc.type_name == "Geographic 2D CRS"
    assert gc.to_authority() == ("OGC", "CRS84")


def test_make_geographic_3d_crs():
    gcrs = GeographicCRS(ellipsoidal_cs=Ellipsoidal3DCS())
    assert gcrs.type_name == "Geographic 3D CRS"
    assert gcrs.to_authority() == ("IGNF", "WGS84GEODD")


def test_make_derived_geographic_crs():
    conversion = RotatedLatitudeLongitudeConversion(o_lat_p=0, o_lon_p=0)
    dgc = DerivedGeographicCRS(base_crs=GeographicCRS(), conversion=conversion)
    assert dgc.name == "undefined"
    assert dgc.type_name == "Geographic 2D CRS"
    assert dgc.coordinate_operation == conversion


def test_vertical_crs():
    vc = VerticalCRS(
        name="NAVD88 height",
        datum="North American Vertical Datum 1988",
        geoid_model="GEOID12B",
    )
    assert vc.name == "NAVD88 height"
    assert vc.type_name == "Vertical CRS"
    assert vc.coordinate_system == VerticalCS()
    if LooseVersion(__proj_version__) >= LooseVersion("6.3.0"):
        assert vc.to_json_dict()["geoid_model"]["name"] == "GEOID12B"


@pytest.mark.parametrize(
    "axis",
    [
        VerticalCSAxis.UP,
        VerticalCSAxis.UP_FT,
        VerticalCSAxis.DEPTH,
        VerticalCSAxis.DEPTH_FT,
        VerticalCSAxis.GRAVITY_HEIGHT_FT,
    ],
)
def test_vertical_crs__chance_cs_axis(axis):
    vc = VerticalCRS(
        name="NAVD88 height",
        datum="North American Vertical Datum 1988",
        vertical_cs=VerticalCS(axis=axis),
    )
    assert vc.name == "NAVD88 height"
    assert vc.type_name == "Vertical CRS"
    assert vc.coordinate_system == VerticalCS(axis=axis)


def test_compund_crs():
    vertcrs = VerticalCRS(
        name="NAVD88 height",
        datum="North American Vertical Datum 1988",
        vertical_cs=VerticalCS(),
        geoid_model="GEOID12B",
    )
    projcrs = ProjectedCRS(
        name="NAD83 / Pennsylvania South",
        conversion=LambertConformalConic2SPConversion(
            latitude_false_origin=39.3333333333333,
            longitude_false_origin=-77.75,
            latitude_first_parallel=40.9666666666667,
            latitude_second_parallel=39.9333333333333,
            easting_false_origin=600000,
            northing_false_origin=0,
        ),
        geodetic_crs=GeographicCRS(datum="North American Datum 1983"),
        cartesian_cs=Cartesian2DCS(),
    )
    compcrs = CompoundCRS(
        name="NAD83 / Pennsylvania South + NAVD88 height", components=[projcrs, vertcrs]
    )
    assert compcrs.name == "NAD83 / Pennsylvania South + NAVD88 height"
    assert compcrs.type_name == "Compound CRS"
    assert compcrs.sub_crs_list[0].type_name == "Projected CRS"
    assert compcrs.sub_crs_list[1].type_name == "Vertical CRS"


def test_bound_crs():
    proj_crs = ProjectedCRS(conversion=UTMConversion(12))
    bound_crs = BoundCRS(
        source_crs=proj_crs,
        target_crs="WGS 84",
        transformation=ToWGS84Transformation(
            proj_crs.geodetic_crs, 1, 2, 3, 4, 5, 6, 7
        ),
    )
    assert bound_crs.type_name == "Bound CRS"
    assert bound_crs.source_crs.coordinate_operation.name == "UTM zone 12N"
    assert bound_crs.coordinate_operation.towgs84 == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
    assert bound_crs.target_crs.name == "WGS 84"


def test_bound_crs__example():
    proj_crs = ProjectedCRS(
        conversion=TransverseMercatorConversion(
            latitude_natural_origin=0,
            longitude_natural_origin=15,
            false_easting=2520000,
            false_northing=0,
            scale_factor_natural_origin=0.9996,
        ),
        geodetic_crs=GeographicCRS(
            datum=CustomDatum(ellipsoid="International 1909 (Hayford)")
        ),
    )
    bound_crs = BoundCRS(
        source_crs=proj_crs,
        target_crs="WGS 84",
        transformation=ToWGS84Transformation(
            proj_crs.geodetic_crs, -122.74, -34.27, -22.83, -1.884, -3.4, -3.03, -15.62
        ),
    )
    with pytest.warns(UserWarning):
        assert bound_crs.to_dict() == {
            "ellps": "intl",
            "k": 0.9996,
            "lat_0": 0,
            "lon_0": 15,
            "no_defs": None,
            "proj": "tmerc",
            "towgs84": [-122.74, -34.27, -22.83, -1.884, -3.4, -3.03, -15.62],
            "type": "crs",
            "units": "m",
            "x_0": 2520000,
            "y_0": 0,
        }
