"""
Pyrex wrapper to provide python interfaces to 
PROJ.4 (http://proj.maptools.org) functions.

Performs cartographic transformations (converts from longitude,latitude
to native map projection x,y coordinates and vice versa, or from
one map projection coordinate system directly to another).

Example usage:

>>> from pyproj_numpy import Proj
>>> p = Proj(proj='utm',zone=10,ellps='WGS84')
>>> x,y = p(-120.108, 34.36116666)
>>> print 'x=%9.3f y=%11.3f' % (x,y)
x=765975.641 y=3805993.134
>>> print 'lon=%8.3f lat=%5.3f' % p(x,y,inverse=True)
lon=-120.108 lat=34.361

Inputs may anything that can be converted to float64 numpy arrays.
Outputs are float64 numpy arrays.

Download: http://python.org/pypi/pyproj

Requirements: PROJ.4 library (http://proj.maptools.org).

Install:  Set the PROJ_DIR environment variable to point to the location 
          of your proj.4 installation, then run 'python setup.py install'.
          If you're using Windows with mingw, see README.mingw.

Example scripts are in 'test' subdirectory of source distribution.
The 'test()' function will run the examples in the docstrings.

Contact:  Jeffrey Whitaker <jeffrey.s.whitaker@noaa.gov

copyright (c) 2006 by Jeffrey Whitaker.

Permission to use, copy, modify, and distribute this software and its
documentation for any purpose and without fee is hereby granted,
provided that the above copyright notice appear in all copies and that
both the copyright notice and this permission notice appear in
supporting documentation.
THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE,
INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO
EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, INDIRECT OR
CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF
USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.
""" 

from _pyproj_numpy import Proj as _Proj
from _pyproj_numpy import _transform
from _pyproj_numpy import __version__
import numpy

class Proj(_Proj):
    """
 performs cartographic transformations (converts from longitude,latitude
 to native map projection x,y coordinates and vice versa) using proj 
 (http://proj.maptools.org/)

 A Proj class instance is initialized with 
 proj map projection control parameter key/value pairs.
 The key/value pairs can either be passed in a dictionary,
 or as keyword arguments.
 See http://www.remotesensing.org/geotiff/proj_list for
 examples of key/value pairs defining different map projections.

 Calling a Proj class instance with the arguments lon, lat will
 convert lon/lat (in degrees) to x/y native map projection 
 coordinates (in meters).  If optional keyword 'inverse' is
 True (default is False), the inverse transformation from x/y
 to lon/lat is performed. If optional keyword 'radians' is True
 (default is False) lon/lat are interpreted as radians instead
 of degrees. If optional keyword 'errcheck' is True (default is 
 False) an exception is raised if the transformation is invalid.
 If errcheck=False and the transformation is invalid, no execption
 is raised and the platform dependent value HUGE_VAL is returned.
 Inputs coordinates can be anything that can be converted to 
 a float64 numpy array using numpy.asarray, outputs are float64 numpy arrays.
 If inputs are arrays or sequences, they must have the same length.
    """

    def __new__(self, projparams=None, **kwargs):
        """
 initialize a Proj class instance.

 Proj4 projection control parameters must either be
 given in a dictionary 'projparams' or as keyword arguments.
 See the proj documentation (http://proj.maptools.org) for more
 information about specifying projection parameters.
        """
        # if projparams is None, use kwargs.
        if projparams is None:
            if len(kwargs) == 0:
                raise RuntimeError('no projection control parameters specified')
            else:
                projparams = kwargs
        # set units to meters.
        if not projparams.has_key('units'):
            projparams['units']='m'
        elif projparams['units'] != 'm':
            print 'resetting units to meters ...'
            projparams['units']='m'
        return _Proj.__new__(self, projparams)

    def __call__(self,lon,lat,inverse=False,radians=False,errcheck=False):
        """
 Calling a Proj class instance with the arguments lon, lat will
 convert lon/lat (in degrees) to x/y native map projection 
 coordinates (in meters).  If optional keyword 'inverse' is
 True (default is False), the inverse transformation from x/y
 to lon/lat is performed.  If optional keyword 'radians' is
 True (default is False) the units of lon/lat are radians instead
 of degrees. If optional keyword 'errcheck' is True (default is 
 False) an exception is raised if the transformation is invalid.
 If errcheck=False and the transformation is invalid, no execption
 is raised and the platform dependent value HUGE_VAL is returned.

 Inputs should be doubles (they will be cast to doubles
 if they are not, causing a slight performance hit).

 Inputs coordinates can be anything that can be converted to 
 a float64 numpy array using numpy.asarray, outputs are float64 numpy arrays.
 If inputs are arrays or sequences, they must have the same length.
        """
        lon = numpy.asarray(lon,dtype=numpy.float64)
        lat = numpy.asarray(lat,dtype=numpy.float64)
        # make sure sizes are the same.
        if lon.size != lat.size:
            raise ValueError,'inputs must have the same size'
        # make sure data is contiguous, if not make a copy.
        if not lon.flags['C_CONTIGUOUS']:
           lon = lon.copy()     
        if not lat.flags['C_CONTIGUOUS']:
           lat = lat.copy()     
        # call proj4 functions.
        if inverse:
            return _Proj._inv(self, lon, lat, radians=radians, errcheck=errcheck)
        else:
            return _Proj._fwd(self, lon, lat, radians=radians, errcheck=errcheck)
    def is_latlong(self):
        """returns True if projection in geographic (lon/lat) coordinates"""
        return _Proj.is_latlong(self)

    def is_geocent(self):
        """returns True if projection in geocentric (x/y) coordinates"""
        return _Proj.is_geocent(self)

def transform(p1, p2, x, y, z=None, radians=False):
    """
 x2, y2, z2 = transform(p1, p2, x1, y1, z1, radians=False)

 Transform points between two coordinate systems defined
 by the Proj instances p1 and p2.

 The points x1,y1,z1 in the coordinate system defined by p1
 are transformed to x2,y2,z2 in the coordinate system defined by p2.

 z1 is optional, if it is not set it is assumed to be zero (and 
 only x2 and y2 are returned).

 In addition to converting between cartographic and geographic
 projection coordinates, this function can take care of datum shifts
 (which cannot be done using the __call__ method of the Proj instances).
 It also allows for one of the coordinate systems to be geographic 
 (proj = 'latlong'). 

 If optional keyword 'radians' is True (default is False) and
 p1 is defined in geographic coordinate (pj.is_latlong() is True),
 x1,y1 is interpreted as radians instead of the default degrees.
 Similarly, if p2 is defined in geographic coordinates 
 and radians=True, x2, y2 are returned in radians instead of degrees.
 if p1.is_latlong() and p2.is_latlong() both are False, the
 radians keyword has no effect.

 Inputs coordinates can be anything that can be converted to 
 a float64 numpy array using numpy.asarray, outputs are float64 numpy arrays.
 If inputs are arrays or sequences, they must have the same length.

 For projections in geocentric coordinates, values of
 x and y are given in meters.  z is always meters.

 Example usage:

 >>> # projection 1: north polar stereographic
 >>> p1 = Proj(proj='stere',lat_0=90,lat_ts=90,lon_0=270)
 >>> # projection 2: lambert conformal conic, 2 standard parallels.
 >>> p2 = Proj(proj='lcc',lat_1=33,lat_2=45,lon_0=270,lat_0=30)
 >>> # find x,y of Boulder, CO in projection 1
 >>> x1, y1 = p1(-105,40)
 >>> # transform this point to projection 2 coordinates.
 >>> x2, y2 = transform(p1,p2,x1,y1)
 >>> print '%9.3f %11.3f' % (x1,y1)
 -1541018.485 -5751159.282
 >>> print '%9.3f %11.3f' % (x2,y2)
 -1268297.854 1212356.336
 >>> print '%8.3f %5.3f' % p2(x2,y2,inverse=True)
 -105.000 40.000
    """
    # make a copy that will be modified in place.
    outx = numpy.array(x,dtype=numpy.float64)
    outy = numpy.array(y,dtype=numpy.float64)
    if outx.size != outy.size:
        raise ValueError,'inputs must have the same size'
    if z is not None:
        outz = numpy.array(z,dtype=numpy.float64)
        if outx.size != outz.size:
            raise ValueError,'inputs must have the same size'
    else:
        outz = numpy.array(False,numpy.bool)
    # call pj_transform.
    _transform(p1,p2,outx,outy,outz,radians)
    if z is not None:
        return outx,outz,outz
    else:
        return outx,outy

def test():
    """run the examples out the docstrings using the doctest module"""
    import doctest, pyproj_numpy
    doctest.testmod(pyproj_numpy,verbose=True)

if __name__ == "__main__": test()
