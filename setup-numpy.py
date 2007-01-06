import os
from numpy.distutils.core  import setup, Extension

# check to make sure PROJ_DIR env var set.
proj_dir = os.environ.get('PROJ_DIR')
if proj_dir is None:
    raise KeyError('please set the environment variable PROJ_DIR to point to the location of your proj.4 installation')

lib_dirs = [os.path.join(proj_dir,'lib')]
inc_dirs = [os.path.join(proj_dir,'include')]
libs = ['proj']

# build directly from .pyx file if USE_PYREX env var set.
use_pyrex = os.environ.get('USE_PYREX')
if use_pyrex:
    try:
        from Pyrex.Distutils import build_ext
    except:
        raise ImportError("Pyrex not installed - please unset USE_PYREX environment variable")
    srcs = ["_pyproj.pyx"]
    cmdclass = {'build_ext': build_ext}
# or else use pre-generated C source file.
else:
    srcs = ["_pyproj.c"]
    cmdclass = {}

extensions = [Extension("_pyproj",srcs,
              libraries=libs,library_dirs=lib_dirs,
              runtime_library_dirs=lib_dirs,include_dirs=inc_dirs)]

setup(name = "pyproj",
  version = "1.8.1",
  description = "Pyrex generated python interface to PROJ.4 library",
  long_description  = """
Performs cartographic transformations between geographic (lat/lon)
and map projection (x/y) coordinates. Can also transform directly
from one map projection coordinate system to another.
Coordinates can be given as umpy arrays, python arrays, lists or scalars.
Optimized for numpy arrays.""",
  url               = "http://code.google.com/p/pyproj",
  download_url      = "http://python.org/pypi/pyproj",
  author            = "Jeff Whitaker",
  author_email      = "jeffrey.s.whitaker@noaa.gov",
  platforms         = ["any"],
  license           = ["OSI Approved"],
  cmdclass          = cmdclass,
  keywords          = ["python","map projections","GIS","mapping","maps"],
  classifiers       = ["Development Status :: 4 - Beta",
			           "Intended Audience :: Science/Research", 
			           "License :: OSI Approved", 
			           "Topic :: Software Development :: Libraries :: Python Modules",
                       "Topic :: Scientific/Engineering :: GIS",
                       "Topic :: Scientific/Engineering :: Mathematics",
			           "Operating System :: OS Independent"],
  py_modules        = ['pyproj'],
  ext_modules = extensions)
