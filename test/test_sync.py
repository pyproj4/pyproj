from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from urllib.error import URLError

import pytest

from pyproj.aoi import BBox
from pyproj.sync import (
    _download_resource_file,
    _load_grid_geojson,
    _sha256sum,
    get_transform_grid_list,
)


@pytest.mark.network
def test_get_transform_grid_list():
    grids = get_transform_grid_list(include_already_downloaded=True)
    assert len(grids) > 200


@pytest.mark.network
def test_get_transform_grid_list__bbox__antimeridian():
    grids = get_transform_grid_list(
        bbox=BBox(170, -90, -170, 90), include_already_downloaded=True
    )
    assert len(grids) > 10
    source_ids = set()
    for grid in grids:
        source_ids.add(grid["properties"]["source_id"])
    assert sorted(source_ids) == [
        "au_ga",
        "nc_dittt",
        "nz_linz",
        "us_nga",
        "us_noaa",
    ]


@pytest.mark.network
def test_get_transform_grid_list__bbox__out_of_bounds():
    grids = get_transform_grid_list(
        bbox=BBox(170, -90, 190, 90), include_already_downloaded=True
    )
    assert len(grids) > 10
    source_ids = set()
    for grid in grids:
        source_ids.add(grid["properties"]["source_id"])
    assert sorted(source_ids) == [
        "au_ga",
        "nc_dittt",
        "nz_linz",
        "us_nga",
        "us_noaa",
    ]


@pytest.mark.network
def test_get_transform_grid_list__source_id():
    grids = get_transform_grid_list(
        bbox=BBox(170, -90, -170, 90),
        source_id="us_noaa",
        include_already_downloaded=True,
    )
    assert len(grids) > 5
    source_ids = set()
    for grid in grids:
        source_ids.add(grid["properties"]["source_id"])
    assert sorted(source_ids) == ["us_noaa"]


@pytest.mark.network
def test_get_transform_grid_list__contains():
    grids = get_transform_grid_list(
        bbox=BBox(170, -90, -170, 90),
        spatial_test="contains",
        include_already_downloaded=True,
    )
    assert len(grids) > 5
    source_ids = set()
    for grid in grids:
        source_ids.add(grid["properties"]["source_id"])
    assert sorted(source_ids) == ["nz_linz"]


@pytest.mark.network
def test_get_transform_grid_list__file():
    grids = get_transform_grid_list(
        filename="us_noaa_alaska", include_already_downloaded=True
    )
    assert len(grids) == 1
    assert grids[0]["properties"]["name"] == "us_noaa_alaska.tif"


@pytest.mark.network
def test_get_transform_grid_list__area_of_use():
    grids = get_transform_grid_list(area_of_use="USA", include_already_downloaded=True)
    assert len(grids) > 10
    for grid in grids:
        assert "USA" in grid["properties"]["area_of_use"]


def test_sha256sum(tmp_path):
    test_file = tmp_path / "test.file"
    test_file.write_text("TEST")
    assert (
        _sha256sum(test_file)
        == "94ee059335e587e501cc4bf90613e0814f00a7b08bc7c648fd865a2af6a22cc2"
    )


@patch("pyproj.sync.urlretrieve", autospec=True)
@pytest.mark.parametrize("verbose", [True, False])
def test_download_resource_file(urlretrieve_mock, verbose, tmp_path, capsys):
    def dummy_urlretrieve(url, local_path):
        with open(local_path, "w") as testf:
            testf.write("TEST")

    urlretrieve_mock.side_effect = dummy_urlretrieve
    _download_resource_file(
        file_url="test_url",
        short_name="test_file.txt",
        directory=tmp_path,
        verbose=verbose,
        sha256="94ee059335e587e501cc4bf90613e0814f00a7b08bc7c648fd865a2af6a22cc2",
    )
    urlretrieve_mock.assert_called_with("test_url", tmp_path / "test_file.txt.part")
    captured = capsys.readouterr()
    if not verbose:
        assert captured.out == ""
    else:
        assert captured.out == "Downloading: test_url\n"
    expected_file = tmp_path / "test_file.txt"
    assert expected_file.exists()
    assert (
        _sha256sum(expected_file)
        == "94ee059335e587e501cc4bf90613e0814f00a7b08bc7c648fd865a2af6a22cc2"
    )


@patch("pyproj.sync.urlretrieve", autospec=True)
def test_download_resource_file__nosha256(urlretrieve_mock, tmp_path):
    def dummy_urlretrieve(url, local_path):
        local_path.touch()

    urlretrieve_mock.side_effect = dummy_urlretrieve
    _download_resource_file(
        file_url="test_url", short_name="test_file.txt", directory=tmp_path
    )
    urlretrieve_mock.assert_called_with("test_url", tmp_path / "test_file.txt.part")
    expected_file = tmp_path / "test_file.txt"
    assert expected_file.exists()


@patch("pyproj.sync.urlretrieve", autospec=True)
def test_download_resource_file__exception(urlretrieve_mock, tmp_path):
    def dummy_urlretrieve(url, local_path):
        local_path.touch()
        raise URLError("Test")

    urlretrieve_mock.side_effect = dummy_urlretrieve
    with pytest.raises(URLError):
        _download_resource_file(
            file_url="test_url",
            short_name="test_file.txt",
            directory=str(tmp_path),
            verbose=False,
            sha256="test",
        )
    urlretrieve_mock.assert_called_with("test_url", tmp_path / "test_file.txt.part")
    assert not tmp_path.joinpath("test_file.txt.part").exists()
    assert not tmp_path.joinpath("test_file.txt").exists()


@patch("pyproj.sync.urlretrieve", autospec=True)
def test_download_resource_file__bad_sha256sum(urlretrieve_mock, tmp_path):
    def dummy_urlretrieve(url, local_path):
        local_path.touch()

    urlretrieve_mock.side_effect = dummy_urlretrieve
    with pytest.raises(RuntimeError, match="SHA256 mismatch: test_file.txt"):
        _download_resource_file(
            file_url="test_url",
            short_name="test_file.txt",
            directory=tmp_path,
            verbose=False,
            sha256="test",
        )
    urlretrieve_mock.assert_called_with("test_url", tmp_path / "test_file.txt.part")
    assert not tmp_path.joinpath("test_file.txt.part").exists()
    assert not tmp_path.joinpath("test_file.txt").exists()


@pytest.mark.network
@patch("pyproj.sync.Path.stat")
def test__load_grid_geojson_old_file(stat_mock, tmp_path):
    return_timestamp = MagicMock()
    return_timestamp.st_mtime = (datetime.utcnow() - timedelta(days=2)).timestamp()
    stat_mock.return_value = return_timestamp
    tmp_path.joinpath("files.geojson").touch()
    grids = _load_grid_geojson(target_directory=tmp_path)
    assert sorted(grids) == ["features", "name", "type"]
