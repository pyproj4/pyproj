# geomath.py
#
# This is a rather literal translation of the GeographicLib::Math class
# to python.  See the documentation for the C++ class for more
# information at
#
#    http://sourceforge.net/html/annotated.html
#
# Copyright (c) Charles Karney (2011) <charles@karney.com> and licensed
# under the MIT/X11 License.  For more information, see
# http://sourceforge.net/
#
# $Id: 9c5444e65f8541f8528ef2a504465e5565987c15 $
######################################################################

import sys
import math

class Math(object):
  """
  Additional math routines for GeographicLib.

  This defines constants:
    epsilon, difference between 1 and the next bigger number
    minval, minimum positive number
    maxval, maximum finite number
    degree, the number of radians in a degree
    nan, not a number
    int, infinity
  """
  
  epsilon = math.pow(2.0, -52)
  minval = math.pow(2.0, -1022)
  maxval = math.pow(2.0, 1023) * (2 - epsilon)
  degree = math.pi/180
  nan = float("nan")
  inf = float("inf")

  def sq(x):
    """Square a number"""

    return x * x
  sq = staticmethod(sq)

  def cbrt(x):
    """Real cube root of a number"""

    y = math.pow(abs(x), 1/3.0)
    return y if x >= 0 else -y
  cbrt = staticmethod(cbrt)

  def log1p(x):
    """log(1 + x) accurate for small x (missing from python 2.5.2)"""

    if sys.version_info > (2, 6):
      return math.log1p(x)

    y = 1 + x
    z = y - 1
    # Here's the explanation for this magic: y = 1 + z, exactly, and z
    # approx x, thus log(y)/z (which is nearly constant near z = 0) returns
    # a good approximation to the true log(1 + x)/x.  The multiplication x *
    # (log(y)/z) introduces little additional error.
    return x if z == 0 else x * math.log(y) / z
  log1p = staticmethod(log1p)

  def atanh(x):
    """atanh(x) (missing from python 2.5.2)"""

    if sys.version_info > (2, 6):
      return math.atanh(x)

    y = abs(x)                  # Enforce odd parity
    y = Math.log1p(2 * y/(1 - y))/2
    return -y if x < 0 else y
  atanh = staticmethod(atanh)

  def isfinite(x):
    """Test for finiteness"""

    return abs(x) <= Math.maxval
  isfinite = staticmethod(isfinite)
