from __future__ import with_statement
import sys, os, glob, subprocess, shutil
from distutils import ccompiler, sysconfig
from setuptools import setup, Extension

USE_CYTHON = False

# is this a repository
if not os.path.isfile("_proj.c"):
    # no _proj.c, repository
    USE_CYTHON = True

ext = '.pyx' if USE_CYTHON else '.c'

proj_dir = os.environ.get('PROJ_DIR')

# if PROJ_DIR env var is set, build against
# existing proj.4 installation.

if proj_dir is not None:
    sys.stderr.write('PROJ_DIR is set, using existing proj4 installation..\n')
    proj_libdir = os.environ.get('PROJ_LIBDIR')
    proj_incdir = os.environ.get('PROJ_INCDIR')
    libdirs=[]; incdirs = []; libraries = ['proj']

    if proj_libdir is None and proj_dir is not None:
        libdirs.append(os.path.join(proj_dir,'lib'))
        libdirs.append(os.path.join(proj_dir,'lib64'))
    if proj_incdir is None and proj_dir is not None:
        incdirs.append(os.path.join(proj_dir,'include'))

    pyprojext =\
    Extension("pyproj._proj",["_proj"+ext],include_dirs=incdirs,library_dirs=libdirs,\
    runtime_library_dirs=libdirs,libraries=libraries)

    # over-write default data directory.
    pyproj_datadir = os.path.join(os.path.join(proj_dir,'share'),'proj')
    datadirfile = os.path.join('lib',os.path.join('pyproj','datadir.py'))
    datadirfile_save = os.path.join('lib',os.path.join('pyproj','datadir.py.save'))
    if not os.path.isfile(datadirfile_save):
        shutil.copyfile(datadirfile, datadirfile_save)
    f = open(datadirfile,'w')
    f.write('pyproj_datadir="%s"\n' % pyproj_datadir)
    f.close()

    extensions = [pyprojext]
    package_data = {}

else:
    # use bundled proj.4
    sys.stderr.write('using bundled proj4..\n')

    # copy saved datadir.py back
    datadirfile = os.path.join('lib',os.path.join('pyproj','datadir.py'))
    datadirfile_save = os.path.join('lib',os.path.join('pyproj','datadir.py.save'))
    if os.path.isfile(datadirfile_save):
        shutil.move(datadirfile_save, datadirfile)

    deps = glob.glob('src/*.c')
    macros = []
    # these flags are set by configure when proj.4 lib is built.
    # enable pthreads support
    #macros.append(('MUTEX_pthread',1))
    #macros.append(('HAVE_PTHREAD_MUTEX_RECURSIVE',1))
    # you have localeconv
    #macros.append(('HAVE_LOCALECONV',1))
    # use strerror to print error messages
    #macros.append(('HAVE_STRERROR',1))
    # for win32 threads
    #macros.append(('MUTEX_win32',1))
    extensions = [Extension("pyproj._proj",deps+['_proj'+ext],
                  include_dirs=['src'],define_macros=macros)]

    # create binary datum shift grid files.
    pathout = os.path.join('lib',os.path.join('pyproj','data'))
    if len(sys.argv) > 1 and sys.argv[1] != 'sdist':
        cc = ccompiler.new_compiler()
        cc.define_macro('_CRT_SECURE_NO_WARNINGS')
        sysconfig.get_config_vars()
        sysconfig.customize_compiler(cc)
        cc.set_include_dirs(['src'])
        objects = cc.compile(['nad2bin.c', 'src/pj_malloc.c'])
        execname = 'nad2bin'
        cc.link_executable(objects, execname, extra_postargs = [ '/MANIFEST' ] if os.name == 'nt' else  None)
        llafiles = glob.glob('datumgrid/*.lla')
        cmd = os.path.join(os.getcwd(),execname)
        for f in llafiles:
            fout = os.path.basename(f.split('.lla')[0])
            fout = os.path.join(pathout,fout)
            strg = '%s %s < %s' % (cmd, fout, f)
            sys.stderr.write('executing %s\n'%strg)
            subprocess.call(strg,shell=True)

    datafiles = glob.glob(os.path.join(pathout,'*'))
    datafiles = [os.path.join('data',os.path.basename(f)) for f in datafiles]
    package_data = {'pyproj':datafiles}


# use Cython to generate the C code (_proj.c) from _proj.pyx
if USE_CYTHON:
    try:
        from Cython.Build import cythonize
    except ImportError:
        sys.stderr.write("\n\n_proj.c does not exist in a repository copy.\n"
                         "ImportError: Cython must be installed in order to generate _proj.c\n"
                         "\tto install Cython run `pip install cython`\n")
        sys.exit(1)

    extensions = cythonize(extensions)


# retreive pyproj version information (stored in _proj.pyx) in version variable
# (taken from Fiona)
with open('_proj.pyx', 'r') as f:
    for line in f:
        if line.find("__version__") >= 0:
            # parse __version__ and remove surrounding " or '
            version = line.split("=")[1].strip()[1:-1]
            break

packages          = ['pyproj']
package_dirs       = {'':'lib'}

setup(name = "pyproj",
  version = version,
  description = "Python interface to PROJ.4 library",
  long_description  = """
Performs cartographic transformations between geographic (lat/lon)
and map projection (x/y) coordinates. Can also transform directly
from one map projection coordinate system to another.
Coordinates can be given as numpy arrays, python arrays, lists or scalars.
Optimized for numpy arrays.""",
  url               = "https://github.com/jswhit/pyproj",
  download_url      = "http://python.org/pypi/pyproj",
  author            = "Jeff Whitaker",
  author_email      = "jeffrey.s.whitaker@noaa.gov",
  platforms         = ["any"],
  license           = "OSI Approved",
  keywords          = ["python","map projections","GIS","mapping","maps"],
  classifiers       = ["Development Status :: 4 - Beta",
                       "Intended Audience :: Science/Research",
                       "License :: OSI Approved",
                       "Programming Language :: Python :: 2",
                       "Programming Language :: Python :: 2.6",
                       "Programming Language :: Python :: 2.7",
                       "Programming Language :: Python :: 3",
                       "Programming Language :: Python :: 3.3",
                       "Programming Language :: Python :: 3.4",
                       "Programming Language :: Python :: 3.5",
                       "Topic :: Software Development :: Libraries :: Python Modules",
                       "Topic :: Scientific/Engineering :: GIS",
                       "Topic :: Scientific/Engineering :: Mathematics",
                       "Operating System :: OS Independent"],
  packages          = packages,
  package_dir       = package_dirs,
  ext_modules       = extensions,
  package_data      = package_data
  )
