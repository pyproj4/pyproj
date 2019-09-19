import subprocess
import sys

import pytest


def test_main():
    output = subprocess.check_output(
        [sys.executable, "-m", "pyproj"], stderr=subprocess.STDOUT
    ).decode("utf-8")
    assert "pyproj version:" in output
    assert "PROJ version:" in output
    assert "-v, --verbose  Show verbose debugging version information." in output


@pytest.mark.parametrize("option", ["-v", "--verbose"])
def test_main__verbose(option):
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
