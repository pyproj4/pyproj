# accumulator.py
#
# This is a rather literal translation of the GeographicLib::Accumulator
# class from to python.  See the documentation for the C++ class for
# more information at
#
#    http://sourceforge.net/html/annotated.html
#
# Copyright (c) Charles Karney (2011) <charles@karney.com> and licensed
# under the MIT/X11 License.  For more information, see
# http://sourceforge.net/
#
# $Id: 057b47320e60c424502f17f822629d5107c6f80d $
######################################################################

class Accumulator(object):
  """Like math.fsum, but allows a running sum"""

  def sum(u, v):
    # Error free transformation of a sum.  Note that t can be the same as one
    # of the first two arguments.
      s = u + v
      up = s - v
      vpp = s - up
      up -= u
      vpp -= v
      t = -(up + vpp)
      # u + v =       s      + t
      #       = round(u + v) + t
      return s, t
  sum = staticmethod(sum)

  def Set(self, y = 0.0):
    if type(self) == type(y):
      self._s, self._t = y._s, y._t
    else:
      self._s, self._t = float(y), 0.0

  def __init__(self, y = 0.0):
    self.Set(y)

  def Add(self, y):
    # Here's Shewchuk's solution...
    # hold exact sum as [s, t, u]
    y, u  = Accumulator.sum(y, self._t) # Accumulate starting at
    self._s, self._t = Accumulator.sum(y, self._s) # least significant end
    # Start is _s, _t decreasing and non-adjacent.  Sum is now (s + t + u)
    # exactly with s, t, u non-adjacent and in decreasing order (except
    # for possible zeros).  The following code tries to normalize the
    # result.  Ideally, we want _s = round(s+t+u) and _u = round(s+t+u -
    # _s).  The follow does an approximate job (and maintains the
    # decreasing non-adjacent property).  Here are two "failures" using
    # 3-bit floats:
    #
    # Case 1: _s is not equal to round(s+t+u) -- off by 1 ulp
    # [12, -1] - 8 -> [4, 0, -1] -> [4, -1] = 3 should be [3, 0] = 3
    #
    # Case 2: _s+_t is not as close to s+t+u as it shold be
    # [64, 5] + 4 -> [64, 8, 1] -> [64,  8] = 72 (off by 1)
    #                    should be [80, -7] = 73 (exact)
    #
    # "Fixing" these problems is probably not worth the expense.  The
    # representation inevitably leads to small errors in the accumulated
    # values.  The additional errors illustrated here amount to 1 ulp of
    # the less significant word during each addition to the Accumulator
    # and an additional possible error of 1 ulp in the reported sum.
    #
    # Incidentally, the "ideal" representation described above is not
    # canonical, because _s = round(_s + _t) may not be true.  For
    # example, with 3-bit floats:
    #
    # [128, 16] + 1 -> [160, -16] -- 160 = round(145).
    # But [160, 0] - 16 -> [128, 16] -- 128 = round(144).
    #
    if self._s == 0:            # This implies t == 0,
      self._s = u               # so result is u
    else:
      self._t += u              # otherwise just accumulate u to t.

  def Sum(self, y = 0.0):
    if y == 0.0:
      return self._s
    else:
      b = Accumulator(self)
      b.Add(y)
      return b._s

  def Negate(self):
    self._s *= -1
    self._t *= -1
