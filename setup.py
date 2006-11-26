import os
from distutils.core import setup, Extension
proj_dir = os.environ.get('PROJ_DIR')
if not proj_dir:
    raise KeyError('please set the environment variable PROJ_DIR to point to the location of your proj.4 installation')
extensions = [Extension("pyproj",
                        ["pyproj.c",],
                        libraries = ['proj'],
                        library_dirs = [os.path.join(proj_dir,'lib')],
                        runtime_library_dirs = [os.path.join(proj_dir,'lib')],
                        include_dirs = [os.path.join(proj_dir,'include')])]
setup(name = "pyproj",
  version = "1.8.1",
  description = "Pyrex generated python interface to PROJ.4 library",
  long_description  = """
Performs cartographic transformations between geographic (lat/lon)
and map projection (x/y) coordinates. Can also transform directly
from one map projection coordinate system to another.
Coordinates can be given as umpy arrays, python arrays, lists or scalars.
Optimized for numpy arrays.""",
  url               = "http://code.google.com/p/pyproj/"
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
  ext_modules = extensions)
