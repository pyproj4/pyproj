Change Log
==========

3.5.0
------
- DEP: Minimum PROJ version 9.0 (issue #1223)
- WHL: PROJ 9.2 in wheels (pull #1243)
- ENH: Add `return_back_azimuth: bool` to allow compatibility between the azimuth output of the following functions (issue #1163):
    `fwd` and `fwd_intermediate`, `inv` and `inv_intermediate`,
    Note: BREAKING CHANGE for the default value `return_back_azimuth=True` in the functions `fwd_intermediate` and `inv_intermediate`
    to mach the default value in `fwd` and `inv`
- ENH: Added only_best kwarg to :meth:`.Transformer.from_crs` (issue #1228)
- PERF: Optimize point transformations (pull #1204)
- REF: Raise error when :meth:`.CRS.to_wkt`, :meth:`.CRS.to_json`, or :meth:`.CRS.to_proj4` returns None (issue #1036)
- CLN: Remove `AzumuthalEquidistantConversion` & :class:`LambertAzumuthalEqualAreaConversion`. :class:`AzimuthalEquidistantConversion` & :class:`LambertAzimuthalEqualAreaConversion` should be used instead (pull #1219)
- BUG: Fix Derived Projected CRS support (issue #1182)
- BUG: Add horizontal_datum_name for geographic CRS in :meth:`.CRS.to_cf` (issue #1251)
- BUG: Add datum ensemble support to :class:`.GeographicCRS` (pull #1255)

3.4.1
-----
- WHL: Add win32 to build_wheels matrix (pull #1169)
- BUG: Changed so that the setup.cfg depends on the version code in the __init__.py instead of the other way around (issuue #1155)
- BUG: Fix :meth:`.CRS.to_cf` for Pole rotation GRIB convention (pull #1167)
- BUG: Fix :meth:`.CRS.to_authority` memory leak (pull #1178)
- REF: Use upper case EPSG code when creating CRS (pull #1162)

3.4.0
-----
- WHL: Python 3.11 Wheels (issue #1110)
- WHL: Wheels contain PROJ 9.1.0 (pull #1132)
- DEP: Minimum PROJ version 8.2 (issue #1011)
- BUG: Fix transformer list for 3D transformations in :class:`.TransformerGroup` (discussion #1072)
- ENH: Added authority, accuracy, and allow_ballpark kwargs to :class:`.TransformerGroup` (pull #1076)
- ENH: Added ``force_over`` kwarg to :meth:`.Transformer.from_crs` (issue #997)
- ENH: Added :meth:`.Transformer.get_last_used_operation` (issue #1071)
- CLN: Remove deprecated ``skip_equivalent`` kwarg from transformers and ``errcheck`` kwarg from :meth:`.CRS.from_cf` (pull #1077)
- REF: use regex to process PROJ strings in :meth:`.CRS.to_dict` (pull #1086)
- BUG: :class:`.MercatorAConversion` defined only for lat_0 = 0 (issue #1089)
- BUG: Add support for `PROJ_DATA` environment variable (issue #1097)
- BUG: Ensure numpy masked arrays stay masked after projection (issue #1102)
- BLD: Don't specify runtime_library_dirs on Cygwin (pull #1120)
- BUG: Fix finding PROJ version with PROJ_LIB and PROJ 9.1+ (issue #1127)

3.3.1
-------
- WHL: Wheels for Linux are manylinux2014 (pip 19.3+)
- BUG: Complete database stub file with query_utm_crs_info() signature (issue #1044)
- BUG: Reorder deps in show_versions for setuptools issue (issue #1017)
- BUG: remove CustomConstructorCRS @abstractmethod decorator (pull #1018)
- BUG: Correct type annotation for AreaofUse.bounds (issue #1012)
- BUG: :func:`pyproj.datadir.get_data_dir` support for conda Windows (issue #1029)
- ENH: warn when :meth:`pyproj.crs.CRS.to_wkt`, :meth:`pyproj.crs.CRS.to_proj4`, or :meth:`pyproj.crs.CRS.to_json()` returns None (issue #1036)
- ENH: Added support for int-like strings and numpy dtypes (issues #1026 and #1835)
- ENH: Added support to pickle :class:`pyproj.transformer.Transformer` (issues #1058)

3.3.0
-------
- WHL: Wheels contain PROJ 8.2.0
- DEP: Minimum supported Python version 3.8 (issue #930)
- DEP: Minimum PROJ version 8.0 (issue #940)
- BUG: Prepend "Derived" to CRS type name if CRS is derived (issue #932)
- BUG: Improved handling of inf values in :meth:`pyproj.transformer.Transformer.transform_bounds` (pull #961)
- BUG: CRS CF conversions mismatch of PROJ parameters in rotated pole (issue #948)
- ENH: Add support for transforming bounds at the poles in :meth:`pyproj.transformer.Transformer.transform_bounds` (pull #962)
- ENH: Added :attr:`pyproj.transformer.Transformer.source_crs` & :attr:`pyproj.transformer.Transformer.target_crs` (pull #976)
- ENH: Added :class:`pyproj.crs.coordinate_operation.PoleRotationNetCDFCFConversion` (issue #948)
- ENH: Added :func:`pyproj.database.get_database_metadata` (issue #990)
- ENH: Added PROJ database metadata to :func:`pyproj.show_versions` (issue #990)

3.2.1
------
- REF: declare specific python types in cython (pull #928)
- REF: Use cython string decoding (pull #929)
- BUG: Return multiple authorities with :attr:`pyproj.crs.CRS.list_authority` (pull #943)
- BUG: CRS CF conversions ensure lon_0 = north_pole_grid_longitude + 180 (issue #927)
- BUG: CRS CF conversions ensure Pole rotation (netCDF CF convention) conversion works (issue #927)

3.2.0
------
- WHL: Wheels contain PROJ 8.1.1
- DOC: Add new pyproj logo (issue #700)
- REF: Handle deprecation of proj_context_set_autoclose_database (issue #866)
- REF: Make CRS methods inheritable (issue #847)
- ENH: Added :attr:`pyproj.crs.CRS.is_derived` (pull #902)
- ENH: Added :attr:`pyproj.crs.GeocentricCRS` (pull #903)
- ENH: Added :attr:`pyproj.crs.CRS.list_authority` (issue #918)
- ENH: Added `inplace` kwarg to :meth:`pyproj.transformer.Transformer.transform` (issue #906)
- PERF: Disable unnecessary copy in dtype conversion for buffer (pull #904)
- DOC: Improve FAQ text about CRS formats (issue #789)
- BUG: Add PyPy cython array implementation (issue #854)
- BUG: Fix spelling for
  :class:`pyproj.crs.coordinate_operation.AzimuthalEquidistantConversion`
  and :class:`pyproj.crs.coordinate_operation.LambertAzimuthalEqualAreaConversion` (issue #882)
- BUG: Make datum name match exact in :func:`pyproj.database.query_utm_crs_info` (pull #887)
- BUG: Update :class:`pyproj.enums.GeodIntermediateFlag` for future Python compatibility (issue #855)
- BUG: Hide unnecessary PROJ ERROR from proj_crs_get_coordoperation (issue #873)
- BUG: Fix pickling for CRS builder classes (issue #897)
- CLN: Remove `ignore_axis_order` kwarg from :meth:`pyproj.crs.CRS.is_exact_same` as it was added by accident (pull #904)
- CLN: remove numeric/numarrays support (pull #908)
- LNT: Add pylint & address issues (pull #909)
- DEP: Remove distutils dependency (pull #917)

3.1.0
-----
* WHL: Wheels contain PROJ 8.0.1
* DEP: Minimum supported Python version 3.7 (issue #790)
* REF: Multithread safe CRS, Proj, & Transformer (issue #782)
* BUG: Disallow NaN values with AreaOfInterest & BBox (issue #788)
* ENH: Pretty format PROJ string support (issue #764)
* ENH: Added :meth:`pyproj.transformer.Transformer.to_proj4` (pull #798)
* ENH: Added authority, accuracy, and allow_ballpark kwargs to :meth:`pyproj.transformer.Transformer.from_crs` (issue #754)
* ENH: Added support for "AUTH:CODE" input to :meth:`pyproj.transformer.Transformer.from_pipeline` (issue #755)
* ENH: Added :meth:`pyproj.crs.CRS.to_3d` (pull #808)
* ENH: Added :meth:`pyproj.transformer.Transformer.transform_bounds` (issue #809)
* ENH: Added :attr:`pyproj.crs.CRS.is_compound` (pull #823)
* ENH: Added `initial_idx` and `terminal_index` kwargs to :meth:`pyproj.Geod.npts` (pull #841)
* ENH: Added :meth:`pyproj.Geod.inv_intermediate` & :meth:`pyproj.Geod.fwd_intermediate` (pull #841)
* REF: Skip transformations if `noop` & deprecate `skip_equivalent` (pull #824)

3.0.1
-----
* WHL: Wheels contain PROJ 7.2.1
* Use `proj_context_errno_string` in PROJ 8+ due to deprecation (issue #760)
* BUG: Allow transformations with empty arrays (issue #766)
* BUG: support numpy objects in CRS.from_cf (issue #773)

3.0.0
-----
* Minimum supported Python version 3.6 (issue #499)
* Minimum PROJ version 7.2 (issues #599 & #689)
* WHL: Removed datumgrids from wheels because not needed with RFC 4 (pull #628)
* WHL: Wheels contain PROJ 7.2
* ENH: Added :ref:`network_api` (#675, #691, #695)
* ENH: Added ability to use global context (issue #661)
* ENH: Added transformation grid sync API/CLI (issue #572)
* ENH: Support obects with '__array__' method (pandas.Series, xarray.DataArray, dask.array.Array) (issue #573)
* ENH: Added :func:`pyproj.datadir.get_user_data_dir` (pull #636)
* ENH: Added :attr:`pyproj.transformer.Transformer.is_network_enabled` (issue #629)
* ENH: Added :meth:`pyproj.transformer.TransformerGroup.download_grids` (pull #643)
* ENH: Use 'proj_get_units_from_database' in :func:`pyproj.database.get_units_map` & cleanup :func:`pyproj.database.get_codes` (issue #619)
* ENH: Added support for radians for Proj & Transformer.from_pipeline & use less gil (issue #612)
* ENH: Datum.from_name default to check all datum types (issue #606)
* ENH: Use from_user_input in __eq__ when comparing CRS sub-classes (i.e. PrimeMeridian, Datum, Ellipsoid, etc.) (issue #606)
* ENH: Add support for coordinate systems with CRS using CF conventions (issue #536)
* ENH: Use `proj_is_equivalent_to_with_ctx` in the place of `proj_is_equivalent_to` internally (issue #666)
* BUG: Add support for identifying engineering/parametric/temporal datums (issue #670)
* ENH: Add support for temporal CRS CF coordinate system (issue #672)
* ENH: Added support for debugging internal PROJ (pull #696)
* ENH: Added pathlib support for data directory methods (pull #702)
* ENH: Added :func:`pyproj.database.query_crs_info` (pull #703)
* ENH: Added :func:`pyproj.database.query_utm_crs_info` (pull #712)
* REF: Refactor Proj to inherit from Transformer (issue #624)
* REF: Added `pyproj.database`, `pyproj.aoi`, and `pyproj.list` modules (pull #703)
* BUG: Fix handling of polygon holes when calculating area in Geod (pull #686)

2.6.1
~~~~~
* WHL: Wheels contain PROJ version is 7.0.1
* BUG: Allow `*_name` to be added in CRS.to_cf (issue #585)
* BUG: Fix building prime meridian in :meth:`pyproj.crs.CRS.from_cf` (pull #588)
* BUG: Fix check for numpy bool True kwarg (pull #590)
* DOC: Update pyproj.Proj docstrings for clarity (issue #584)
* Added `pyproj.__proj_version__`
* BUG: Fix :meth:`pyproj.Proj.get_factors` (issue #600)
* BUG: fix unequal (!=) with non-CRS type (pull #596)

2.6.0
~~~~~
* ENH: Added :meth:`pyproj.Proj.get_factors` (issue #503)
* ENH: Added type hints (issue #369)
* BUG: Don't use CRS classes for defaults in CRS child class init signatures (issue #554)
* ENH: Updated :attr:`pyproj.crs.CRS.axis_info` to pull all relevant axis information from CRS (issue #557)
* ENH: Added :meth:`pyproj.transformer.Transform.__eq__` (issue #559)
* ENH: Added :attr:`pyproj.crs.CRS.utm_zone` (issue #561)
* BUG: Modify CRS dict test to accommodate numpy bool types. (issue #564)
* BUG: Fix pipeline transformations to match cct (issue #565)
* BUG: Don't silently ignore kwargs when projparams are specified (Proj & CRS) (issue #565)

2.5.0
~~~~~
* WHL: Wheels contain PROJ version is 6.3.1
* Remove deprecated PyObject_AsWriteBuffer (issue #495)
* ENH: Added :meth:`pyproj.crs.CRS.equals` with `ignore_axis_order` kwarg (issue #493)
* ENH: Added :meth:`pyproj.crs.CoordinateSystem.from_json`, :meth:`pyproj.crs.CoordinateSystem.from_json_dict`, and :meth:`pyproj.crs.CoordinateSystem.from_string` (pull #501)
* ENH: Added :class:`pyproj.crs.CoordinateSystem` to `pyproj.crs` namespace (pull #501)
* ENH: Added :meth:`pyproj.crs.CoordinateSystem.from_user_input`, :meth:`pyproj.crs.CoordinateOperation.from_user_input`, :meth:`pyproj.crs.Datum.from_user_input`, :meth:`pyproj.crs.PrimeMeridian.from_user_input`, :meth:`pyproj.crs.Ellipsoid.from_user_input` (pull #502)
* ENH: Added :meth:`pyproj.crs.CoordinateSystem.from_name`, :meth:`pyproj.crs.CoordinateOperation.from_name`, :meth:`pyproj.crs.Datum.from_name`, :meth:`pyproj.crs.PrimeMeridian.from_name`, :meth:`pyproj.crs.Ellipsoid.from_name` (pull #505)
* BUG: Fix getting :attr:`pyproj.crs.Ellipsoid.semi_minor_metre` when not computed (issue #457)
* ENH: Added support for custom CRS (issue #389)
* ENH: Added enumeration for WKT2_2019 (issue #526)
* ENH: Update from_cf/to_cf to use WKT instead of PROJ strings for internal management (issue #515)

2.4.2
~~~~~
* Elevate +init= warning to FutureWarning (pull #486)
* Add UserWarning to :meth:`pyproj.crs.CRS.to_proj4` (pull #486)
* BUG: Fix for 32-bit i686 platforms (issue #481)
* Return 'inf' in Proj instead of 1.e30 (pull #491)

2.4.1
~~~~~
* WHL: Wheels contain PROJ version is 6.2.1 (issue #456)
* WHL: Wheels for Linux x86_64 use manylinux2010 (pyproj4/pyproj-wheels/pull/18)
* BUG: Fix setting lat_ts for mercator projection in :meth:`pyproj.crs.CRS.from_cf` and :meth:`pyproj.crs.CRS.to_cf` (issue #461)
* BUG: latlon -> longlat in `CRS.from_cf()` for o_proj so behavior consistent in PROJ 6.2.0 and 6.2.1 (pull #472)
* ENH: Add repr for `pyproj.crs.CoordinateOperation` and for `pyproj.transformer.TransformerGroup` (pull #464)

2.4.0
~~~~~
* Minimum PROJ version is 6.2.0 (issue #411)
* Removed global pyproj context (issue #418)
* Added support for PROJ JSON in `pyproj.crs` objects and `pyproj.Transformer` (pull #432)
* Moved doctests code out of `pyproj.__init__` (issue #417)
* Added version information to `python -m pyproj` (pull #429)
* Added `scope` & `remarks` to `pyproj.crs` objects and `pyproj.Transformer` (issue #441)
* Added `operations` to `pyproj.crs.CoordinateOperation` objects and `pyproj.Transformer` (issue #441)
* Added :func:`pyproj.get_authorities` and :func:`pyproj.get_codes` (issue #440)
* Release gil in core cython/PROJ code (issue #386)
* BUG: Added checks for uninitialized `pyproj.crs` objects to prevent core dumping (issue #433)
* BUG: Added fix for get_transform_crs when checking type (pull #439)
* DOC: Build docs with python3 (pull #428)

2.3.1
~~~~~
* Added cleanup for internal PROJ errors (issue #413)
* Delay checking for pyproj data directory until importing pyproj (issue #415)
* Address issue where PROJ core dumps on proj_create with +init= when global context does not have data directory set (issue #415 & issue #368)

2.3.0
~~~~~
* Minimum supported Python version 3.5 (issue #331)
* New `pyproj.geod.Geod` additions:
    * Added support for calculating geodesic area (:meth:`pyproj.Geod.polygon_area_perimeter`)
      and added interface to calculate total length of a line
      (:meth:`pyproj.Geod.line_length` & :meth:`pyproj.Geod.line_lengths`) (issue #210).
    * Added support for calculating geodesic area and line lengths with shapely geometries
      (:meth:`pyproj.Geod.geometry_area_perimeter` & :meth:`pyproj.Geod.geometry_length`)
      (pull #366)
* New `pyproj.transformer` additions:
    * Added :class:`pyproj.transformer.TransformerGroup` to make all transformations available (issue #381)
    * Added option for `area_of_interest` for :meth:`pyproj.transformer.Transformer.from_crs`,
      :meth:`pyproj.transformer.Transformer.from_proj` and :class:`pyproj.transformer.TransformerGroup`
    * Added :attr:`pyproj.transformer.Transformer.area_of_use` (issue #385)
* Added :attr:`pyproj.crs.CoordinateOperation.area_of_use` (issue #385)
* Updated to only have one PJ_CONTEXT per pyproj session (issue #374)
* Always return latlon with Proj (issue #356)
* Remove aenum dependency (issue #339)
* Removed deprecated functions `Proj.proj_version`, `CRS.is_valid`, and `CRS.to_geodetic()` (pull #371)
* Search on `sys.prefix` for the PROJ data directory (issue #387)

2.2.2
~~~~~
* Update wheels to PROJ 6.1.1
* Add deprecation warning when using +init= syntax (pull #358)
* Added :meth:`pyproj.crs.is_proj` (pull #359)
* Fixed case in :meth:`pyproj.crs.CRS.to_dict` with :meth:`pyproj.crs.CRS.to_proj4` returning None (pull #359)
* Keep `no_defs` in input PROJ string as it does not hurt/help anything in current code (pull #359)
* Made public properties on C classes readonly (pull #359)
* Update data dir exception handling to prevent ignoring errors (pull #361)
* :meth:`pyproj.crs.CRS.to_cf` export transverse mercator parameters for UTM zones (pull #362)

2.2.1
~~~~~
* Added :meth:`pyproj.show_versions` (issue #334)
* Added fix for whitepace around '=' in PROJ strings (issue #345)
* Update version check in `setup.py` (issue #323)
* Add "stable" doc site pointing to latest release (issue #347, pull #348)
* Deprecate `Proj.proj_version` (pull #337)
* Test fixes (pull #333, pull #335)

2.2.0
~~~~~
* Minimum PROJ version is now 6.1.0
* `pyproj.crs` updates:
    * Updated CRS repr (issue #264)
    * Add Datum, CoordinateSystem, CoordinateOperation classes, (issue #262)
    * Added :meth:`pyproj.crs.CRS.to_cf` and :meth:`pyproj.crs.CRS.from_cf` for
      converting to/from Climate and Forecast (CF) 1.8 grid mappings (pull #244)
    * Added :meth:`pyproj.crs.CRS.to_dict` (issue #226)
    * Added :meth:`pyproj.crs.CRS.to_authority` (pull #294)
    * Added :attr:`pyproj.crs.CRS.is_vertical` and :attr:`pyproj.crs.CRS.is_engineering` (issue #316)
    * Added :attr:`pyproj.crs.CRS.target_crs` (pull #328)
    * Provide option to "pretty print" WKT in :attr:`pyproj.crs.CRS.to_wkt` (issue #258)
    * Add support for Bound and Compound CRS for :attr:`pyproj.crs.CRS.is_geographic`, :attr:`pyproj.crs.CRS.is_projected` (issue #274)
    * Add support for Bound CRS for :attr:`pyproj.crs.CRS.is_geocentric` (issue #374)
    * Add support for comparison with CRS a non-crs type supported by :meth:`pyproj.crs.CRS.from_user_input` (issue #312)
    * Added support for ITRF, compound EPSG, and urn projection strings in CRS (pull #289)
    * Better handle Compound CRS (issue #265)
    * Disallow creation of non-CRS object (eg pipeline) in CRS class (issue #267)
    * Added check in :meth:`pyproj.crs.CRS.to_epsg` for when `proj_list` is null (issue #257)
    * Fix comparing classes of non-instance types (issue #310)
* `pyroj.transformer` updates:
    * Added `always_xy` option to Transformer so the transform method will
      always accept as input and return as output coordinates using the
      traditional GIS order, that is longitude, latitudecfor geographic
      CRS and easting, northing for most projected CRS (issue #225)
    * Provide `direction` option in :meth:`pyproj.transformer.Transformer.transform` (issue #266)
    * Add check for valid initialization of Transformer and ensure it is a transformer (issue #321)
    * Added :meth:`pyproj.transformer.Transformer.to_wkt` as well as attributes related to `PJ_PROJ_INFO` (pull #322)
    * Undo deprecation of :meth:`pyproj.transformer.Transformer.from_crs` (issue #275)
    * Fix false positive errors raised in transformer (issue #249)
* Fix :class:`pyproj.Proj` initialization from DerivedGeographicCRS (issue #270)
* Add interface to get the projection/ellps/prime_meridian/units lists (issue #251)
* Docs/Build/Test fixes (pull #278, pull #245, pull #248, pull #247, issue #253, pull #252)

2.1.3
~~~~~
* Added support for time transformations (issue #208)
* Fixed projection equivalence testing for transformations (pull #231).
* Switch to pytest for testing (pull #230)
* Various testing fixes (pull #223, #222, #221, #220)
* Convert PROJ error messages from bytes to strings (pull #219)
* Fix data dir path separator to be (;) for windows and (:) for linux (pull #234)

2.1.2
~~~~~
* Updated to use the CRS definition for Proj instances in transforms (issue #207)
* Add option to skip transformation operation if input and output projections are equivalent
  and always skip if the input and output projections are exact (issue #128)
* Update setup.py method for checking PROJ version (pull #211)
* Add internal proj error log messages to exceptions (pull #215)

2.1.1
~~~~~
* Restore behavior of 1.9.6 when illegal projection transformation requested
  (return ``inf`` instead of raising an exception, issue #202).  kwarg ``errcheck``
  added to :func:`pyproj.transformer.transform` and :func:`pyproj.transformer.itransform`
  (default ``False``). When ``errcheck=True`` an exception is raised.

2.1.0
~~~~~
* Added :class:`pyproj.transformer.Transformer` to make repetitive transformations more efficient (issue #187)
* Added fix for using local datumgrids with transform (issue #191)
* Added :meth:`pyproj.transformer.Transformer.from_pipeline` to support pipeline transformations.
* Added fix for conversion between radians/degrees for transformations (issues #192 & #195)

2.0.2
~~~~~
* add filter for boolean values in dict2string so "no_rot=True" works (issue #183).
* make sure .pxd files included in source tarball.
* add radians flag back in for transform/itransform (issue #185).

2.0.1
~~~~~
* Ensure data path set properly for TransProj (pull request #179, addressed
  issue #176).

2.0.0
~~~~~
* Update to PROJ version 6.0.0 & removed support for older PROJ versions.
* Added pyproj.CRS class.
* Updated pyproj.Proj & pyproj.transform to accept any input from CRS.from_user_input.
* Removed internal PROJ source code.
* Changed default for preserve_units to be True in pyproj.Proj class initialization.
* Modified logic for searching for the PROJ data directory to not conflict with older versions of PROJ.
* Added pyproject.toml.

1.9.6
~~~~~
* fix segfault when inverse projection not defined (issue #43, pull request
  #44).
* supports python 3.7

1.9.5.1
~~~~~~~
* fix for issue #42 (compilation error with microsoft visual studio).

1.9.5
~~~~~
* update proj4 source to latest github master (commit 953cc00fd87425395cabe37641cda905c4b587c1).
* port of basemap fix for input arrays in fortran order
* restore inverse Hammer patch that was lost when proj4 source code was updated.

1.9.4 (git tag v1.9.4rel)
~~~~~~~~~~~~~~~~~~~~~~~~~
 * migrate to github from googlecode.
 * update proj4 source code from svn r2595 (version 4.9.0RC2).
 * include runtime_library_dirs in setup-proj.py.
 * added to_latlong method (issue 51).
 * fix back azimuth when lon1 and lon2 are identical.

1.9.3 (svn revision 327)
~~~~~~~~~~~~~~~~~~~~~~~~
 * Geod now uses C code adapted from geographiclib now included in proj4 source,
   instead of pure python code directly from geographiclib.
 * make radians=True work with Geod.npts (issue 47).
 * allow PROJ_DIR env var to control location of proj data (issue 40).

1.9.2 (svn revision 301)
~~~~~~~~~~~~~~~~~~~~~~~~
 * updated proj4 src to 4.8.0 - includes two new map projections (natearth and
   isea).

1.9.1 (svn revision 285)
~~~~~~~~~~~~~~~~~~~~~~~~
 * restore compatibility with python 2.4/2.5, which was broken by the addition
   of the geographiclib geodesic module (issue 36).

1.9.0 (svn revision 282)
~~~~~~~~~~~~~~~~~~~~~~~~
 * use pure python geographiclib for geodesic computation codes instead of proj4.
 * don't use global variable pj_errno for return codes, use pj_ctx_get_errno instead.
 * use new projCtx structure for thread safety in proj lib.
 * update C source and data from proj4 svn (r2140).
 * add pj_list and pj_ellps module level variables (a dict mapping short names to longer descriptions, e.g. pyproj.pj_list['aea'] = 'Albers Equal Area').

1.8.9 (svn revision 222)
~~~~~~~~~~~~~~~~~~~~~~~~
 * Python 3 now supported.
 * allow 'EPSG' init (as well as 'epsg'). This only worked on case-insensitive
   filesystems previously. Fixes issue 6.
 * added inverse to Hammer projection.
 * updated proj.4/src/pj_mutex.c from proj4 svn to fix a threading issue on windows
   (issue 25). Windows binary installers updated (version 1.8.8-1), courtesy
   Christoph Gohlke.
 * if inputs are NaNs, return huge number (1.e30).

1.8.8 (svn revision 196)
~~~~~~~~~~~~~~~~~~~~~~~~
 * add extra datum shift files, added test/test_datum.py (fixes issue 22).
   datum shifts now work correctly in transform function.

1.8.7 (svn revision 175)
~~~~~~~~~~~~~~~~~~~~~~~~
 * reverted pj_init.c to old version (from proj4 4.6.1) because version in
   4.7.0 includes caching code that can cause segfaults in pyproj (issue 19).
 * added 'preserve_units' keyword to Proj.__init__ to suppress conversion
   to meters.

1.8.6 (svn revision 169)
~~~~~~~~~~~~~~~~~~~~~~~~
 * now works with ms vs2008, vs2003 (fixed missing isnan).
 * updated to proj 4.7.0 (fixes a problem coexisting with pyqt).
 * allow Geod instance to be initialized using a proj4 string

1.8.5 (svn revision 155)
~~~~~~~~~~~~~~~~~~~~~~~~
 * allow Proj instance to be initialized using a proj4 string
   (instead of just a dict or kwargs).

1.8.4 (svn revision 151)
~~~~~~~~~~~~~~~~~~~~~~~~
 * updated proj4 sources to version 4.6.0

1.8.3 (svn revision 146)
~~~~~~~~~~~~~~~~~~~~~~~~
 * fixed bug in Geod class that caused erroneous error message
   "undefined inverse geodesic (may be an antipodal point)".
 * fix __reduce__ method of Geod class so instances can be pickled.
 * make sure points outside projection limb are set to 1.e30 on inverse
   transform (if errcheck=False).
 * fixed small setup.py bug.
 * generate C source with Cython 0.9.6.6 (pycompat.h no longer needed).

1.8.2
~~~~~
 * added 'srs' (spatial reference system) instance variable to Proj.
 * instead of returning HUGE_VAL (usually 'inf') when projection not defined
   and errcheck=False, return 1.e30.
 * added Geod class for geodesic (i.e. Great Circle) computations.
   Includes doctests (which can be run with pyproj.test()).
 * proj.4 source code now included, thus removing proj.4 lib
   dependency. Version 4.5.0 is included, with a patch to
   create an API for geodesic computations.
 * python 2.4 compatibility patch (suggested by Andrew Straw)
   from M. v. Loewis:
   http://mail.python.org/pipermail/python-dev/2006-March/062561.html

1.8.1
~~~~~
 * if given tuples, returns tuples (instead of lists).
 * test for numpy arrays first.
 * Fixed error in docstring example.
 * README.html contains html docstrings generated by pydoc.
 * Renamed pyproj.so to _pyproj.so, created a new python module
   called pyproj.py.  Moved as code as possible from _pyproj.so to
   pyproj.py.
 * docstring examples now executed by doctest when 'pyproj.test()' is run.
 * added test to _pyproj.c which defines Py_ssize_t for python < 2.5.
   This is necessary when pyrex 0.9.5 is used.

1.8.0
~~~~~
 * Better error handling Proj.__init__.
 * Added optional keyword 'errcheck' to __call__ method.
 * If True, an exception is raised if the transformation is invalid.

1.7.3
~~~~~
 * python 2.5 support.
