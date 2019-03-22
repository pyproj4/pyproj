import os
import shutil
import tempfile
import unittest
from contextlib import contextmanager

import pytest
from mock import patch

from pyproj.datadir import DataDirError, append_data_dir, get_data_dir, set_data_dir


def create_projdb(tmpdir):
    with open(os.path.join(tmpdir, "proj.db"), "w") as pjdb:
        pjdb.write("DUMMY proj.db")


@contextmanager
def proj_env():
    """
    Ensure environment variable the same at the end of the test.
    """
    proj_lib = os.environ.get("PROJ_LIB")
    try:
        yield
    finally:
        if proj_lib:
            os.environ["PROJ_LIB"] = proj_lib


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


@unittest.skipIf(os.name == "nt", reason="Cannot modify Windows environment variables.")
def test_get_data_dir__missing():
    with proj_env(), pytest.raises(DataDirError), patch(
        "pyproj.datadir.os.path.abspath", return_value="INVALID"
    ), patch("pyproj.datadir.find_executable", return_value=None):
        set_data_dir(None)
        os.environ.pop("PROJ_LIB", None)
        get_data_dir()


def test_get_data_dir__from_user():
    with proj_env(), temporary_directory() as tmpdir, temporary_directory() as tmpdir_env:
        create_projdb(tmpdir)
        os.environ["PROJ_LIB"] = tmpdir_env
        create_projdb(tmpdir_env)
        set_data_dir(tmpdir)
        internal_proj_dir = os.path.join(tmpdir, "proj_dir", "share", "proj")
        os.makedirs(internal_proj_dir)
        create_projdb(internal_proj_dir)
        with patch("pyproj.datadir.os.path.abspath") as abspath_mock:
            abspath_mock.return_value = os.path.join(tmpdir, "randomfilename.py")
            assert get_data_dir() == tmpdir


def test_get_data_dir__internal():
    with proj_env(), temporary_directory() as tmpdir:
        set_data_dir(None)
        os.environ["PROJ_LIB"] = tmpdir
        create_projdb(tmpdir)
        internal_proj_dir = os.path.join(tmpdir, "proj_dir", "share", "proj")
        os.makedirs(internal_proj_dir)
        create_projdb(internal_proj_dir)
        with patch("pyproj.datadir.os.path.abspath") as abspath_mock:
            abspath_mock.return_value = os.path.join(tmpdir, "randomfilename.py")
            assert get_data_dir() == internal_proj_dir


@unittest.skipIf(os.name == "nt", reason="Cannot modify Windows environment variables.")
def test_get_data_dir__from_env_var():
    with proj_env(), temporary_directory() as tmpdir, patch(
        "pyproj.datadir.os.path.abspath", return_value="INVALID"
    ):
        set_data_dir(None)
        os.environ["PROJ_LIB"] = tmpdir
        create_projdb(tmpdir)
        assert get_data_dir() == tmpdir


@unittest.skipIf(os.name == "nt", reason="Cannot modify Windows environment variables.")
def test_get_data_dir__from_env_var__multiple():
    with proj_env(), temporary_directory() as tmpdir, patch(
        "pyproj.datadir.os.path.abspath", return_value="INVALID"
    ):
        set_data_dir(None)
        os.environ["PROJ_LIB"] = ";".join([tmpdir, tmpdir, tmpdir])
        create_projdb(tmpdir)
        assert get_data_dir() == ";".join([tmpdir, tmpdir, tmpdir])


@unittest.skipIf(os.name == "nt", reason="Cannot modify Windows environment variables.")
def test_get_data_dir__from_path():
    with proj_env(), temporary_directory() as tmpdir, patch(
        "pyproj.datadir.os.path.abspath", return_value="INVALID"
    ), patch("pyproj.datadir.find_executable") as find_exe:
        set_data_dir(None)
        os.environ.pop("PROJ_LIB", None)
        find_exe.return_value = os.path.join(tmpdir, "bin", "proj")
        proj_dir = os.path.join(tmpdir, "share", "proj")
        os.makedirs(proj_dir)
        create_projdb(proj_dir)
        assert get_data_dir() == proj_dir


def test_append_data_dir__internal():
    with proj_env(), temporary_directory() as tmpdir:
        set_data_dir(None)
        os.environ["PROJ_LIB"] = tmpdir
        create_projdb(tmpdir)
        internal_proj_dir = os.path.join(tmpdir, "proj_dir", "share", "proj")
        os.makedirs(internal_proj_dir)
        create_projdb(internal_proj_dir)
        extra_datadir = str(os.path.join(tmpdir, "extra_datumgrids"))
        with patch("pyproj.datadir.os.path.abspath") as abspath_mock:
            abspath_mock.return_value = os.path.join(tmpdir, "randomfilename.py")
            append_data_dir(extra_datadir)
            assert get_data_dir() == ";".join([internal_proj_dir, extra_datadir])
