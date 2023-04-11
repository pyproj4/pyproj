from typing import NamedTuple, Optional, Union

from pyproj.aoi import AreaOfInterest, AreaOfUse
from pyproj.enums import PJType

class Unit(NamedTuple):
    auth_name: str
    code: str
    name: str
    category: str
    conv_factor: float
    proj_short_name: Optional[str]
    deprecated: bool

def get_units_map(
    auth_name: Optional[str] = None,
    category: Optional[str] = None,
    allow_deprecated: bool = False,
) -> dict[str, Unit]: ...
def get_authorities() -> list[str]: ...
def get_codes(
    auth_name: str, pj_type: Union[PJType, str], allow_deprecated: bool = False
) -> list[str]: ...

class CRSInfo(NamedTuple):
    auth_name: str
    code: str
    name: str
    type: PJType
    deprecated: bool
    area_of_use: Optional[AreaOfUse]
    projection_method_name: Optional[str]

def query_crs_info(
    auth_name: Optional[str] = None,
    pj_types: Union[PJType, list[PJType], None] = None,
    area_of_interest: Optional[AreaOfInterest] = None,
    contains: bool = False,
    allow_deprecated: bool = False,
) -> list[CRSInfo]: ...
def query_utm_crs_info(
    datum_name: Optional[str] = None,
    area_of_interest: Optional[AreaOfInterest] = None,
    contains: bool = False,
) -> list[CRSInfo]: ...
def get_database_metadata(key: str) -> Optional[str]: ...
