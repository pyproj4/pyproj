import pytest

from pyproj import CRS, Proj
from pyproj.exceptions import CRSError, ProjError


def test_proj_exception():
    with pytest.raises(ProjError, match="Internal Proj Error"):
        Proj("+proj=bobbyjoe")


def test_crs_exception():
    with pytest.raises(CRSError, match="Internal Proj Error"):
        CRS("+proj=bobbyjoe")
