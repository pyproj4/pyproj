import os
from numpy.distutils.core  import setup, Extension

# check to make sure PROJ_DIR env var set.
proj_dir = os.environ.get('PROJ_DIR')
if proj_dir is None:
    raise KeyError('please set the environment variable PROJ_DIR to point to the location of your proj.4 installation')

lib_dirs = [os.path.join(proj_dir,'lib')]
inc_dirs = [os.path.join(proj_dir,'include')]
libs = ['proj']
srcs = ["_pyproj_numpy.c"]

extensions = [Extension("_pyproj_numpy",srcs,
              libraries=libs,library_dirs=lib_dirs,
              runtime_library_dirs=lib_dirs,include_dirs=inc_dirs)]

setup(name = "pyproj_numpy",
  version = "1.8.1",
  description = "Pyrex generated python interface to PROJ.4 library (numpy version)",
  long_description  = """
Performs cartographic transformations between geographic (lat/lon)
and map projection (x/y) coordinates. Can also transform directly
from one map projection coordinate system to another.
Designed for use with numpy arrays""",
  url               = "http://code.google.com/p/pyproj",
  download_url      = "http://python.org/pypi/pyproj",
  author            = "Jeff Whitaker",
  author_email      = "jeffrey.s.whitaker@noaa.gov",
  platforms         = ["any"],
  license           = ["OSI Approved"],
  keywords          = ["python","map projections","GIS","mapping","maps"],
  classifiers       = ["Development Status :: 4 - Beta",
			           "Intended Audience :: Science/Research", 
			           "License :: OSI Approved", 
			           "Topic :: Software Development :: Libraries :: Python Modules",
                       "Topic :: Scientific/Engineering :: GIS",
                       "Topic :: Scientific/Engineering :: Mathematics",
			           "Operating System :: OS Independent"],
  py_modules        = ['pyproj_numpy'],
  ext_modules = extensions)
