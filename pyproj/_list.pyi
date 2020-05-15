from typing import Dict, List, NamedTuple, Optional, Union

from pyproj.enums import PJType

def get_proj_operations_map() -> Dict[str, str]: ...
def get_ellps_map() -> Dict[str, Dict[str, float]]: ...
def get_prime_meridians_map() -> Dict[str, str]: ...

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
) -> Dict[str, Unit]: ...
def get_authorities() -> List[str]: ...
def get_codes(
    auth_name: str, pj_type: Union[PJType, str], allow_deprecated: bool = False
) -> List[str]: ...
