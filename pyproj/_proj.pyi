from typing import Any, NamedTuple

proj_version_str: str

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

class _Proj:
    srs: str
    def __init__(self, proj_string: str) -> None: ...
    @property
    def definition(self) -> str: ...
    @property
    def has_inverse(self) -> bool: ...
    def _fwd(self, lons: Any, lats: Any, errcheck: bool = False) -> None: ...
    def _inv(self, x: Any, y: Any, errcheck: bool = False) -> None: ...
    def _get_factors(
        self, longitude: Any, latitude: Any, radians: bool, errcheck: bool
    ) -> Factors: ...
    def __repr__(self) -> str: ...
    def _is_equivalent(self, other: "_Proj") -> bool: ...
    def is_exact_same(self, other: Any) -> bool: ...
