from numpy.testing import assert_almost_equal

from pyproj.crs.datum import (
    CustomDatum,
    CustomEllipsoid,
    CustomPrimeMeridian,
    Ellipsoid,
    PrimeMeridian,
)


def test_custom_datum():
    cd = CustomDatum()
    assert cd.ellipsoid.name == "WGS 84"
    assert cd.prime_meridian.name == "Greenwich"


def test_custom_datum__input():
    cd = CustomDatum(
        ellipsoid=Ellipsoid.from_epsg(7001),
        prime_meridian=PrimeMeridian.from_name("Lisbon"),
    )
    assert cd.ellipsoid.name == "Airy 1830"
    assert cd.prime_meridian.name == "Lisbon"


def test_custom_ellipsoid():
    ce = CustomEllipsoid(semi_major_axis=6378137, inverse_flattening=298.257222101)
    assert ce.name == "undefined"
    assert ce.semi_major_metre == 6378137
    assert ce.semi_minor_metre == 6356752.314140356
    assert_almost_equal(ce.inverse_flattening, 298.257222101)
    assert sorted(ce.to_json_dict()) == [
        "$schema",
        "inverse_flattening",
        "name",
        "semi_major_axis",
        "type",
    ]


def test_custom_ellipsoid__minor():
    ce = CustomEllipsoid(
        name="test", semi_major_axis=6378137, semi_minor_axis=6356752.314
    )
    assert ce.name == "test"
    assert ce.semi_major_metre == 6378137
    assert ce.semi_minor_metre == 6356752.314
    assert_almost_equal(ce.inverse_flattening, 298.25722014)
    assert sorted(ce.to_json_dict()) == [
        "$schema",
        "name",
        "semi_major_axis",
        "semi_minor_axis",
        "type",
    ]


def test_custom_ellipsoid__radius():
    ce = CustomEllipsoid(radius=6378137)
    assert ce.name == "undefined"
    assert ce.semi_major_metre == 6378137
    assert ce.semi_minor_metre == 6378137
    assert ce.inverse_flattening == 0
    assert sorted(ce.to_json_dict()) == ["$schema", "name", "radius", "type"]


def test_custom_prime_meridian():
    pm = CustomPrimeMeridian(longitude=2)
    assert pm.name == "undefined"
    assert pm.longitude == 2


def test_custom_prime_meridian__name():
    pm = CustomPrimeMeridian(longitude=1, name="frank")
    assert pm.name == "frank"
    assert pm.longitude == 1
