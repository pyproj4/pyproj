Change Log
==========
2.1.1
~~~~~
* Restore behavior of 1.9.6 when illegal projection transformation requested
  (return ``inf`` instead of raising an exception, issue #202).  kwarg ``errcheck``
  added to :func:`pyproj.transform` and :func:`pyproj.itransform`
  (default ``False``). When ``errcheck=True`` an exception is raised.

2.1.0
~~~~~
* Added :class:`pyproj.Transformer` to make repetitive transformations more efficient (issue #187)
* Added fix for using local datumgrids with transform (issue #191)
* Added :class:`pyproj.Transformer.from_pipeline` to support pipeline transformations.
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
* Update to PROJ.4 version 6.0.0 & removed support for older PROJ.4 versions.
* Added pyproj.CRS class.
* Updated pyproj.Proj & pyproj.transform to accept any input from CRS.from_user_input.
* Removed internal PROJ.4 source code.
* Changed default for preserve_units to be True in pyproj.Proj class initialization.
* Modified logic for searching for the PROJ.4 data directory to not conflict with older versions of PROJ.4.
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

