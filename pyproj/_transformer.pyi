from array import array
from typing import Any, List, NamedTuple, Optional, Tuple, Union

from pyproj._crs import _CRS, AreaOfUse, Base, CoordinateOperation
from pyproj.enums import ProjVersion, TransformDirection

proj_version_str: str

class AreaOfInterest(NamedTuple):
    west_lon_degree: float
    south_lat_degree: float
    east_lon_degree: float
    north_lat_degree: float

class Factors(NamedTuple):
    meridional_scale: float
    parallel_scale: float
    areal_scale: float
    angular_distortion: float
    meridian_parallel_angle: float
    meridian_convergence: float
    tissot_semimajor: float
    tissot_semiminor: float
    dx_dlam: float
    dx_dphi: float
    dy_dlam: float
    dy_dphi: float

class _TransformerGroup:
    _transformers: Any
    _unavailable_operations: List[CoordinateOperation]
    _best_available: bool
    def __init__(
        self,
        crs_from: str,
        crs_to: str,
        always_xy: bool = False,
        area_of_interest: Optional[AreaOfInterest] = None,
    ) -> None: ...

class _Transformer(Base):
    input_geographic: bool
    output_geographic: bool
    is_pipeline: bool
    type_name: str
    @property
    def id(self) -> str: ...
    @property
    def description(self) -> str: ...
    @property
    def definition(self) -> str: ...
    @property
    def has_inverse(self) -> bool: ...
    @property
    def accuracy(self) -> float: ...
    @property
    def area_of_use(self) -> AreaOfUse: ...
    @property
    def operations(self) -> Union[Tuple[CoordinateOperation], None]: ...
    @property
    def is_network_enabled(self) -> bool: ...
    def to_proj4(
        self,
        version: Union[ProjVersion, str] = ProjVersion.PROJ_5,
        pretty: bool = False,
    ) -> str: ...
    @staticmethod
    def from_crs(
        crs_from: str,
        crs_to: str,
        always_xy: bool = False,
        area_of_interest: Optional[AreaOfInterest] = None,
        authority: Optional[str] = None,
        accuracy: Optional[float] = None,
        allow_ballpark: Optional[bool] = None,
    ) -> "_Transformer": ...
    @staticmethod
    def from_pipeline(proj_pipeline: str) -> "_Transformer": ...
    def _transform(
        self,
        inx: Any,
        iny: Any,
        inz: Any,
        intime: Any,
        direction: Union[TransformDirection, str],
        radians: bool,
        errcheck: bool,
    ) -> None: ...
    def _transform_sequence(
        self,
        stride: int,
        inseq: array[float],
        switch: bool,
        direction: Union[TransformDirection, str],
        time_3rd: bool,
        radians: bool,
        errcheck: bool,
    ) -> None: ...
    def _transform_bounds(
        self,
        left: float,
        bottom: float,
        right: float,
        top: float,
        densify_pts: int = 21,
        radians: bool = False,
        errcheck: bool = False,
        direction: Union[TransformDirection, str] = TransformDirection.FORWARD,
    ) -> Tuple[float, float, float, float]: ...
    def _get_factors(
        self, longitude: Any, latitude: Any, radians: bool, errcheck: bool
    ) -> Factors: ...
