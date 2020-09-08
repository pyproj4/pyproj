from pyproj.aoi import BBox


def test_backwards_compatible_import_paths():
    from pyproj.transformer import AreaOfInterest  # noqa: F401


def test_contains():
    assert BBox(1, 1, 4, 4).contains(BBox(2, 2, 3, 3))


def test_not_contains():
    assert not BBox(1, 1, 4, 4).contains(BBox(2, 2, 5, 5))


def test_intersects():
    assert BBox(1, 1, 4, 4).intersects(BBox(2, 2, 5, 5))


def test_not_intersects():
    assert not BBox(1, 1, 4, 4).intersects(BBox(10, 10, 20, 20))
