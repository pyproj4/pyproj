import contextlib
import os
import subprocess
import sys

import pytest


@contextlib.contextmanager
def tmp_chdir(new_dir):
    """
    This temporarily changes directories when running the tests.
    Useful for when testing wheels in the pyproj directory
    when pyproj has not been build and prevents conflicts.
    """
    curdir = os.getcwd()
    try:
        os.chdir(new_dir)
        yield
    finally:
        os.chdir(curdir)


def test_main(tmpdir):
    with tmp_chdir(str(tmpdir)):
        output = subprocess.check_output(
            [sys.executable, "-m", "pyproj"], stderr=subprocess.STDOUT
        ).decode("utf-8")
    assert "pyproj version:" in output
    assert "PROJ version:" in output
    assert "-v, --verbose  Show verbose debugging version information." in output


@pytest.mark.parametrize("option", ["-v", "--verbose"])
def test_main__verbose(option, tmpdir):
    with tmp_chdir(str(tmpdir)):
        output = subprocess.check_output(
            [sys.executable, "-m", "pyproj", option], stderr=subprocess.STDOUT
        ).decode("utf-8")
    assert "pyproj:" in output
    assert "PROJ:" in output
    assert "data dir" in output
    assert "System" in output
    assert "python" in output
    assert "Python deps" in output
    assert "-v, --verbose " not in output
