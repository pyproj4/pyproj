from typing import Any, NamedTuple, Tuple, Type

geodesic_version_str: str

class GeodIntermediateReturn(NamedTuple):
    npts: int
    del_s: float
    dist: float
    lons: Any
    lats: Any
    azis: Any

class Geod:
    initstring: str
    a: float
    b: float
    f: float
    es: float
    sphere: bool
    def __init__(
        self, a: float, f: float, sphere: bool, b: float, es: float
    ) -> None: ...
    def __reduce__(self) -> Tuple[Type["Geod"], str]: ...
    def __repr__(self) -> str: ...
    def _fwd(
        self, lons: Any, lats: Any, az: Any, dist: Any, radians: bool = False
    ) -> None: ...
    def _inv(
        self, lons1: Any, lats1: Any, lons2: Any, lats2: Any, radians: bool = False
    ) -> None: ...
    def _inv_or_fwd_intermediate(
        self,
        lon1: float,
        lat1: float,
        lon2_or_azi1: float,
        lat2_or_nan: float,
        npts: int,
        del_s: float,
        radians: bool,
        initial_idx: int,
        terminus_idx: int,
        flags: int,
        out_lons: Any,
        out_lats: Any,
        out_azis: Any,
    ) -> GeodIntermediateReturn: ...
    def _line_length(self, lons: Any, lats: Any, radians: bool = False) -> float: ...
    def _polygon_area_perimeter(
        self, lons: Any, lats: Any, radians: bool = False
    ) -> Tuple[float, float]: ...
