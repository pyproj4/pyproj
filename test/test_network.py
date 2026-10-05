import os
import subprocess
import sys
from unittest.mock import patch

import certifi
import pytest

from pyproj.network import set_ca_bundle_path


@patch.dict("os.environ", {}, clear=True)
@patch("pyproj.network._set_context_ca_bundle_path")
def test_ca_bundle_path__default(c_set_ca_bundle_path_mock):
    set_ca_bundle_path()
    c_set_ca_bundle_path_mock.assert_called_with(certifi.where())


@pytest.mark.parametrize(
    "env_var", ["PROJ_CURL_CA_BUNDLE", "CURL_CA_BUNDLE", "SSL_CERT_FILE"]
)
@patch("pyproj.network._set_context_ca_bundle_path")
def test_ca_bundle_path__always_certifi(c_set_ca_bundle_path_mock, env_var):
    with patch.dict("os.environ", {env_var: "/tmp/dummy/path/cacert.pem"}, clear=True):
        set_ca_bundle_path(True)
    c_set_ca_bundle_path_mock.assert_called_with(certifi.where())


@patch.dict("os.environ", {}, clear=True)
@patch("pyproj.network._set_context_ca_bundle_path")
def test_ca_bundle_path__skip(c_set_ca_bundle_path_mock):
    set_ca_bundle_path(False)
    c_set_ca_bundle_path_mock.assert_called_with("")


@pytest.mark.parametrize(
    "env_var", ["PROJ_CURL_CA_BUNDLE", "CURL_CA_BUNDLE", "SSL_CERT_FILE"]
)
@patch("pyproj.network._set_context_ca_bundle_path")
def test_ca_bundle_path__env_var_skip(c_set_ca_bundle_path_mock, env_var):
    with patch.dict("os.environ", {env_var: "/tmp/dummy/path/cacert.pem"}, clear=True):
        set_ca_bundle_path()
    c_set_ca_bundle_path_mock.assert_called_with("")


@pytest.mark.parametrize(
    "env_var", ["PROJ_CURL_CA_BUNDLE", "CURL_CA_BUNDLE", "SSL_CERT_FILE"]
)
@patch("pyproj.network._set_context_ca_bundle_path")
def test_ca_bundle_path__custom_path(c_set_ca_bundle_path_mock, env_var):
    with patch.dict("os.environ", {env_var: "/tmp/dummy/path/cacert.pem"}, clear=True):
        set_ca_bundle_path("/my/path/to/cacert.pem")
    c_set_ca_bundle_path_mock.assert_called_with("/my/path/to/cacert.pem")


@pytest.mark.network
def test_ca_bundle_path__new_thread(tmp_path):
    # A context made in a new thread is given the CA bundle path set earlier.
    # The memory of the path's string is overwritten first, so a path that was
    # not kept alive is garbage by the time the thread downloads a grid. Run in
    # a fresh process with an empty user directory so the grid is not cached.
    code = """
import threading

import certifi
import pyproj

pyproj.network.set_ca_bundle_path(certifi.where())
size = len(certifi.where().encode())
junk = [b"x" * size + bytes([n % 256]) for n in range(100_000)]


def convert(results):
    transformer = pyproj.Transformer.from_crs("EPSG:4267", "EPSG:4269", always_xy=True)
    results.append(transformer.transform(-79.4, 43.65))


results = []
thread = threading.Thread(target=convert, args=(results,))
thread.start()
thread.join()
assert all(abs(value) < 180 for value in results[0]), results[0]
"""
    subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        env={
            **os.environ,
            "PROJ_NETWORK": "ON",
            "PROJ_USER_WRITABLE_DIRECTORY": str(tmp_path),
        },
    )
