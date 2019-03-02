# -*- coding: utf-8 -*-
"""
Exceptions for pyproj
"""


class CRSError(RuntimeError):
    """Raised when a CRS error occurs."""


class ProjError(RuntimeError):
    """Raised when a Proj error occurs."""


class GeodError(RuntimeError):
    """Raised when a Geod error occurs."""


class DataDirError(RuntimeError):
    """Raised when a the data directory was not found."""
