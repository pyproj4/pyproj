import os
import subprocess
import sys
from collections import defaultdict
from distutils.spawn import find_executable
from glob import glob

from pkg_resources import parse_version
from setuptools import Extension, setup

PROJ_MIN_VERSION = parse_version("6.0.0")
CURRENT_FILE_PATH = os.path.dirname(os.path.abspath(__file__))
BASE_INTERNAL_PROJ_DIR = "proj_dir"
INTERNAL_PROJ_DIR = os.path.join(CURRENT_FILE_PATH, "pyproj", BASE_INTERNAL_PROJ_DIR)


def check_proj_version(proj_dir):
    """checks that the PROJ library meets the minimum version"""
    proj = os.path.join(proj_dir, "bin", "proj")
    try:
        proj_ver_bytes = subprocess.check_output([proj], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        if os.name == "nt":
            return
        raise
    proj_ver_bytes = (proj_ver_bytes.decode("ascii").split()[1]).strip(",")
    proj_version = parse_version(proj_ver_bytes)
    if proj_version < PROJ_MIN_VERSION:
        sys.exit(
            "ERROR: Minimum supported proj version is {}, installed "
            "version is {}.".format(PROJ_MIN_VERSION, proj_version)
        )

    return proj_version


def get_proj_dir():
    """
    This function finds the base PROJ directory.
    """
    proj_dir = os.environ.get("PROJ_DIR")
    if proj_dir is None and os.path.exists(INTERNAL_PROJ_DIR):
        proj_dir = INTERNAL_PROJ_DIR
        print("Internally compiled directory being used {}.".format(INTERNAL_PROJ_DIR))
    elif proj_dir is None and not os.path.exists(INTERNAL_PROJ_DIR):
        proj = find_executable("proj")
        if proj is None:
            sys.exit("Proj executable not found. Please set PROJ_DIR variable.")
        proj_dir = os.path.dirname(os.path.dirname(proj))
    elif proj_dir is not None and os.path.exists(proj_dir):
        print("PROJ_DIR is set, using existing proj4 installation..\n")
    else:
        sys.exit("ERROR: Invalid path for PROJ_DIR {}".format(proj_dir))

    # check_proj_version
    check_proj_version(proj_dir)
    return proj_dir


def get_proj_libdirs(proj_dir):
    """
    This function finds the library directories
    """
    proj_libdir = os.environ.get("PROJ_LIBDIR")
    libdirs = []
    if proj_libdir is None:
        libdir_search_paths = (
            os.path.join(proj_dir, "lib"),
            os.path.join(proj_dir, "lib64"),
        )
        for libdir_search_path in libdir_search_paths:
            if os.path.exists(libdir_search_path):
                libdirs.append(libdir_search_path)
        if not libdirs:
            sys.exit("ERROR: PROJ_LIBDIR dir not found. Please set PROJ_LIBDIR.")
    else:
        libdirs.append(proj_libdir)
    return libdirs


def get_proj_incdirs(proj_dir):
    """
    This function finds the include directories
    """
    proj_incdir = os.environ.get("PROJ_INCDIR")
    incdirs = []
    if proj_incdir is None:
        if os.path.exists(os.path.join(proj_dir, "include")):
            incdirs.append(os.path.join(proj_dir, "include"))
        else:
            sys.exit("ERROR: PROJ_INCDIR dir not found. Please set PROJ_INCDIR.")
    else:
        incdirs.append(proj_incdir)
    return incdirs


def get_cythonize_options():
    """
    This function gets the options to cythinize with
    """
    # Configure optional Cython coverage.
    cythonize_options = {"language_level": sys.version_info[0]}
    if os.environ.get("PYPROJ_FULL_COVERAGE"):
        cythonize_options["compiler_directives"] = {"linetrace": True}
        cythonize_options["annotate"] = True
    return cythonize_options


def get_libraries(libdirs):
    """
    This function gets the libraries to cythonize with
    """
    libraries = ["proj"]
    if os.name == "nt":
        for libdir in libdirs:
            projlib = glob(os.path.join(libdir, "proj*.lib"))
            if projlib:
                libraries = [os.path.basename(projlib[0]).split(".lib")[0]]
                break
    return libraries


def get_extension_modules():
    """
    This function retrieves the extension modules
    """
    if "clean" in sys.argv:
        return None

    # make sure cython is available
    try:
        from Cython.Build import cythonize
    except ImportError:
        sys.exit(
            "ERROR: Cython.Build.cythonize not found. "
            "Cython is required to build from a repo."
        )

    # By default we'll try to get options PROJ_DIR or the local version of proj
    proj_dir = get_proj_dir()
    library_dirs = get_proj_libdirs(proj_dir)
    include_dirs = get_proj_incdirs(proj_dir)

    # setup extension options
    ext_options = dict(
        include_dirs=include_dirs,
        library_dirs=library_dirs,
        runtime_library_dirs=library_dirs if os.name != "nt" else None,
        libraries=get_libraries(library_dirs),
    )
    if os.name != "nt":
        ext_options["embedsignature"] = True

    # setup cythonized modules
    return cythonize(
        [
            Extension("pyproj._proj", ["pyproj/_proj.pyx"], **ext_options),
            Extension("pyproj._geod", ["pyproj/_geod.pyx"], **ext_options),
            Extension("pyproj._crs", ["pyproj/_crs.pyx"], **ext_options),
            Extension(
                "pyproj._transformer", ["pyproj/_transformer.pyx"], **ext_options
            ),
            Extension("pyproj._datadir", ["pyproj/_datadir.pyx"], **ext_options),
        ],
        quiet=True,
        **get_cythonize_options()
    )


def get_package_data():
    """
    This function retrieves the package data
    """
    # setup package data
    package_data = defaultdict(list)
    if os.environ.get("PROJ_WHEEL") is not None and os.path.exists(INTERNAL_PROJ_DIR):
        package_data["pyproj"].append(
            os.path.join(BASE_INTERNAL_PROJ_DIR, "share", "proj", "*")
        )
    if os.environ.get("PROJ_WHEEL") is not None and os.path.exists(
        os.path.join(CURRENT_FILE_PATH, "pyproj", ".lib")
    ):
        package_data["pyproj"].append(os.path.join(".lib", "*"))

    return package_data


def get_version():
    """
    retreive pyproj version information (stored in _proj.pyx) in version variable
    (taken from Fiona)
    """
    with open(os.path.join("pyproj", "__init__.py"), "r") as f:
        for line in f:
            if line.find("__version__") >= 0:
                # parse __version__ and remove surrounding " or '
                return line.split("=")[1].strip()[1:-1]
    sys.exit("ERROR: pyproj version not fount.")


setup(
    name="pyproj",
    version=get_version(),
    description="Python interface to PROJ.4 library",
    long_description="""
Performs cartographic transformations between geographic (lat/lon)
and map projection (x/y) coordinates. Can also transform directly
from one map projection coordinate system to another.
Coordinates can be given as numpy arrays, python arrays, lists or scalars.
Optimized for numpy arrays.""",
    url="https://github.com/pyproj4/pyproj",
    download_url="http://python.org/pypi/pyproj",
    author="Jeff Whitaker",
    author_email="jeffrey.s.whitaker@noaa.gov",
    platforms=["any"],
    license="OSI Approved",
    keywords=["python", "map projections", "GIS", "mapping", "maps"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Operating System :: OS Independent",
    ],
    packages=["pyproj"],
    ext_modules=get_extension_modules(),
    package_data=get_package_data(),
)
