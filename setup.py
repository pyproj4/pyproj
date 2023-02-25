import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from pkg_resources import parse_version
from setuptools import Extension, setup

PROJ_MIN_VERSION = parse_version("9.0.0")
CURRENT_FILE_PATH = Path(__file__).absolute().parent
BASE_INTERNAL_PROJ_DIR = Path("proj_dir")
INTERNAL_PROJ_DIR = CURRENT_FILE_PATH / "pyproj" / BASE_INTERNAL_PROJ_DIR
PROJ_VERSION_SEARCH = re.compile(r".*Rel\.\s+(?P<version>\d+\.\d+\.\d+).*")


def get_proj_version(proj_dir: Path) -> str:
    proj_version = os.environ.get("PROJ_VERSION")
    if proj_version:
        return proj_version
    proj = proj_dir / "bin" / "proj"
    proj_ver = subprocess.check_output(str(proj), stderr=subprocess.STDOUT).decode(
        "ascii"
    )
    match = PROJ_VERSION_SEARCH.search(proj_ver)
    if not match:
        raise SystemExit(
            "PROJ version unable to be determined. "
            "Please set the PROJ_VERSION environment variable."
        )
    return match.groupdict()["version"]


def check_proj_version(proj_version: str) -> None:
    """checks that the PROJ library meets the minimum version"""
    if parse_version(proj_version) < PROJ_MIN_VERSION:
        raise SystemExit(
            f"ERROR: Minimum supported PROJ version is {PROJ_MIN_VERSION}, installed "
            f"version is {proj_version}. For more information see: "
            "https://pyproj4.github.io/pyproj/stable/installation.html"
        )


def get_proj_dir() -> Path:
    """
    This function finds the base PROJ directory.
    """
    proj_dir_environ = os.environ.get("PROJ_DIR")
    proj_dir: Optional[Path] = None
    if proj_dir_environ is not None:
        proj_dir = Path(proj_dir_environ)
    if proj_dir is None and INTERNAL_PROJ_DIR.exists():
        proj_dir = INTERNAL_PROJ_DIR
        print(f"Internally compiled directory being used {INTERNAL_PROJ_DIR}.")
    elif proj_dir is None and not INTERNAL_PROJ_DIR.exists():
        proj = shutil.which("proj", path=sys.prefix)
        if proj is None:
            proj = shutil.which("proj")
        if proj is None:
            raise SystemExit(
                "proj executable not found. Please set the PROJ_DIR variable. "
                "For more information see: "
                "https://pyproj4.github.io/pyproj/stable/installation.html"
            )
        proj_dir = Path(proj).parent.parent
    elif proj_dir is not None and proj_dir.exists():
        print("PROJ_DIR is set, using existing PROJ installation..\n")
    else:
        raise SystemExit(f"ERROR: Invalid path for PROJ_DIR {proj_dir}")
    return proj_dir


def get_proj_libdirs(proj_dir: Path) -> List[str]:
    """
    This function finds the library directories
    """
    proj_libdir = os.environ.get("PROJ_LIBDIR")
    libdirs = []
    if proj_libdir is None:
        libdir_search_paths = (proj_dir / "lib", proj_dir / "lib64")
        for libdir_search_path in libdir_search_paths:
            if libdir_search_path.exists():
                libdirs.append(str(libdir_search_path))
        if not libdirs:
            raise SystemExit(
                "ERROR: PROJ_LIBDIR dir not found. Please set PROJ_LIBDIR."
            )
    else:
        libdirs.append(proj_libdir)
    return libdirs


def get_proj_incdirs(proj_dir: Path) -> List[str]:
    """
    This function finds the include directories
    """
    proj_incdir = os.environ.get("PROJ_INCDIR")
    incdirs = []
    if proj_incdir is None:
        if (proj_dir / "include").exists():
            incdirs.append(str(proj_dir / "include"))
        else:
            raise SystemExit(
                "ERROR: PROJ_INCDIR dir not found. Please set PROJ_INCDIR."
            )
    else:
        incdirs.append(proj_incdir)
    return incdirs


def get_cythonize_options():
    """
    This function gets the options to cythonize with
    """
    # Configure optional Cython coverage.
    cythonize_options = {
        "language_level": sys.version_info[0],
        "compiler_directives": {
            "c_string_type": "str",
            "c_string_encoding": "utf-8",
            "embedsignature": True,
        },
    }
    if os.environ.get("PYPROJ_FULL_COVERAGE"):
        cythonize_options["compiler_directives"].update(linetrace=True)
        cythonize_options["annotate"] = True
    return cythonize_options


def get_libraries(libdirs: List[str]) -> List[str]:
    """
    This function gets the libraries to cythonize with
    """
    libraries = ["proj"]
    if os.name == "nt":
        for libdir in libdirs:
            projlib = list(Path(libdir).glob("proj*.lib"))
            if projlib:
                libraries = [str(projlib[0].stem)]
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
        raise SystemExit(
            "ERROR: Cython.Build.cythonize not found. "
            "Cython is required to build pyproj."
        )

    # By default we'll try to get options PROJ_DIR or the local version of proj
    proj_dir = get_proj_dir()
    library_dirs = get_proj_libdirs(proj_dir)
    include_dirs = get_proj_incdirs(proj_dir)

    proj_version = get_proj_version(proj_dir)
    check_proj_version(proj_version)
    proj_version_major, proj_version_minor, proj_version_patch = parse_version(
        proj_version
    ).base_version.split(".")

    # setup extension options
    ext_options = {
        "include_dirs": include_dirs,
        "library_dirs": library_dirs,
        "runtime_library_dirs": (
            library_dirs if os.name != "nt" and sys.platform != "cygwin" else None
        ),
        "libraries": get_libraries(library_dirs),
    }
    # setup cythonized modules
    return cythonize(
        [
            Extension("pyproj._geod", ["pyproj/_geod.pyx"], **ext_options),
            Extension("pyproj._crs", ["pyproj/_crs.pyx"], **ext_options),
            Extension(
                "pyproj._transformer", ["pyproj/_transformer.pyx"], **ext_options
            ),
            Extension("pyproj._compat", ["pyproj/_compat.pyx"], **ext_options),
            Extension("pyproj.database", ["pyproj/database.pyx"], **ext_options),
            Extension("pyproj._datadir", ["pyproj/_datadir.pyx"], **ext_options),
            Extension("pyproj.list", ["pyproj/list.pyx"], **ext_options),
            Extension("pyproj._network", ["pyproj/_network.pyx"], **ext_options),
            Extension("pyproj._sync", ["pyproj/_sync.pyx"], **ext_options),
        ],
        quiet=True,
        compile_time_env={
            "CTE_PROJ_VERSION_MAJOR": int(proj_version_major),
            "CTE_PROJ_VERSION_MINOR": int(proj_version_minor),
            "CTE_PROJ_VERSION_PATCH": int(proj_version_patch),
            "CTE_PYTHON_IMPLEMENTATION": platform.python_implementation(),
        },
        **get_cythonize_options(),
    )


def get_package_data() -> Dict[str, List[str]]:
    """
    This function retrieves the package data
    """
    # setup package data
    package_data = {"pyproj": ["*.pyi", "py.typed"]}
    if os.environ.get("PROJ_WHEEL") is not None and INTERNAL_PROJ_DIR.exists():
        package_data["pyproj"].append(
            str(BASE_INTERNAL_PROJ_DIR / "share" / "proj" / "*")
        )
    if (
        os.environ.get("PROJ_WHEEL") is not None
        and (CURRENT_FILE_PATH / "pyproj" / ".lib").exists()
    ):
        package_data["pyproj"].append(os.path.join(".lib", "*"))
    return package_data


# static items in setup.cfg
setup(
    ext_modules=get_extension_modules(),
    package_data=get_package_data(),
)
