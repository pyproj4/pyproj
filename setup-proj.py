from distutils.core import setup, Extension
import os, glob, numpy, sys, subprocess
proj_dir = os.environ.get('PROJ_DIR')
proj_libdir = os.environ.get('PROJ_LIBDIR')
proj_incdir = os.environ.get('PROJ_INCDIR')
libdirs=[]
incdirs=[numpy.get_include()]
libraries=['proj']

if proj_libdir is None and proj_dir is not None: 
    libdirs.append(os.path.join(proj_dir,'lib'))
    libdirs.append(os.path.join(proj_dir,'lib64'))
if proj_incdir is None and proj_dir is not None: 
    incdirs.append(os.path.join(proj_dir,'include'))

pyprojext =\
Extension("pyproj._proj",["_proj.c"],include_dirs=incdirs,library_dirs=libdirs,libraries=libraries)

# to use datum shift grid files installed with proj, edit
# lib/pyproj/__init__.py and replace
# pyproj_datadir = os.sep.join([os.path.dirname(__file__), 'data'])
# with
# pyproj_datadir = os.path.join(os.path.join(proj_dir,'share'),'proj')

# create binary datum shift grid files.
#pathout = os.path.join('lib',os.path.join('pyproj','data'))
#if sys.argv[1] != 'sdist':
#    execname = 'nad2bin'
#    llafiles = glob.glob('datumgrid/*.lla')
#    cmd = os.path.join(proj_dir+'/bin',execname)
#    for f in llafiles:
#        fout = os.path.basename(f.split('.lla')[0])
#        fout = os.path.join(pathout,fout)
#        strg = '%s %s < %s' % (cmd, fout, f)
#        sys.stdout.write('executing %s'%strg)
#        subprocess.call(strg,shell=True)

packages          = ['pyproj']
package_dirs       = {'':'lib'}

#datafiles = glob.glob(os.path.join(pathout,'*'))
#datafiles = [os.path.join('data',os.path.basename(f)) for f in datafiles]
#package_data = {'pyproj':datafiles}

setup(name = "pyproj",
  version = "1.9.2",
  description = "Python interface to PROJ.4 library",
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
  license           = "OSI Approved",
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
  ext_modules = [pyprojext],
  #package_data = package_data
  )

