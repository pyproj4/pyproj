import os, glob
from distutils.core import setup, Extension

deps = glob.glob('src/*.c')
extensions = [Extension("pyproj._proj",deps+['_proj.c'],include_dirs = ['src'])]
extensions.append(Extension("pyproj._geod",deps+['_geod.c'],include_dirs = ['src']))

packages          = ['pyproj']
package_dirs       = {'':'lib'}

path = os.path.join('lib',os.path.join('pyproj','data'))
datafiles = glob.glob(os.path.join(path,'*'))
datafiles = [os.path.join('data',os.path.basename(f)) for f in datafiles]
package_data = {'pyproj':datafiles}

setup(name = "pyproj",
  version = "1.8.7",
  description = "Pyrex generated python interface to PROJ.4 library",
  long_description  = """
Performs cartographic transformations between geographic (lat/lon)
and map projection (x/y) coordinates. Can also transform directly
from one map projection coordinate system to another.
Coordinates can be given as numpy arrays, python arrays, lists or scalars.
Optimized for numpy arrays.""",
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
  packages          = packages,
  package_dir       = package_dirs,
  ext_modules = extensions,
  package_data = package_data
  )
