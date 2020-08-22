"""
Module for managing the PROJ network settings.
"""
import os
from pathlib import Path
from typing import Union

import certifi

from pyproj._network import (  # noqa: F401
    _set_ca_bundle_path,
    is_network_enabled,
    set_network_enabled,
)


def set_ca_bundle_path(ca_bundle_path: Union[Path, str, bool, None] = None) -> None:
    """
    .. versionadded:: 3.0.0

    Sets the path to the CA Bundle used by the `curl`
    built into PROJ when PROJ network is enabled..

    Environment variables that can be used with PROJ 7.2+:

    - PROJ_CURL_CA_BUNDLE
    - CURL_CA_BUNDLE
    - SSL_CERT_FILE

    Parameters
    ----------
    ca_bundle_path: Union[Path, str, bool, None], optional
        Default is None, which only uses the `certifi` package path as a fallback if
        the environment variables are not set. If a path is passed in, then
        that will be the path used. If it is set to True, then it will default
        to using the path provied by the `certifi` package. If it is set to False,
        then it will not set the path.
    """
    if ca_bundle_path is False:
        return

    env_var_names = (
        "PROJ_CURL_CA_BUNDLE",
        "CURL_CA_BUNDLE",
        "SSL_CERT_FILE",
    )
    if isinstance(ca_bundle_path, (str, Path)):
        ca_bundle_path = str(ca_bundle_path)
    elif (ca_bundle_path is True) or not any(
        env_var_name in os.environ for env_var_name in env_var_names
    ):
        ca_bundle_path = certifi.where()

    if isinstance(ca_bundle_path, str):
        _set_ca_bundle_path(ca_bundle_path)
