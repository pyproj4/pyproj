# geodesic.py
#
# This is a rather literal translation of the GeographicLib::Geodesic
# class to python.  See the documentation for the C++ class for more
# information at
#
#    http://sourceforge.net/html/annotated.html
#
# The algorithms are derived in
#
#    Charles F. F. Karney,
#    Geodesics on an ellipsoid of revolution, Feb. 2011,
#    http://arxiv.org/abs/1102.1215
#    errata: http://sourceforge.net/geod-errata.html
#
#    Charles F. F. Karney,
#    Algorithms for geodesics, Sept. 2011,
#    http://arxiv.org/abs/1109.4448
#
# Copyright (c) Charles Karney (2011) <charles@karney.com> and licensed
# under the MIT/X11 License.  For more information, see
# http://sourceforge.net/
#
# $Id: 0df741f8ec25f4cccd4f69e9e2bed2ee152d42d0 $
######################################################################

import math
from pyproj.geomath import Math
from pyproj.constants import Constants
from pyproj.geodesiccapability import GeodesicCapability

class Geodesic(object):
  """
  Solve geodesic problems.  The following illustrates its use

    import sys
    sys.path.append("/usr/local/lib/python/site-packages");
    from geodesic import Geodesic

    # The geodesic inverse problem
    Geodesic.WGS84.Inverse(-41.32, 174.81, 40.96, -5.50)

    # The geodesic direct problem
    Geodesic.WGS84.Direct(40.6, -73.8, 45, 10000e3)

    # How to obtain several points along a geodesic
    line = Geodesic.WGS84.Line(40.6, -73.8, 45)
    line.Position( 5000e3)
    line.Position(10000e3)

    # Computing the area of a geodesic polygon
    def p(lat,lon): return {'lat': lat, 'lon': lon}

    Geodesic.WGS84.Area([p(0, 0), p(0, 90), p(90, 0)])

  Documentation on these routines is available via

    help(Geodesic.__init__)
    help(Geodesic.Inverse)
    help(Geodesic.Direct)
    help(Geodesic.Line)
    help(line.Position)
    help(Geodesic.Area)
  """

  GEOD_ORD = 6
  nA1_ = GEOD_ORD
  nC1_ = GEOD_ORD
  nC1p_ = GEOD_ORD
  nA2_ = GEOD_ORD
  nC2_ = GEOD_ORD
  nA3_ = GEOD_ORD
  nA3x_ = nA3_
  nC3_ = GEOD_ORD
  nC3x_ = (nC3_ * (nC3_ - 1)) / 2
  nC4_ = GEOD_ORD
  nC4x_ = (nC4_ * (nC4_ + 1)) / 2
  maxit_ = 50

  tiny_ = math.sqrt(Math.minval)
  tol0_ = Math.epsilon
  tol1_ = 200 * tol0_
  tol2_ = math.sqrt(Math.epsilon)
  xthresh_ = 1000 * tol2_

  CAP_NONE = GeodesicCapability.CAP_NONE
  CAP_C1   = GeodesicCapability.CAP_C1
  CAP_C1p  = 1<<1
  CAP_C2   = 1<<2
  CAP_C3   = 1<<3
  CAP_C4   = 1<<4
  CAP_ALL  = 0x1F
  OUT_ALL  = 0x7F80
  NONE          = 0
  LATITUDE      = 1<<7  | CAP_NONE
  LONGITUDE     = 1<<8  | CAP_C3
  AZIMUTH       = 1<<9  | CAP_NONE
  DISTANCE      = 1<<10 | CAP_C1
  DISTANCE_IN   = 1<<11 | CAP_C1 | CAP_C1p
  REDUCEDLENGTH = 1<<12 | CAP_C1 | CAP_C2
  GEODESICSCALE = 1<<13 | CAP_C1 | CAP_C2
  AREA          = 1<<14 | CAP_C4
  ALL           = OUT_ALL| CAP_ALL

  def SinCosSeries(sinp, sinx, cosx,  c, n):
    # Evaluate
    # y = sinp ? sum(c[i] * sin( 2*i    * x), i, 1, n) :
    #            sum(c[i] * cos((2*i+1) * x), i, 0, n-1) :
    # using Clenshaw summation.  N.B. c[0] is unused for sin series
    # Approx operation count = (n + 5) mult and (2 * n + 2) add
    k = (n + sinp)             # Point to one beyond last element
    ar = 2 * (cosx - sinx) * (cosx + sinx) # 2 * cos(2 * x)
    y1 = 0                                 # accumulators for sum
    if n & 1:
      k -= 1; y0 = c[k]
    else:
      y0 = 0
    # Now n is even
    n //= 2
    while n:                    # while n--:
      n -= 1
      # Unroll loop x 2, so accumulators return to their original role
      k -= 1; y1 = ar * y0 - y1 + c[k]
      k -= 1; y0 = ar * y1 - y0 + c[k]
    return ( 2 * sinx * cosx * y0 if sinp # sin(2 * x) * y0
             else cosx * (y0 - y1) )      # cos(x) * (y0 - y1)
  SinCosSeries = staticmethod(SinCosSeries)

  def AngNormalize(x):
    # Place angle in [-180, 180).  Assumes x is in [-540, 540).
    return (x - 360 if x >= 180 else
            (x + 360 if x < -180 else x))
  AngNormalize = staticmethod(AngNormalize)

  def AngRound(x):
    # The makes the smallest gap in x = 1/16 - nextafter(1/16, 0) = 1/2^57
    # for reals = 0.7 pm on the earth if x is an angle in degrees.  (This
    # is about 1000 times more resolution than we get with angles around 90
    # degrees.)  We use this to avoid having to deal with near singular
    # cases when x is non-zero but tiny (e.g., 1.0e-200).
    z = 0.0625                  # 1/16
    y = abs(x)
    # The compiler mustn't "simplify" z - (z - y) to y
    y =  z - (z - y) if y < z else y
    return -y if x < 0 else y
  AngRound = staticmethod(AngRound)

  def SinCosNorm(sinx, cosx):
    r = math.hypot(sinx, cosx)
    return sinx/r, cosx/r
  SinCosNorm = staticmethod(SinCosNorm)

  def Astroid(x, y):
    # Solve k^4+2*k^3-(x^2+y^2-1)*k^2-2*y^2*k-y^2 = 0 for positive root k.
    # This solution is adapted from Geocentric::Reverse.
    p = Math.sq(x)
    q = Math.sq(y)
    r = (p + q - 1) / 6
    if not(q == 0 and r <= 0):
      # Avoid possible division by zero when r = 0 by multiplying equations
      # for s and t by r^3 and r, resp.
      S = p * q / 4            # S = r^3 * s
      r2 = Math.sq(r)
      r3 = r * r2
      # The discrimant of the quadratic equation for T3.  This is zero on
      # the evolute curve p^(1/3)+q^(1/3) = 1
      disc =  S * (S + 2 * r3)
      u = r
      if (disc >= 0):
        T3 = S + r3
        # Pick the sign on the sqrt to maximize abs(T3).  This minimizes loss
        # of precision due to cancellation.  The result is unchanged because
        # of the way the T is used in definition of u.
        T3 += -math.sqrt(disc) if T3 < 0 else math.sqrt(disc) # T3 = (r * t)^3
        # N.B. cbrt always returns the real root.  cbrt(-8) = -2.
        T = Math.cbrt(T3)       # T = r * t
        # T can be zero; but then r2 / T -> 0.
        u += T + (r2 / T if T != 0 else 0)
      else:
        # T is complex, but the way u is defined the result is real.
        ang = math.atan2(math.sqrt(-disc), -(S + r3))
        # There are three possible cube roots.  We choose the root which
        # avoids cancellation.  Note that disc < 0 implies that r < 0.
        u += 2 * r * math.cos(ang / 3)
      v = math.sqrt(Math.sq(u) + q)  # guaranteed positive
      # Avoid loss of accuracy when u < 0.
      uv = q / (v - u) if u < 0 else u + v # u+v, guaranteed positive
      w = (uv - q) / (2 * v)               # positive?
      # Rearrange expression for k to avoid loss of accuracy due to
      # subtraction.  Division by 0 not possible because uv > 0, w >= 0.
      k = uv / (math.sqrt(uv + Math.sq(w)) + w) # guaranteed positive
    else:                                       # q == 0 && r <= 0
      # y = 0 with |x| <= 1.  Handle this case directly.
      # for y small, positive root is k = abs(y)/sqrt(1-x^2)
      k = 0
    return k
  Astroid = staticmethod(Astroid)

  def A1m1f(eps):
    eps2 = Math.sq(eps)
    t = eps2*(eps2*(eps2+4)+64)/256
    return (t + eps) / (1 - eps)
  A1m1f = staticmethod(A1m1f)

  def C1f(eps, c):
    eps2 = Math.sq(eps)
    d = eps
    c[1] = d*((6-eps2)*eps2-16)/32
    d *= eps
    c[2] = d*((64-9*eps2)*eps2-128)/2048
    d *= eps
    c[3] = d*(9*eps2-16)/768
    d *= eps
    c[4] = d*(3*eps2-5)/512
    d *= eps
    c[5] = -7*d/1280
    d *= eps
    c[6] = -7*d/2048
  C1f = staticmethod(C1f)

  def C1pf(eps, c):
    eps2 = Math.sq(eps)
    d = eps
    c[1] = d*(eps2*(205*eps2-432)+768)/1536
    d *= eps
    c[2] = d*(eps2*(4005*eps2-4736)+3840)/12288
    d *= eps
    c[3] = d*(116-225*eps2)/384
    d *= eps
    c[4] = d*(2695-7173*eps2)/7680
    d *= eps
    c[5] = 3467*d/7680
    d *= eps
    c[6] = 38081*d/61440
  C1pf = staticmethod(C1pf)

  def A2m1f(eps):
    eps2 = Math.sq(eps)
    t = eps2*(eps2*(25*eps2+36)+64)/256
    return t * (1 - eps) - eps
  A2m1f = staticmethod(A2m1f)

  def C2f(eps, c):
    eps2 = Math.sq(eps)
    d = eps
    c[1] = d*(eps2*(eps2+2)+16)/32
    d *= eps
    c[2] = d*(eps2*(35*eps2+64)+384)/2048
    d *= eps
    c[3] = d*(15*eps2+80)/768
    d *= eps
    c[4] = d*(7*eps2+35)/512
    d *= eps
    c[5] = 63*d/1280
    d *= eps
    c[6] = 77*d/2048
  C2f = staticmethod(C2f)

  def __init__(self, a, f):
    """
    Construct a Geodesic object for ellipsoid with major radius a and
    flattening f.
    """

    self._a = float(a)
    self._f = float(f) if f <= 1 else 1.0/f
    self._f1 = 1 - self._f
    self._e2 = self._f * (2 - self._f)
    self._ep2 = self._e2 / Math.sq(self._f1) # e2 / (1 - e2)
    self._n = self._f / ( 2 - self._f)
    self._b = self._a * self._f1
    # authalic radius squared
    self._c2 = (Math.sq(self._a) + Math.sq(self._b) *
                (1 if self._e2 == 0 else
                 (Math.atanh(math.sqrt(self._e2)) if self._e2 > 0 else
                  math.atan(math.sqrt(-self._e2))) /
                 math.sqrt(abs(self._e2))))/2
    self._etol2 = Geodesic.tol2_ / max(0.1, math.sqrt(abs(self._e2)))
    if not(Math.isfinite(self._a) and self._a > 0):
      raise ValueError("Major radius is not positive")
    if not(Math.isfinite(self._b) and self._b > 0):
      raise ValueError("Minor radius is not positive")
    self._A3x = list(range(int(Geodesic.nA3x_)))
    self._C3x = list(range(int(Geodesic.nC3x_)))
    self._C4x = list(range(int(Geodesic.nC4x_)))
    self.A3coeff()
    self.C3coeff()
    self.C4coeff()

  def A3coeff(self):
    _n = self._n
    self._A3x[0] = 1
    self._A3x[1] = (_n-1)/2
    self._A3x[2] = (_n*(3*_n-1)-2)/8
    self._A3x[3] = ((-_n-3)*_n-1)/16
    self._A3x[4] = (-2*_n-3)/64
    self._A3x[5] = -3/128.0

  def C3coeff(self):
    _n = self._n
    self._C3x[0] = (1-_n)/4
    self._C3x[1] = (1-_n*_n)/8
    self._C3x[2] = ((3-_n)*_n+3)/64
    self._C3x[3] = (2*_n+5)/128
    self._C3x[4] = 3/128.0
    self._C3x[5] = ((_n-3)*_n+2)/32
    self._C3x[6] = ((-3*_n-2)*_n+3)/64
    self._C3x[7] = (_n+3)/128
    self._C3x[8] = 5/256.0
    self._C3x[9] = (_n*(5*_n-9)+5)/192
    self._C3x[10] = (9-10*_n)/384
    self._C3x[11] = 7/512.0
    self._C3x[12] = (7-14*_n)/512
    self._C3x[13] = 7/512.0
    self._C3x[14] = 21/2560.0

  def C4coeff(self):
    _ep2 = self._ep2
    self._C4x[0] = (_ep2*(_ep2*(_ep2*((832-640*_ep2)*_ep2-1144)+1716)-3003)+
                    30030)/45045
    self._C4x[1] = (_ep2*(_ep2*((832-640*_ep2)*_ep2-1144)+1716)-3003)/60060
    self._C4x[2] = (_ep2*((208-160*_ep2)*_ep2-286)+429)/18018
    self._C4x[3] = ((104-80*_ep2)*_ep2-143)/10296
    self._C4x[4] = (13-10*_ep2)/1430
    self._C4x[5] = -1/156.0
    self._C4x[6] = (_ep2*(_ep2*(_ep2*(640*_ep2-832)+1144)-1716)+3003)/540540
    self._C4x[7] = (_ep2*(_ep2*(160*_ep2-208)+286)-429)/108108
    self._C4x[8] = (_ep2*(80*_ep2-104)+143)/51480
    self._C4x[9] = (10*_ep2-13)/6435
    self._C4x[10] = 5/3276.0
    self._C4x[11] = (_ep2*((208-160*_ep2)*_ep2-286)+429)/900900
    self._C4x[12] = ((104-80*_ep2)*_ep2-143)/257400
    self._C4x[13] = (13-10*_ep2)/25025
    self._C4x[14] = -1/2184.0
    self._C4x[15] = (_ep2*(80*_ep2-104)+143)/2522520
    self._C4x[16] = (10*_ep2-13)/140140
    self._C4x[17] = 5/45864.0
    self._C4x[18] = (13-10*_ep2)/1621620
    self._C4x[19] = -1/58968.0
    self._C4x[20] = 1/792792.0

  def A3f(self, eps):
    # Evaluation sum(_A3c[k] * eps^k, k, 0, nA3x_-1) by Horner's method
    v = 0
    for i in range(Geodesic.nA3x_-1, -1, -1):
      v = eps * v + self._A3x[i]
    return v

  def C3f(self, eps, c):
    # Evaluation C3 coeffs by Horner's method
    # Elements c[1] thru c[nC3_ - 1] are set
    j = int(Geodesic.nC3x_); k = int(Geodesic.nC3_) - 1
    while k:
      t = 0
      for i in range(Geodesic.nC3_ - k):
        j -= 1
        t = eps * t + self._C3x[j]
      c[k] = t
      k -= 1

    mult = 1
    for k in range(1, Geodesic.nC3_):
      mult *= eps
      c[k] *= mult

  def C4f(self, k2, c):
    # Evaluation C4 coeffs by Horner's method
    # Elements c[0] thru c[nC4_ - 1] are set
    j = int(Geodesic.nC4x_); k = int(Geodesic.nC4_)
    while k:
      t = 0
      for i in range(Geodesic.nC4_ - k + 1):
        j -= 1
        t = k2 * t + self._C4x[j]
      k -= 1
      c[k] = t

    mult = 1
    for k in range(1, Geodesic.nC4_):
      mult *= k2
      c[k] *= mult

  # return s12b, m12a, m0, M12, M21
  def Lengths(self, eps, sig12,
              ssig1, csig1, ssig2, csig2, cbet1, cbet2, scalep,
              # Scratch areas of the right size
              C1a, C2a):
    # Return m12a = (reduced length)/_a; also calculate s12b = distance/_b,
    # and m0 = coefficient of secular term in expression for reduced length.
    Geodesic.C1f(eps, C1a)
    Geodesic.C2f(eps, C2a)
    A1m1 = Geodesic.A1m1f(eps)
    AB1 = (1 + A1m1) * (
      Geodesic.SinCosSeries(True, ssig2, csig2, C1a, Geodesic.nC1_) -
      Geodesic.SinCosSeries(True, ssig1, csig1, C1a, Geodesic.nC1_))
    A2m1 = Geodesic.A2m1f(eps)
    AB2 = (1 + A2m1) * (
      Geodesic.SinCosSeries(True, ssig2, csig2, C2a, Geodesic.nC2_) -
      Geodesic.SinCosSeries(True, ssig1, csig1, C2a, Geodesic.nC2_))
    cbet1sq = Math.sq(cbet1)
    cbet2sq = Math.sq(cbet2)
    w1 = math.sqrt(1 - self._e2 * cbet1sq)
    w2 = math.sqrt(1 - self._e2 * cbet2sq)
    # Make sure it's OK to have repeated dummy arguments
    m0x = A1m1 - A2m1
    J12 = m0x * sig12 + (AB1 - AB2)
    m0 = m0x
    # Missing a factor of _a.
    # Add parens around (csig1 * ssig2) and (ssig1 * csig2) to ensure accurate
    # cancellation in the case of coincident points.
    m12a = ((w2 * (csig1 * ssig2) - w1 * (ssig1 * csig2))
            - self._f1 * csig1 * csig2 * J12)
    # Missing a factor of _b
    s12b =  (1 + A1m1) * sig12 + AB1
    if scalep:
      csig12 = csig1 * csig2 + ssig1 * ssig2
      J12 *= self._f1
      M12 = csig12 + (self._e2 * (cbet1sq - cbet2sq) * ssig2 / (w1 + w2)
                      - csig2 * J12) * ssig1 / w1
      M21 = csig12 - (self._e2 * (cbet1sq - cbet2sq) * ssig1 / (w1 + w2)
                        - csig1 * J12) * ssig2 / w2
    else:
      M12 = M21 = Math.nan
    return s12b, m12a, m0, M12, M21

  # return sig12, salp1, calp1, salp2, calp2
  def InverseStart(self, sbet1, cbet1, sbet2, cbet2, lam12,
                   # Scratch areas of the right size
                   C1a, C2a):
    # Return a starting point for Newton's method in salp1 and calp1 (function
    # value is -1).  If Newton's method doesn't need to be used, return also
    # salp2 and calp2 and function value is sig12.
    sig12 = -1; salp2 = calp2 = Math.nan # Return values
    # bet12 = bet2 - bet1 in [0, pi); bet12a = bet2 + bet1 in (-pi, 0]
    sbet12 = sbet2 * cbet1 - cbet2 * sbet1
    cbet12 = cbet2 * cbet1 + sbet2 * sbet1
    # Volatile declaration needed to fix inverse cases
    # 88.202499451857 0 -88.202499451857 179.981022032992859592
    # 89.262080389218 0 -89.262080389218 179.992207982775375662
    # 89.333123580033 0 -89.333123580032997687 179.99295812360148422
    # which otherwise fail with g++ 4.4.4 x86 -O3
    sbet12a = sbet2 * cbet1
    sbet12a += cbet2 * sbet1

    shortline = cbet12 >= 0 and sbet12 < 0.5 and lam12 <= math.pi / 6
    omg12 =  (lam12 / math.sqrt(1 - self._e2 * Math.sq(cbet1)) if shortline
              else lam12)
    somg12 = math.sin(omg12); comg12 = math.cos(omg12)

    salp1 = cbet2 * somg12
    calp1 = (
      sbet12 + cbet2 * sbet1 * Math.sq(somg12) / (1 + comg12)  if comg12 >= 0
      else sbet12a - cbet2 * sbet1 * Math.sq(somg12) / (1 - comg12))

    ssig12 = math.hypot(salp1, calp1)
    csig12 = sbet1 * sbet2 + cbet1 * cbet2 * comg12

    if shortline and ssig12 < self._etol2:
      # really short lines
      salp2 = cbet1 * somg12
      calp2 = sbet12 - cbet1 * sbet2 * Math.sq(somg12) / (1 + comg12)
      salp2, calp2 = Geodesic.SinCosNorm(salp2, calp2)
      # Set return value
      sig12 = math.atan2(ssig12, csig12)
    elif csig12 >= 0 or ssig12 >= 3 * abs(self._f) * math.pi * Math.sq(cbet1):
      # Nothing to do, zeroth order spherical approximation is OK
      pass
    else:
      # Scale lam12 and bet2 to x, y coordinate system where antipodal point
      # is at origin and singular point is at y = 0, x = -1.
      # real y, lamscale, betscale
      # Volatile declaration needed to fix inverse case
      # 56.320923501171 0 -56.320923501171 179.664747671772880215
      # which otherwise fails with g++ 4.4.4 x86 -O3
      # volatile real x
      if self._f >= 0:            # In fact f == 0 does not get here
        # x = dlong, y = dlat
        k2 = Math.sq(sbet1) * self._ep2
        eps = k2 / (2 * (1 + math.sqrt(1 + k2)) + k2)
        lamscale = self._f * cbet1 * self.A3f(eps) * math.pi
        betscale = lamscale * cbet1
        x = (lam12 - math.pi) / lamscale
        y = sbet12a / betscale
      else:                     # _f < 0
        # x = dlat, y = dlong
        cbet12a = cbet2 * cbet1 - sbet2 * sbet1
        bet12a = math.atan2(sbet12a, cbet12a)
        # real m12a, m0, dummy
        # In the case of lon12 = 180, this repeats a calculation made in
        # Inverse.
        dummy, m12a, m0, dummy, dummy = self.Lengths(
          self._n, math.pi + bet12a, sbet1, -cbet1, sbet2, cbet2,
          cbet1, cbet2, dummy, False, C1a, C2a)
        x = -1 + m12a/(self._f1 * cbet1 * cbet2 * m0 * math.pi)
        betscale = (sbet12a / x if x < -real(0.01)
                    else -self._f * Math.sq(cbet1) * math.pi)
        lamscale = betscale / cbet1
        y = (lam12 - math.pi) / lamscale

      if y > -Geodesic.tol1_ and x >  -1 - Geodesic.xthresh_:
        # strip near cut
        if self._f >= 0:
          salp1 = min(1.0, -x); calp1 = - math.sqrt(1 - Math.sq(salp1))
        else:
          calp1 = max((0.0 if x > -Geodesic.tol1_ else -1.0),  x)
          salp1 = math.sqrt(1 - Math.sq(calp1))
      else:
        # Estimate alp1, by solving the astroid problem.
        #
        # Could estimate alpha1 = theta + pi/2, directly, i.e.,
        #   calp1 = y/k; salp1 = -x/(1+k);  for _f >= 0
        #   calp1 = x/(1+k); salp1 = -y/k;  for _f < 0 (need to check)
        #
        # However, it's better to estimate omg12 from astroid and use
        # spherical formula to compute alp1.  This reduces the mean number of
        # Newton iterations for astroid cases from 2.24 (min 0, max 6) to 2.12
        # (min 0 max 5).  The changes in the number of iterations are as
        # follows:
        #
        # change percent
        #    1       5
        #    0      78
        #   -1      16
        #   -2       0.6
        #   -3       0.04
        #   -4       0.002
        #
        # The histogram of iterations is (m = number of iterations estimating
        # alp1 directly, n = number of iterations estimating via omg12, total
        # number of trials = 148605):
        #
        #  iter    m      n
        #    0   148    186
        #    1 13046  13845
        #    2 93315 102225
        #    3 36189  32341
        #    4  5396      7
        #    5   455      1
        #    6    56      0
        #
        # Because omg12 is near pi, estimate work with omg12a = pi - omg12
        k = Geodesic.Astroid(x, y)
        omg12a = lamscale * ( -x * k/(1 + k) if self._f >= 0
                               else -y * (1 + k)/k )
        somg12 = math.sin(omg12a); comg12 = -math.cos(omg12a)
        # Update spherical estimate of alp1 using omg12 instead of lam12
        salp1 = cbet2 * somg12
        calp1 = sbet12a - cbet2 * sbet1 * Math.sq(somg12) / (1 - comg12)
    salp1, calp1 = Geodesic.SinCosNorm(salp1, calp1)
    return sig12, salp1, calp1, salp2, calp2

  # return lam12, salp2, calp2, sig12, ssig1, csig1, ssig2, csig2, eps,
  # domg12, dlam12
  def Lambda12(self, sbet1, cbet1, sbet2, cbet2, salp1, calp1, diffp,
               # Scratch areas of the right size
               C1a, C2a, C3a):

    if sbet1 == 0 and calp1 == 0:
      # Break degeneracy of equatorial line.  This case has already been
      # handled.
      calp1 = -Geodesic.tiny_

    # sin(alp1) * cos(bet1) = sin(alp0)
    salp0 = salp1 * cbet1
    calp0 = math.hypot(calp1, salp1 * sbet1) # calp0 > 0

    # real somg1, comg1, somg2, comg2, omg12, lam12
    # tan(bet1) = tan(sig1) * cos(alp1)
    # tan(omg1) = sin(alp0) * tan(sig1) = tan(omg1)=tan(alp1)*sin(bet1)
    ssig1 = sbet1; somg1 = salp0 * sbet1
    csig1 = comg1 = calp1 * cbet1
    ssig1, csig1 = Geodesic.SinCosNorm(ssig1, csig1)
    # SinCosNorm(somg1, comg1); -- don't need to normalize!

    # Enforce symmetries in the case abs(bet2) = -bet1.  Need to be careful
    # about this case, since this can yield singularities in the Newton
    # iteration.
    # sin(alp2) * cos(bet2) = sin(alp0)
    salp2 = salp0 / cbet2 if cbet2 != cbet1 else salp1
    # calp2 = sqrt(1 - sq(salp2))
    #       = sqrt(sq(calp0) - sq(sbet2)) / cbet2
    # and subst for calp0 and rearrange to give (choose positive sqrt
    # to give alp2 in [0, pi/2]).
    calp2 = (math.sqrt(Math.sq(calp1 * cbet1) +
                       ((cbet2 - cbet1) * (cbet1 + cbet2) if cbet1 < -sbet1
                        else (sbet1 - sbet2) * (sbet1 + sbet2))) / cbet2
             if cbet2 != cbet1 or abs(sbet2) != -sbet1 else abs(calp1))
    # tan(bet2) = tan(sig2) * cos(alp2)
    # tan(omg2) = sin(alp0) * tan(sig2).
    ssig2 = sbet2; somg2 = salp0 * sbet2
    csig2 = comg2 = calp2 * cbet2
    ssig2, csig2 = Geodesic.SinCosNorm(ssig2, csig2)
    # SinCosNorm(somg2, comg2); -- don't need to normalize!

    # sig12 = sig2 - sig1, limit to [0, pi]
    sig12 = math.atan2(max(csig1 * ssig2 - ssig1 * csig2, 0.0),
                       csig1 * csig2 + ssig1 * ssig2)

    # omg12 = omg2 - omg1, limit to [0, pi]
    omg12 = math.atan2(max(comg1 * somg2 - somg1 * comg2, 0.0),
                       comg1 * comg2 + somg1 * somg2)
    # real B312, h0
    k2 = Math.sq(calp0) * self._ep2
    eps = k2 / (2 * (1 + math.sqrt(1 + k2)) + k2)
    self.C3f(eps, C3a)
    B312 = (Geodesic.SinCosSeries(True, ssig2, csig2, C3a, Geodesic.nC3_-1) -
            Geodesic.SinCosSeries(True, ssig1, csig1, C3a, Geodesic.nC3_-1))
    h0 = -self._f * self.A3f(eps)
    domg12 = salp0 * h0 * (sig12 + B312)
    lam12 = omg12 + domg12

    if diffp:
      if calp2 == 0:
        dlam12 = - 2 * math.sqrt(1 - self._e2 * Math.sq(cbet1)) / sbet1
      else:
        dummy, dlam12, dummy, dummy, dummy = self.Lengths(
          eps, sig12, ssig1, csig1, ssig2, csig2, cbet1, cbet2, False, C1a, C2a)
        dlam12 /= calp2 * cbet2
    else:
      dlam12 = Math.nan

    return (lam12, salp2, calp2, sig12, ssig1, csig1, ssig2, csig2, eps,
            domg12, dlam12)

  # return a12, s12, azi1, azi2, m12, M12, M21, S12
  def GenInverse(self, lat1, lon1, lat2, lon2, outmask):
    a12 = s12 = azi1 = azi2 = m12 = M12 = M21 = S12 = Math.nan # return vals

    outmask &= Geodesic.OUT_ALL
    lon1 = Geodesic.AngNormalize(lon1)
    lon12 = Geodesic.AngNormalize(Geodesic.AngNormalize(lon2) - lon1)
    # If very close to being on the same meridian, then make it so.
    # Not sure this is necessary...
    lon12 = Geodesic.AngRound(lon12)
    # Make longitude difference positive.
    lonsign = 1 if lon12 >= 0 else -1
    lon12 *= lonsign
    if lon12 == 180:
      lonsign = 1
    # If really close to the equator, treat as on equator.
    lat1 = Geodesic.AngRound(lat1)
    lat2 = Geodesic.AngRound(lat2)
    # Swap points so that point with higher (abs) latitude is point 1
    swapp = 1 if abs(lat1) >= abs(lat2) else -1
    if swapp < 0:
      lonsign *= -1
      lat2, lat1 = lat1, lat2
    # Make lat1 <= 0
    latsign = 1 if lat1 < 0 else -1
    lat1 *= latsign
    lat2 *= latsign
    # Now we have
    #
    #     0 <= lon12 <= 180
    #     -90 <= lat1 <= 0
    #     lat1 <= lat2 <= -lat1
    #
    # longsign, swapp, latsign register the transformation to bring the
    # coordinates to this canonical form.  In all cases, 1 means no change was
    # made.  We make these transformations so that there are few cases to
    # check, e.g., on verifying quadrants in atan2.  In addition, this
    # enforces some symmetries in the results returned.

    # real phi, sbet1, cbet1, sbet2, cbet2, s12x, m12x

    phi = lat1 * Math.degree
    # Ensure cbet1 = +epsilon at poles
    sbet1 = self._f1 * math.sin(phi)
    cbet1 = Geodesic.tiny_ if lat1 == -90 else math.cos(phi)
    sbet1, cbet1 = Geodesic.SinCosNorm(sbet1, cbet1)

    phi = lat2 * Math.degree
    # Ensure cbet2 = +epsilon at poles
    sbet2 = self._f1 * math.sin(phi)
    cbet2 = Geodesic.tiny_ if abs(lat2) == 90 else math.cos(phi)
    sbet2, cbet2 = Geodesic.SinCosNorm(sbet2, cbet2)

    # If cbet1 < -sbet1, then cbet2 - cbet1 is a sensitive measure of the
    # |bet1| - |bet2|.  Alternatively (cbet1 >= -sbet1), abs(sbet2) + sbet1 is
    # a better measure.  This logic is used in assigning calp2 in Lambda12.
    # Sometimes these quantities vanish and in that case we force bet2 = +/-
    # bet1 exactly.  An example where is is necessary is the inverse problem
    # 48.522876735459 0 -48.52287673545898293 179.599720456223079643
    # which failed with Visual Studio 10 (Release and Debug)

    if cbet1 < -sbet1:
      if cbet2 == cbet1:
        sbet2 = sbet1 if sbet2 < 0 else -sbet1
    else:
      if abs(sbet2) == -sbet1:
        cbet2 = cbet1

    lam12 = lon12 * Math.degree
    slam12 = 0 if lon12 == 180 else math.sin(lam12)
    clam12 = math.cos(lam12)      # lon12 == 90 isn't interesting

    # real a12, sig12, calp1, salp1, calp2, salp2
    # index zero elements of these arrays are unused
    C1a = list(range(Geodesic.nC1_ + 1))
    C2a = list(range(Geodesic.nC2_ + 1))
    C3a = list(range(Geodesic.nC3_))

    meridian = lat1 == -90 or slam12 == 0

    if meridian:

      # Endpoints are on a single full meridian, so the geodesic might lie on
      # a meridian.

      calp1 = clam12; salp1 = slam12 # Head to the target longitude
      calp2 = 1; salp2 = 0           # At the target we're heading north

      # tan(bet) = tan(sig) * cos(alp)
      ssig1 = sbet1; csig1 = calp1 * cbet1
      ssig2 = sbet2; csig2 = calp2 * cbet2

      # sig12 = sig2 - sig1
      sig12 = math.atan2(max(csig1 * ssig2 - ssig1 * csig2, 0.0),
                         csig1 * csig2 + ssig1 * ssig2)

      s12x, m12x, dummy, M12, M21 = self.Lengths(
        self._n, sig12, ssig1, csig1, ssig2, csig2, cbet1, cbet2,
        (outmask & Geodesic.GEODESICSCALE) != 0, C1a, C2a)

      # Add the check for sig12 since zero length geodesics might yield m12 <
      # 0.  Test case was
      #
      #    echo 20.001 0 20.001 0 | Geod -i
      #
      # In fact, we will have sig12 > pi/2 for meridional geodesic which is
      # not a shortest path.
      if sig12 < 1 or m12x >= 0:
        m12x *= self._a
        s12x *= self._b
        a12 = sig12 / Math.degree
      else:
        # m12 < 0, i.e., prolate and too close to anti-podal
        meridian = False
    # end if meridian:

    #real omg12
    if (not meridian and
        sbet1 == 0 and   # and sbet2 == 0
        # Mimic the way Lambda12 works with calp1 = 0
        (self._f <= 0 or lam12 <= math.pi - self._f * math.pi)):

      # Geodesic runs along equator
      calp1 = calp2 = 0; salp1 = salp2 = 1
      s12x = self._a * lam12
      m12x = self._b * math.sin(lam12 / self._f1)
      if outmask & Geodesic.GEODESICSCALE:
        M12 = M21 = math.cos(lam12 / self._f1)
      a12 = lon12 / self._f1
      sig12 = omg12 = lam12 / self._f1

    elif not meridian:

      # Now point1 and point2 belong within a hemisphere bounded by a
      # meridian and geodesic is neither meridional or equatorial.

      # Figure a starting point for Newton's method
      sig12, salp1, calp1, salp2, calp2 = self.InverseStart(
        sbet1, cbet1, sbet2, cbet2, lam12, C1a, C2a)

      if sig12 >= 0:
        # Short lines (InverseStart sets salp2, calp2)
        w1 = math.sqrt(1 - self._e2 * Math.sq(cbet1))
        s12x = sig12 * self._a * w1
        m12x = (Math.sq(w1) * self._a / self._f1 *
                math.sin(sig12 * self._f1 / w1))
        if outmask & Geodesic.GEODESICSCALE:
          M12 = M21 = math.cos(sig12 * self._f1 / w1)
        a12 = sig12 / Math.degree
        omg12 = lam12 / w1
      else:

        # Newton's method
        # real ssig1, csig1, ssig2, csig2, eps
        ov = numit = trip = 0

        while numit < Geodesic.maxit_:
          (nlam12, salp2, calp2, sig12, ssig1, csig1, ssig2, csig2,
           eps, omg12, dv) = self.Lambda12(
            sbet1, cbet1, sbet2, cbet2, salp1, calp1, trip < 1, C1a, C2a, C3a)
          v = nlam12 - lam12
          if not(abs(v) > Geodesic.tiny_) or not(trip < 1):
            if not(abs(v) <= max(Geodesic.tol1_, ov)):
              numit = Geodesic.maxit_
            break
          dalp1 = -v/dv
          sdalp1 = math.sin(dalp1); cdalp1 = math.cos(dalp1)
          nsalp1 = salp1 * cdalp1 + calp1 * sdalp1
          calp1 = calp1 * cdalp1 - salp1 * sdalp1
          salp1 = max(0.0, nsalp1)
          salp1, calp1 = Geodesic.SinCosNorm(salp1, calp1)
          # In some regimes we don't get quadratic convergence because slope
          # -> 0.  So use convergence conditions based on epsilon instead of
          # sqrt(epsilon).  The first criterion is a test on abs(v) against
          # 100 * epsilon.  The second takes credit for an anticipated
          # reduction in abs(v) by v/ov (due to the latest update in alp1) and
          # checks this against epsilon.
          if not(abs(v) >= Geodesic.tol1_ and
                 Math.sq(v) >= ov * Geodesic.tol0_):
            trip += 1
          ov = abs(v)
          numit += 1

        if numit >= Geodesic.maxit_:
          # Signal failure.
          return a12, s12, azi1, azi2, m12, M12, M21, S12

        s12x, m12x, dummy, M12, M21 = self.Lengths(
          eps, sig12, ssig1, csig1, ssig2, csig2, cbet1, cbet2,
          (outmask & Geodesic.GEODESICSCALE) != 0, C1a, C2a)

        m12x *= self._a
        s12x *= self._b
        a12 = sig12 / Math.degree
        omg12 = lam12 - omg12
    # end elif not meridian

    if outmask & Geodesic.DISTANCE:
      s12 = 0 + s12x           # Convert -0 to 0

    if outmask & Geodesic.REDUCEDLENGTH:
      m12 = 0 + m12x           # Convert -0 to 0

    if outmask & Geodesic.AREA:
      # From Lambda12: sin(alp1) * cos(bet1) = sin(alp0)
      salp0 = salp1 * cbet1
      calp0 = math.hypot(calp1, salp1 * sbet1) # calp0 > 0
      # real alp12
      if calp0 != 0 and salp0 != 0:
        # From Lambda12: tan(bet) = tan(sig) * cos(alp)
        ssig1 = sbet1; csig1 = calp1 * cbet1
        ssig2 = sbet2; csig2 = calp2 * cbet2
        k2 = Math.sq(calp0) * self._ep2
        # Multiplier = a^2 * e^2 * cos(alpha0) * sin(alpha0).
        A4 = Math.sq(self._a) * calp0 * salp0 * self._e2
        ssig1, csig1 = Geodesic.SinCosNorm(ssig1, csig1)
        ssig2, csig2 = Geodesic.SinCosNorm(ssig2, csig2)
        C4a = list(range(Geodesic.nC4_))
        self.C4f(k2, C4a)
        B41 = Geodesic.SinCosSeries(False, ssig1, csig1, C4a, Geodesic.nC4_)
        B42 = Geodesic.SinCosSeries(False, ssig2, csig2, C4a, Geodesic.nC4_)
        S12 = A4 * (B42 - B41)
      else:
        # Avoid problems with indeterminate sig1, sig2 on equator
        S12 = 0
      if (not meridian and
          omg12 < 0.75 * math.pi and # Long difference too big
          sbet2 - sbet1 < 1.75):     # Lat difference too big
        # Use tan(Gamma/2) = tan(omg12/2)
        # * (tan(bet1/2)+tan(bet2/2))/(1+tan(bet1/2)*tan(bet2/2))
        # with tan(x/2) = sin(x)/(1+cos(x))
        somg12 = math.sin(omg12); domg12 = 1 + math.cos(omg12)
        dbet1 = 1 + cbet1; dbet2 = 1 + cbet2
        alp12 = 2 * math.atan2( somg12 * ( sbet1 * dbet2 + sbet2 * dbet1 ),
                                domg12 * ( sbet1 * sbet2 + dbet1 * dbet2 ) )
      else:
        # alp12 = alp2 - alp1, used in atan2 so no need to normalize
        salp12 = salp2 * calp1 - calp2 * salp1
        calp12 = calp2 * calp1 + salp2 * salp1
        # The right thing appears to happen if alp1 = +/-180 and alp2 = 0, viz
        # salp12 = -0 and alp12 = -180.  However this depends on the sign
        # being attached to 0 correctly.  The following ensures the correct
        # behavior.
        if salp12 == 0 and calp12 < 0:
          salp12 = Geodesic.tiny_ * calp1
          calp12 = -1
        alp12 = math.atan2(salp12, calp12)
      S12 += self._c2 * alp12
      S12 *= swapp * lonsign * latsign
      # Convert -0 to 0
      S12 += 0

    # Convert calp, salp to azimuth accounting for lonsign, swapp, latsign.
    if swapp < 0:
      salp2, salp1 = salp1, salp2
      calp2, calp1 = calp1, calp2
      if outmask & Geodesic.GEODESICSCALE:
        M21, M12 = M12, M21

    salp1 *= swapp * lonsign; calp1 *= swapp * latsign
    salp2 *= swapp * lonsign; calp2 *= swapp * latsign

    if outmask & Geodesic.AZIMUTH:
      # minus signs give range [-180, 180). 0- converts -0 to +0.
      azi1 = 0 - math.atan2(-salp1, calp1) / Math.degree
      azi2 = 0 - math.atan2(-salp2, calp2) / Math.degree

    # Returned value in [0, 180]
    return a12, s12, azi1, azi2, m12, M12, M21, S12

  def CheckPosition(lat, lon):
    if not (abs(lat) <= 90):
      raise ValueError("latitude " + str(lat) + " not in [-90, 90]")
    if lon > 360.: lon = lon - 360.
    if lon < -180: lon = lon + 360.
    if not (lon >= -180 and lon <= 360):
      raise ValueError("longitude " + str(lon) + " not in [-180, 360]")
    return Geodesic.AngNormalize(lon)
  CheckPosition = staticmethod(CheckPosition)

  def CheckAzimuth(azi):
    if azi > 360.: azi = azi - 360.
    if azi < -180: azi = azi + 360.
    if not (azi >= -180 and azi <= 360):
      raise ValueError("azimuth " + str(azi) + " not in [-180, 360]")
    return Geodesic.AngNormalize(azi)
  CheckAzimuth = staticmethod(CheckAzimuth)

  def CheckDistance(s):
    if not (Math.isfinite(s)):
      raise ValueError("distance " + str(s) + " not a finite number")
  CheckDistance = staticmethod(CheckDistance)

  def Inverse(self, lat1, lon1, lat2, lon2, outmask = DISTANCE | AZIMUTH):
    """
    Solve the inverse geodesic problem.  Compute geodesic between
    (lat1, lon1) and (lat2, lon2).  Return a dictionary with (some) of
    the following entries:

      lat1 latitude of point 1
      lon1 longitude of point 1
      azi1 azimuth of line at point 1
      lat2 latitude of point 2
      lon2 longitude of point 2
      azi2 azimuth of line at point 2
      s12 distance from 1 to 2
      a12 arc length on auxiliary sphere from 1 to 2
      m12 reduced length of geodesic
      M12 geodesic scale 2 relative to 1
      M21 geodesic scale 1 relative to 2
      S12 area between geodesic and equator

    outmask determines which fields get included and if outmask is
    omitted, then only the basic geodesic fields are computed.  The mask
    is an or'ed combination of the following values

      Geodesic.LATITUDE
      Geodesic.LONGITUDE
      Geodesic.AZIMUTH
      Geodesic.DISTANCE
      Geodesic.REDUCEDLENGTH
      Geodesic.GEODESICSCALE
      Geodesic.AREA
      Geodesic.ALL
    """

    lon1 = Geodesic.CheckPosition(lat1, lon1)
    lon2 = Geodesic.CheckPosition(lat2, lon2)

    result = {'lat1': lat1, 'lon1': lon1, 'lat2': lat2, 'lon2': lon2}
    a12, s12, azi1, azi2, m12, M12, M21, S12 = self.GenInverse(
      lat1, lon1, lat2, lon2, outmask)
    outmask &= Geodesic.OUT_ALL
    result['a12'] = a12
    if outmask & Geodesic.DISTANCE: result['s12'] = s12
    if outmask & Geodesic.AZIMUTH:
      result['azi1'] = azi1; result['azi2'] = azi2
    if outmask & Geodesic.REDUCEDLENGTH: result['m12'] = m12
    if outmask & Geodesic.GEODESICSCALE:
      result['M12'] = M12; result['M21'] = M21
    if outmask & Geodesic.AREA: result['S12'] = S12
    return result

  # return a12, lat2, lon2, azi2, s12, m12, M12, M21, S12
  def GenDirect(self, lat1, lon1, azi1, arcmode, s12_a12, outmask):
    from geodesicline import GeodesicLine
    line = GeodesicLine(
      self, lat1, lon1, azi1,
      # Automatically supply DISTANCE_IN if necessary
      outmask | ( Geodesic.NONE if arcmode else Geodesic.DISTANCE_IN))
    return line.GenPosition(arcmode, s12_a12, outmask)

  def Direct(self, lat1, lon1, azi1, s12,
             outmask = LATITUDE | LONGITUDE | AZIMUTH):
    """
    Solve the direct geodesic problem.  Compute geodesic starting at
    (lat1, lon1) with azimuth azi1 and length s12.  Return a dictionary
    with (some) of the following entries:

      lat1 latitude of point 1
      lon1 longitude of point 1
      azi1 azimuth of line at point 1
      lat2 latitude of point 2
      lon2 longitude of point 2
      azi2 azimuth of line at point 2
      s12 distance from 1 to 2
      a12 arc length on auxiliary sphere from 1 to 2
      m12 reduced length of geodesic
      M12 geodesic scale 2 relative to 1
      M21 geodesic scale 1 relative to 2
      S12 area between geodesic and equator

    outmask determines which fields get included and if outmask is
    omitted, then only the basic geodesic fields are computed.  The mask
    is an or'ed combination of the following values

      Geodesic.LATITUDE
      Geodesic.LONGITUDE
      Geodesic.AZIMUTH
      Geodesic.DISTANCE
      Geodesic.REDUCEDLENGTH
      Geodesic.GEODESICSCALE
      Geodesic.AREA
      Geodesic.ALL
    """

    lon1 = Geodesic.CheckPosition(lat1, lon1)
    azi1 = Geodesic.CheckAzimuth(azi1)
    Geodesic.CheckDistance(s12)

    result = {'lat1': lat1, 'lon1': lon1, 'azi1': azi1, 's12': s12}
    a12, lat2, lon2, azi2, s12, m12, M12, M21, S12 = self.GenDirect(
      lat1, lon1, azi1, False, s12, outmask)
    outmask &= Geodesic.OUT_ALL
    result['a12'] = a12
    if outmask & Geodesic.LATITUDE: result['lat2'] = lat2
    if outmask & Geodesic.LONGITUDE: result['lon2'] = lon2
    if outmask & Geodesic.AZIMUTH: result['azi2'] = azi2
    if outmask & Geodesic.REDUCEDLENGTH: result['m12'] = m12
    if outmask & Geodesic.GEODESICSCALE:
      result['M12'] = M12; result['M21'] = M21
    if outmask & Geodesic.AREA: result['S12'] = S12
    return result

  def Line(self, lat1, lon1, azi1, caps = ALL):
    """
    Return a GeodesicLine object to compute points along a geodesic
    starting at lat1, lon1, with azimuth azi1.  caps is an or'ed
    combination of bit the following values indicating the capabilities
    of the return object

      Geodesic.LATITUDE
      Geodesic.LONGITUDE
      Geodesic.AZIMUTH
      Geodesic.DISTANCE
      Geodesic.REDUCEDLENGTH
      Geodesic.GEODESICSCALE
      Geodesic.AREA
      Geodesic.DISTANCE_IN
      Geodesic.ALL
    """

    from geodesicline import GeodesicLine
    lon1 = Geodesic.CheckPosition(lat1, lon1)
    azi1 = Geodesic.CheckAzimuth(azi1)
    return GeodesicLine(
      self, lat1, lon1, azi1,
      # Automatically supply DISTANCE_IN
      caps | Geodesic.DISTANCE_IN)

  def Area(self, points, polyline = False):
    """
    Compute the area of a geodesic polygon given by points, an array of
    dictionaries with entries lat and lon.  Return a dictionary with
    entries

      number the number of verices
      perimeter the perimeter
      area the area (counter-clockwise traversal positive)

    There is no need to "close" the polygon.  If polyline is set to
    True, then the points define a polyline instead of a polygon, the
    length is returned as the perimeter, and the area is not returned.
    """

    from polygonarea import PolygonArea
    for p in points:
      Geodesic.CheckPosition(p['lat'], p['lon'])
    num, perimeter, area = PolygonArea.Area(self, points, polyline)
    result = {'number': num, 'perimeter': perimeter}
    if not polyline: result['area'] = area
    return result

Geodesic.WGS84 = Geodesic(Constants.WGS84_a, Constants.WGS84_f)
