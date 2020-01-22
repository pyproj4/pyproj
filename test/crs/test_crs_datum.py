from pyproj.crs.datum import CustomDatum, Ellipsoid, PrimeMeridian


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
