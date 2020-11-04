import argparse
import os
import subprocess
import sys
from glob import glob
from pathlib import Path
from unittest.mock import patch

import pytest

from pyproj.__main__ import main
from pyproj.datadir import append_data_dir, get_data_dir, get_user_data_dir
from pyproj.sync import _load_grid_geojson
from test.conftest import grids_available, proj_env, tmp_chdir

PYPROJ_CLI_ENDPONTS = pytest.mark.parametrize(
    "input_command", [["pyproj"], [sys.executable, "-m", "pyproj"]]
)


@pytest.mark.cli
@PYPROJ_CLI_ENDPONTS
def test_main(input_command, tmpdir):
    with tmp_chdir(str(tmpdir)):
        output = subprocess.check_output(
            input_command, stderr=subprocess.STDOUT
        ).decode("utf-8")
    assert "pyproj version:" in output
    assert "PROJ version:" in output
    assert "-v, --verbose  Show verbose debugging version information." in output


@pytest.mark.cli
@PYPROJ_CLI_ENDPONTS
@pytest.mark.parametrize("option", ["-v", "--verbose"])
def test_main__verbose(input_command, option, tmpdir):
    with tmp_chdir(str(tmpdir)):
        output = subprocess.check_output(
            input_command + [option], stderr=subprocess.STDOUT
        ).decode("utf-8")
    assert "pyproj:" in output
    assert "PROJ:" in output
    assert "data dir" in output
    assert "user_data_dir" in output
    assert "System" in output
    assert "python" in output
    assert "Python deps" in output
    assert "-v, --verbose " not in output


@pytest.mark.cli
@PYPROJ_CLI_ENDPONTS
@pytest.mark.parametrize("option", [["-h"], []])
def test_sync(input_command, option, tmpdir):
    with tmp_chdir(str(tmpdir)):
        output = subprocess.check_output(
            input_command + ["sync"] + option, stderr=subprocess.STDOUT
        ).decode("utf-8")
    assert (
        "Tool for synchronizing PROJ datum and transformation support data." in output
    )
    assert "--bbox" in output
    assert "--spatial-test" in output
    assert "--source-id" in output
    assert "--area-of-use" in output
    assert "--file" in output
    assert "--exclude-world-coverage" in output
    assert "--include-already-downloaded" in output
    assert "--list-files" in output
    assert "--system-directory" in output
    assert "--target-directory" in output
    assert "-v, --verbose" in output


def _check_list_files_header(lines):
    assert lines[0].rstrip("\r") == "filename | source_id | area_of_use"
    assert lines[1].rstrip("\r") == "----------------------------------"


@pytest.mark.cli
@pytest.mark.network
@PYPROJ_CLI_ENDPONTS
def test_sync__source_id__list(input_command, tmpdir):
    with tmp_chdir(str(tmpdir)):
        output = subprocess.check_output(
            input_command
            + [
                "sync",
                "--source-id",
                "fr_ign",
                "--list-files",
                "--include-already-downloaded",
            ],
            stderr=subprocess.STDOUT,
        ).decode("utf-8")
    lines = output.strip().split("\n")
    assert len(lines) > 2
    _check_list_files_header(lines)
    for line in lines[2:]:
        assert "fr_ign" == line.split("|")[1].strip()


@pytest.mark.cli
@pytest.mark.network
@PYPROJ_CLI_ENDPONTS
def test_sync__area_of_use__list(input_command, tmpdir):
    with tmp_chdir(str(tmpdir)):
        output = subprocess.check_output(
            input_command
            + [
                "sync",
                "--area-of-use",
                "France",
                "--list-files",
                "--include-already-downloaded",
            ],
            stderr=subprocess.STDOUT,
        ).decode("utf-8")
    lines = output.strip().split("\n")
    assert len(lines) > 2
    _check_list_files_header(lines)
    for line in lines[2:]:
        assert "France" in line.split("|")[-1]


@pytest.mark.cli
@pytest.mark.network
@PYPROJ_CLI_ENDPONTS
def test_sync__file__list(input_command, tmpdir):
    with tmp_chdir(str(tmpdir)):
        output = subprocess.check_output(
            input_command
            + [
                "sync",
                "--file",
                "ntf_r93",
                "--list-files",
                "--include-already-downloaded",
            ],
            stderr=subprocess.STDOUT,
        ).decode("utf-8")
    lines = output.strip().split("\n")
    assert len(lines) > 2
    _check_list_files_header(lines)
    for line in lines[2:]:
        assert "ntf_r93" in line.split("|")[0]


@pytest.mark.cli
@pytest.mark.network
@PYPROJ_CLI_ENDPONTS
def test_sync__bbox__list(input_command, tmpdir):
    with tmp_chdir(str(tmpdir)):
        output = subprocess.check_output(
            input_command
            + [
                "sync",
                "--bbox",
                "2,49,3,50",
                "--list-files",
                "--include-already-downloaded",
            ],
            stderr=subprocess.STDOUT,
        ).decode("utf-8")
    lines = output.strip().split("\n")
    assert len(lines) > 2
    _check_list_files_header(lines)
    assert " | be_ign | " in output
    assert " | us_nga | " in output
    assert " | fr_ign | " in output


@pytest.mark.cli
@pytest.mark.network
@PYPROJ_CLI_ENDPONTS
def test_sync__bbox__list__exclude_world_coverage(input_command, tmpdir):
    with tmp_chdir(str(tmpdir)):
        output = subprocess.check_output(
            input_command
            + [
                "sync",
                "--bbox",
                "2,49,3,50",
                "--exclude-world-coverage",
                "--list-files",
                "--include-already-downloaded",
            ],
            stderr=subprocess.STDOUT,
        ).decode("utf-8")
    lines = output.strip().split("\n")
    assert len(lines) > 2
    _check_list_files_header(lines)
    assert " | be_ign | " in output
    assert " | us_nga | " not in output
    assert " | fr_ign | " in output


@pytest.mark.cli
@PYPROJ_CLI_ENDPONTS
@pytest.mark.parametrize(
    "extra_arg",
    [
        "--list-files",
        "--source-id",
        "--area-of-use",
        "--bbox",
        "--list-files",
        "--file",
    ],
)
def test_sync__all__exclusive_error(input_command, extra_arg, tmpdir):
    with tmp_chdir(str(tmpdir)), pytest.raises(subprocess.CalledProcessError):
        subprocess.check_output(
            input_command + ["sync", "--all", extra_arg], stderr=subprocess.STDOUT
        )


@pytest.mark.network
@patch(
    "pyproj.__main__.parser.parse_args",
    return_value=argparse.Namespace(
        bbox=None,
        list_files=False,
        file="ntf_r93",
        all=False,
        source_id=None,
        area_of_use=None,
        verbose=False,
        target_directory=None,
        system_directory=False,
        spatial_test="intersects",
        exclude_world_coverage=False,
        include_already_downloaded=True,
    ),
)
@patch("pyproj.__main__._download_resource_file")
def test_sync_download(download_mock, parse_args_mock):
    main()
    download_mock.assert_called_with(
        directory=get_user_data_dir(),
        file_url="https://cdn.proj.org/fr_ign_ntf_r93.tif",
        sha256="0aa738b3e00fd2d64f8e3cd0e76034d4792374624fa0e133922433c9491bbf2a",
        short_name="fr_ign_ntf_r93.tif",
        verbose=False,
    )


@pytest.mark.network
@patch(
    "pyproj.__main__.parser.parse_args",
    return_value=argparse.Namespace(
        bbox=None,
        list_files=False,
        file="ntf_r93",
        all=False,
        source_id=None,
        area_of_use=None,
        verbose=True,
        target_directory="test_directory",
        system_directory=False,
        spatial_test="intersects",
        exclude_world_coverage=False,
        include_already_downloaded=True,
    ),
)
@patch("pyproj.__main__._download_resource_file")
@patch("pyproj.sync._load_grid_geojson")
def test_sync_download__directory(
    load_grid_geojson_mock, download_mock, parse_args_mock
):
    load_grid_geojson_mock.return_value = _load_grid_geojson()
    main()
    download_mock.assert_called_with(
        directory="test_directory",
        file_url="https://cdn.proj.org/fr_ign_ntf_r93.tif",
        sha256="0aa738b3e00fd2d64f8e3cd0e76034d4792374624fa0e133922433c9491bbf2a",
        short_name="fr_ign_ntf_r93.tif",
        verbose=True,
    )
    load_grid_geojson_mock.assert_called_with(target_directory="test_directory")


@pytest.mark.network
@patch(
    "pyproj.__main__.parser.parse_args",
    return_value=argparse.Namespace(
        bbox=None,
        list_files=False,
        file="ntf_r93",
        all=False,
        source_id=None,
        area_of_use=None,
        verbose=True,
        target_directory=None,
        system_directory=True,
        spatial_test="intersects",
        exclude_world_coverage=False,
        include_already_downloaded=True,
    ),
)
@patch("pyproj.__main__._download_resource_file")
@patch("pyproj.sync._load_grid_geojson")
def test_sync_download__system_directory(
    load_grid_geojson_mock, download_mock, parse_args_mock
):
    load_grid_geojson_mock.return_value = _load_grid_geojson()
    main()
    datadir = get_data_dir().split(os.path.sep)[0]
    download_mock.assert_called_with(
        directory=datadir,
        file_url="https://cdn.proj.org/fr_ign_ntf_r93.tif",
        sha256="0aa738b3e00fd2d64f8e3cd0e76034d4792374624fa0e133922433c9491bbf2a",
        short_name="fr_ign_ntf_r93.tif",
        verbose=True,
    )
    load_grid_geojson_mock.assert_called_with(target_directory=datadir)


@pytest.mark.network
@patch("pyproj.__main__.parser.parse_args")
def test_sync__download_grids(parse_args_mock, tmp_path, capsys):
    parse_args_mock.return_value = argparse.Namespace(
        bbox=None,
        list_files=False,
        file="us_noaa_alaska",
        all=False,
        source_id=None,
        area_of_use=None,
        verbose=True,
        target_directory=str(tmp_path),
        system_directory=False,
        spatial_test="intersects",
        exclude_world_coverage=False,
        include_already_downloaded=False,
    )
    main()
    captured = capsys.readouterr()
    paths = sorted(Path(path).name for path in glob(str(tmp_path.joinpath("*"))))
    if grids_available("us_noaa_alaska.tif", check_network=False):
        assert paths == ["files.geojson"]
        assert captured.out == ""
    else:
        assert paths == ["files.geojson", "us_noaa_alaska.tif"]
        assert captured.out == "Downloading: https://cdn.proj.org/us_noaa_alaska.tif\n"
    # make sure not downloaded again
    with proj_env():
        append_data_dir(str(tmp_path))
        main()
        captured = capsys.readouterr()
        assert captured.out == ""
