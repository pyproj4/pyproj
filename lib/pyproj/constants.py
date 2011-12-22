# constants.py
#
# This is a translation of the GeographicLib::Constants class to python.
# See the documentation for the C++ class for more information at
#
#    http://sourceforge.net/html/annotated.html
#
# Copyright (c) Charles Karney (2011) <charles@karney.com> and licensed
# under the MIT/X11 License.  For more information, see
# http://sourceforge.net/
#
# $Id: dd3c90107aedf80bead4c3f5c670df2b3eed7492 $
######################################################################

class Constants(object):
  """
  WGS84 constants:
    WGS84_a, the equatorial radius in meters
    WGS84_f, the flattening of the ellipsoid
  """

  WGS84_a = 6378137.0           # meters
  WGS84_f = 1/298.257223563
