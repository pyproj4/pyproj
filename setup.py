import sys, os, glob, subprocess
from distutils import ccompiler, sysconfig
from distutils.core import setup, Extension

deps = glob.glob('src/*.c')
extensions = [Extension("pyproj._proj",deps+['_proj.c'],include_dirs = ['src'])]

# create binary datum shift grid files.
pathout = os.path.join('lib',os.path.join('pyproj','data'))
if sys.argv[1] != 'sdist':
    cc = ccompiler.new_compiler()
    #sysconfig.customize_compiler(cc) # doesn't work in python 3.3
    cc.set_include_dirs(['src'])
    objects = cc.compile(['nad2bin.c', 'src/pj_malloc.c'])
    execname = 'nad2bin'
    cc.link_executable(objects, execname)
    llafiles = glob.glob('datumgrid/*.lla')
    cmd = os.path.join(os.getcwd(),execname)
    for f in llafiles:
        fout = os.path.basename(f.split('.lla')[0])
        fout = os.path.join(pathout,fout)
        strg = '%s %s < %s' % (cmd, fout, f)
        sys.stdout.write('executing %s'%strg)
        subprocess.call(strg,shell=True)

packages          = ['pyproj']
package_dirs       = {'':'lib'}

datafiles = glob.glob(os.path.join(pathout,'*'))
datafiles = [os.path.join('data',os.path.basename(f)) for f in datafiles]
package_data = {'pyproj':datafiles}

setup(name = "pyproj",
  version = "1.9.3",
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
  ext_modules = extensions,
  package_data = package_data
  )
