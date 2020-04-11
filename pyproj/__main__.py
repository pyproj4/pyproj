"""
This is the main entry point for pyproj

e.g. python -m pyproj

"""

import argparse

from pyproj import __proj_version__, __version__, _show_versions

parser = argparse.ArgumentParser()
parser.add_argument(
    "-v",
    "--verbose",
    help="Show verbose debugging version information.",
    action="store_true",
)
args = parser.parse_args()
if args.verbose:
    _show_versions.show_versions()
else:
    print("pyproj version: {} [PROJ version: {}]".format(__version__, __proj_version__))
    parser.print_help()
