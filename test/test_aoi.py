import pytest

from pyproj.aoi import AreaOfInterest, BBox


def test_backwards_compatible_import_paths():
    from pyproj.transformer import (  # noqa: F401 pylint: disable=unused-import
        AreaOfInterest,
    )


def test_contains():
    assert BBox(1, 1, 4, 4).contains(BBox(2, 2, 3, 3))


def test_not_contains():
    assert not BBox(1, 1, 4, 4).contains(BBox(2, 2, 5, 5))


def test_intersects():
    assert BBox(1, 1, 4, 4).intersects(BBox(2, 2, 5, 5))


def test_not_intersects():
    assert not BBox(1, 1, 4, 4).intersects(BBox(10, 10, 20, 20))


@pytest.mark.parametrize("aoi_class", [AreaOfInterest, BBox])
@pytest.mark.parametrize(
    "input",
    [
        (None, None, None, None),
        (float("nan"), float("nan"), float("nan"), float("nan")),
        (None, 0, 0, 0),
        (float("nan"), 0, 0, 0),
        (0, None, 0, 0),
        (0, float("nan"), 0, 0),
        (0, 0, None, 0),
        (0, 0, float("nan"), 0),
        (0, 0, 0, None),
        (0, 0, 0, float("nan")),
    ],
)
def test_null_input(aoi_class, input):
    with pytest.raises(ValueError, match="NaN or None values are not allowed."):
        aoi_class(*input)
