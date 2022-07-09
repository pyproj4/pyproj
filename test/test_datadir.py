import logging
import os
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest

import pyproj._datadir
from pyproj import CRS, Transformer, get_codes, set_use_global_context
from pyproj._datadir import _pyproj_global_context_initialize
from pyproj.datadir import (
    DataDirError,
    append_data_dir,
    get_data_dir,
    get_user_data_dir,
    set_data_dir,
)
from pyproj.enums import PJType
from pyproj.exceptions import CRSError
from test.conftest import proj_env


@contextmanager
def proj_context_env():
    """
    Ensure setting for global context is the same at the end.
    """
    context = pyproj._datadir._USE_GLOBAL_CONTEXT
    try:
        yield
    finally:
        pyproj._datadir._USE_GLOBAL_CONTEXT = context


@contextmanager
def proj_logging_env():
    """
    Ensure handler is added and then removed at end.
    """
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter("%(threadName)s:%(levelname)s:%(message)s")
    console_handler.setFormatter(formatter)
    logger = logging.getLogger("pyproj")
    logger.addHandler(console_handler)
    logger.setLevel(logging.DEBUG)
    try:
        yield
    finally:
        logger.removeHandler(console_handler)


def create_projdb(tmpdir):
    Path(tmpdir, "proj.db").write_text("DUMMY proj.db")


_INVALID_PATH = Path("/invalid/path/to/nowhere")


def test_get_data_dir__missing():
    with proj_env(), pytest.raises(DataDirError), patch.dict(
        os.environ, {}, clear=True
    ), patch("pyproj.datadir.Path.absolute", return_value=_INVALID_PATH), patch(
        "pyproj.datadir.shutil.which", return_value=None
    ), patch(
        "pyproj.datadir.Path.absolute", return_value=_INVALID_PATH
    ), patch(
        "pyproj.datadir.sys.prefix", str(_INVALID_PATH)
    ):
        assert get_data_dir() is None


def test_pyproj_global_context_initialize__datadir_missing():
    with proj_env(), pytest.raises(DataDirError), patch(
        "pyproj.datadir.get_data_dir", side_effect=DataDirError("test")
    ):
        _pyproj_global_context_initialize()


@pytest.mark.parametrize("projdir_type", [str, Path])
def test_get_data_dir__from_user(projdir_type, tmp_path):
    tmpdir = tmp_path / "proj"
    tmpdir.mkdir()
    tmpdir_env = tmp_path / "proj_env"
    tmpdir_env.mkdir()
    with proj_env(), patch.dict(
        os.environ, {"PROJ_DATA": str(tmpdir_env)}, clear=True
    ), patch("pyproj.datadir.Path.absolute", return_value=tmpdir / "datadir.py"), patch(
        "pyproj.datadir.sys.prefix", str(tmpdir_env)
    ):  # noqa: E501
        create_projdb(tmpdir)
        create_projdb(tmpdir_env)
        set_data_dir(projdir_type(tmpdir))
        internal_proj_dir = tmpdir / "proj_dir" / "share" / "proj"
        internal_proj_dir.mkdir(parents=True)
        create_projdb(internal_proj_dir)
        assert get_data_dir() == str(tmpdir)


def test_get_data_dir__internal(tmp_path):
    tmpdir = tmp_path / "proj"
    tmpdir.mkdir()
    tmpdir_fake = tmp_path / "proj_fake"
    tmpdir_fake.mkdir()
    with proj_env(), patch.dict(
        os.environ,
        {"PROJ_LIB": str(tmpdir_fake), "PROJ_DATA": str(tmpdir_fake)},
        clear=True,
    ), patch("pyproj.datadir.Path.absolute", return_value=tmpdir / "datadir.py"), patch(
        "pyproj.datadir.sys.prefix", str(tmpdir_fake)
    ):
        create_projdb(tmpdir)
        create_projdb(tmpdir_fake)
        internal_proj_dir = tmpdir / "proj_dir" / "share" / "proj"
        internal_proj_dir.mkdir(parents=True)
        create_projdb(internal_proj_dir)
        assert get_data_dir() == str(internal_proj_dir)


def test_get_data_dir__from_env_var__proj_lib(tmp_path):
    with proj_env(), patch.dict(
        os.environ, {"PROJ_LIB": str(tmp_path)}, clear=True
    ), patch("pyproj.datadir.Path.absolute", return_value=_INVALID_PATH), patch(
        "pyproj.datadir.sys.prefix", str(_INVALID_PATH)
    ):
        create_projdb(tmp_path)
        assert get_data_dir() == str(tmp_path)


def test_get_data_dir__from_env_var__proj_data(tmp_path):
    with proj_env(), patch.dict(
        os.environ, {"PROJ_DATA": str(tmp_path)}, clear=True
    ), patch("pyproj.datadir.Path.absolute", return_value=_INVALID_PATH), patch(
        "pyproj.datadir.sys.prefix", str(_INVALID_PATH)
    ):
        create_projdb(tmp_path)
        assert get_data_dir() == str(tmp_path)


def test_get_data_dir__from_env_var__multiple(tmp_path):
    tmpdir = os.pathsep.join([str(tmp_path) for _ in range(3)])
    with proj_env(), patch.dict(os.environ, {"PROJ_DATA": tmpdir}, clear=True), patch(
        "pyproj.datadir.Path.absolute", return_value=_INVALID_PATH
    ), patch("pyproj.datadir.sys.prefix", str(_INVALID_PATH)):
        create_projdb(tmp_path)
        assert get_data_dir() == tmpdir


def test_get_data_dir__from_prefix(tmp_path):
    with proj_env(), patch.dict(os.environ, {}, clear=True), patch(
        "pyproj.datadir.Path.absolute", return_value=_INVALID_PATH
    ), patch("pyproj.datadir.sys.prefix", str(tmp_path)):
        proj_dir = tmp_path / "share" / "proj"
        proj_dir.mkdir(parents=True)
        create_projdb(proj_dir)
        assert get_data_dir() == str(proj_dir)


def test_get_data_dir__from_prefix__conda_windows(tmp_path):
    with proj_env(), patch.dict(os.environ, {}, clear=True), patch(
        "pyproj.datadir.Path.absolute", return_value=_INVALID_PATH
    ), patch("pyproj.datadir.sys.prefix", str(tmp_path)):
        proj_dir = tmp_path / "Library" / "share" / "proj"
        proj_dir.mkdir(parents=True)
        create_projdb(proj_dir)
        assert get_data_dir() == str(proj_dir)


def test_get_data_dir__from_path(tmp_path):
    with proj_env(), patch.dict(os.environ, {}, clear=True), patch(
        "pyproj.datadir.Path.absolute", return_value=_INVALID_PATH
    ), patch("pyproj.datadir.sys.prefix", str(_INVALID_PATH)), patch(
        "pyproj.datadir.shutil.which", return_value=str(tmp_path / "bin" / "proj")
    ):
        proj_dir = tmp_path / "share" / "proj"
        proj_dir.mkdir(parents=True)
        create_projdb(proj_dir)
        assert get_data_dir() == str(proj_dir)


@pytest.mark.parametrize("projdir_type", [str, Path])
def test_append_data_dir__internal(projdir_type, tmp_path):
    with proj_env(), patch.dict(os.environ, {}, clear=True), patch(
        "pyproj.datadir.Path.absolute", return_value=tmp_path / "datadir.py"
    ), patch("pyproj.datadir.sys.prefix", str(_INVALID_PATH)):
        create_projdb(tmp_path)
        internal_proj_dir = tmp_path / "proj_dir" / "share" / "proj"
        internal_proj_dir.mkdir(parents=True)
        create_projdb(internal_proj_dir)
        extra_datadir = tmp_path / "extra_datumgrids"
        append_data_dir(projdir_type(extra_datadir))
        assert get_data_dir() == os.pathsep.join(
            [str(internal_proj_dir), str(extra_datadir)]
        )


@pytest.mark.slow
def test_creating_multiple_crs_without_file_limit():
    """
    This test checks for two things:
    1. Ensure database connection is closed for file limit
       https://github.com/pyproj4/pyproj/issues/374
    2. Ensure core-dumping does not occur when many objects are created
       https://github.com/pyproj4/pyproj/issues/678
    """
    codes = get_codes("EPSG", PJType.PROJECTED_CRS, False)
    assert [CRS.from_epsg(code) for code in codes]


def test_get_user_data_dir():
    assert get_user_data_dir().endswith("proj")


@patch.dict("os.environ", {"PYPROJ_GLOBAL_CONTEXT": "ON"}, clear=True)
def test_set_use_global_context__default_on():
    with proj_context_env():
        set_use_global_context()
        assert pyproj._datadir._USE_GLOBAL_CONTEXT is True


@patch.dict("os.environ", {"PYPROJ_GLOBAL_CONTEXT": "OFF"}, clear=True)
def test_set_use_global_context__default_off():
    with proj_context_env():
        set_use_global_context()
        assert pyproj._datadir._USE_GLOBAL_CONTEXT is False


@patch.dict("os.environ", {}, clear=True)
def test_set_use_global_context__default():
    with proj_context_env():
        set_use_global_context()
        assert pyproj._datadir._USE_GLOBAL_CONTEXT is False


@patch.dict("os.environ", {"PYPROJ_GLOBAL_CONTEXT": "OFF"}, clear=True)
def test_set_use_global_context__on():
    with proj_context_env():
        set_use_global_context(True)
        assert pyproj._datadir._USE_GLOBAL_CONTEXT is True


@patch.dict("os.environ", {"PYPROJ_GLOBAL_CONTEXT": "ON"}, clear=True)
def test_set_use_global_context__off():
    with proj_context_env():
        set_use_global_context(False)
        assert pyproj._datadir._USE_GLOBAL_CONTEXT is False


def test_proj_debug_logging(capsys):
    with proj_logging_env():
        with pytest.warns(FutureWarning):
            transformer = Transformer.from_proj("+init=epsg:4326", "+init=epsg:27700")
        transformer.transform(100000, 100000)
        captured = capsys.readouterr()
        if os.environ.get("PROJ_DEBUG") == "3":
            assert "PROJ_TRACE" in captured.err
            assert "PROJ_DEBUG" in captured.err
        elif os.environ.get("PROJ_DEBUG") == "2":
            assert "PROJ_TRACE" not in captured.err
            assert "PROJ_DEBUG" in captured.err
        else:
            assert "PROJ_ERROR" in captured.err


def test_proj_debug_logging__error(capsys):
    with proj_logging_env(), pytest.raises(CRSError):
        CRS("INVALID STRING")
        captured = capsys.readouterr()
        if os.environ.get("PROJ_DEBUG") == "3":
            assert "PROJ_TRACE" in captured.err
            assert "PROJ_DEBUG" in captured.err
            assert "PROJ_ERROR" in captured.err
        elif os.environ.get("PROJ_DEBUG") == "2":
            assert "PROJ_TRACE" not in captured.err
            assert "PROJ_DEBUG" in captured.err
            assert "PROJ_ERROR" in captured.err
        else:
            assert captured.err == ""
            assert captured.out == ""
