"""Tests for dynamic reference frames in coordinate reference systems."""

import pytest

from pyproj import CRS
from pyproj._version import PROJ_COMPILED_VERSION


@pytest.mark.skipif(PROJ_COMPILED_VERSION < (9, 9, 0), reason="requires PROJ 9.9")
@pytest.mark.parametrize(
    ("crs", "expected"),
    [
        ("EPSG:9990", True),  # ITRF2020 dynamic geodetic reference frame
        ("EPSG:4258", False),  # ETRS89 static geodetic reference frame
        ("EPSG:5628", True),  # dynamic compound CRS
        ("EPSG:6871", False),  # static compound CRS
        ("EPSG:9000+5703", True),  # dynamic horizontal plus static vertical
    ],
)
def test_is_dynamic(crs, expected):
    assert CRS(crs).is_dynamic is expected


@pytest.mark.skipif(PROJ_COMPILED_VERSION >= (9, 9, 0), reason="requires older PROJ")
def test_is_dynamic_unsupported_proj():
    with pytest.raises(NotImplementedError, match="PROJ 9.9"):
        CRS("EPSG:4258").is_dynamic
