"""
Pyrex wrapper to provide python interfaces to 
PROJ.4 (http://proj.maptools.org) functions.

Performs cartographic transformations (converts from longitude,latitude
to native map projection x,y coordinates and vice versa, or from
one map projection coordinate system directly to another).

Example usage:

>>> from pyproj import Proj
>>> p = Proj(proj='utm',zone=10,ellps='WGS84')
>>> x,y = p(-120.108, 34.36116666)
>>> print 'x=%9.3f y=%11.3f' % (x,y)
x=765975.641 y=3805993.134
>>> print 'lon=%8.3f lat=%5.3f' % p(x,y,inverse=True)
lon=-120.108 lat=34.361

Input coordinates can be given as python arrays, lists/tuples, scalars
or numpy/Numeric/numarray arrays. Optimized for objects that support
the Python buffer protocol (regular python and numpy array objects).

Download: http://code.google.com/p/pyproj/downloads/list

Requirements: python 2.4 or higher.

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

from _pyproj import Proj as _Proj
from _pyproj import _transform
from _pyproj import __version__
from _pyproj import set_datapath
from array import array
from types import TupleType, ListType, NoneType
import os

pyproj_datadir = os.sep.join([os.path.dirname(__file__), 'data'])
set_datapath(pyproj_datadir)

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
 Works with numpy and regular python array objects, python sequences
 and scalars, but is fastest for array objects. lon and
 lat must be of same type (array, list/tuple or scalar) and have the
 same length (if array, list or tuple).
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

 Works with numpy and regular python array objects, python sequences
 and scalars, but is fastest for array objects. lon and
 lat must be of same type (array, list/tuple or scalar) and have the
 same length (if array, list or tuple).
        """
        # process inputs, making copies that support buffer API.
        inx, iny, inz, isfloat, islist, istuple = _copytobuffer(lon, lat)
        # call proj4 functions. inx and iny modified in place.
        if inverse:
            _Proj._inv(self, inx, iny, radians=radians, errcheck=errcheck)
        else:
            _Proj._fwd(self, inx, iny, radians=radians, errcheck=errcheck)
        # if inputs were lists, tuples or floats, convert back.
        return _convertback(isfloat,islist,istuple,inx,iny,inz=None)

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

 x,y and z can be numpy or regular python arrays,
 python lists/tuples or scalars. Arrays are fastest. x,y and z must be
 all of the same type (array, list/tuple or scalar), and have the 
 same length (if arrays, lists or tuples).
 For projections in geocentric coordinates, values of
 x and y are given in meters.  z is always meters.

 Example usage:

 >>> # projection 1: UTM zone 15, grs80 ellipse, NAD83 datum
 >>> # (defined by epsg code 26915)
 >>> p1 = Proj(init='epsg:26915')
 >>> # projection 2: UTM zone 15, clrk66 ellipse, NAD27 datum
 >>> p2 = Proj(init='epsg:26715')
 >>> # find x,y of Jefferson City, MO.
 >>> x1, y1 = p1(-92.199881,38.56694)
 >>> # transform this point to projection 2 coordinates.
 >>> x2, y2 = transform(p1,p2,x1,y1)
 >>> print '%9.3f %11.3f' % (x1,y1)
 569704.566 4269024.671
 >>> print '%9.3f %11.3f' % (x2,y2)
 569706.333 4268817.680
 >>> print '%8.3f %5.3f' % p2(x2,y2,inverse=True)
  -92.200 38.567
    """
    # process inputs, making copies that support buffer API.
    inx, iny, inz, isfloat, islist, istuple = _copytobuffer(x,y,z)
    # call pj_transform.  inx,iny,inz buffers modified in place.
    _transform(p1,p2,inx,iny,inz,radians)
    # if inputs were lists, tuples or floats, convert back.
    return _convertback(isfloat,islist,istuple,inx,iny,inz)

def _copytobuffer(x,y,z=None):
    """ 
 return copies of x,y (and z, if z is not None) as objects
 that support python Buffer API (python array if input is
 float, list or tuple, numpy array if input is a numpy array).
 returns copyofx, copyofy, copyofz, isfloat, islist, istuple
 (islist is True if inputs are lists, ituple is true if
  inputs are tuples, isfloat is true if inputs are floats).
 An exception is raised if all inputs (except z if z=None)
 are not of the same type.
    """
    # make sure x,y,z support Buffer API and contain doubles.
    isfloat = False; islist = False; istuple = False
    # first, if it's a numpy array scalar convert to float
    # (array scalars don't support buffer API)
    if hasattr(x,'shape') and x.shape == (): x = float(x)
    if hasattr(y,'shape') and y.shape == (): y = float(y)
    if hasattr(z,'shape') and z.shape == (): z = float(z)
    inz = None
    try:
        # typecast numpy arrays to double.
        # (this makes a copy - which is crucial
        #  since buffer is modified in place)
        x.dtype.char
        y.dtype.char
        if z is not None: z.dtype.char
        inx = x.astype('d')
        iny = y.astype('d')
        if z is not None:
            inz = z.astype('d')
    except:
        try: # perhaps they are Numeric/numarrays?
            x.typecode()
            y.typecode()
            if z is not None: z.typecode()
            inx = x.astype('d')
            iny = y.astype('d')
            if z is not None:
                inz = z.astype('d')
        except:
            # perhaps they are regular python arrays?
            try:
                x.typecode
                y.typecode
                if z is not None: z.typecode
                inx = array('d',x)
                iny = array('d',y)
                if z is not None:
                    inz = array('d',z)
            except: 
                # try to convert to python array
                # a list.
                if type(x) is ListType and type(y) is ListType and (type(z) is NoneType or type(z) is ListType):
                    inx = array('d',x)
                    iny = array('d',y)
                    if z is not None:
                        inz = array('d',z)
                    islist = True
                # a tuple.
                elif type(x) is TupleType and type(y) is TupleType and (type(z) is NoneType or type(z) is TupleType):
                    inx = array('d',x)
                    iny = array('d',y)
                    if z is not None:
                        inz = array('d',z)
                    istuple = True
                # a scalar?
                else:
                    try:
                        x = float(x)
                        y = float(y)
                        if z is not None: z = float(z)
                        inx = array('d',(x,))
                        iny = array('d',(y,))
                        if z is not None: inz = array('d',(z,))
                        isfloat = True
                    except:
                        print 'x is',type(x),'y is',type(y),'z is',type(z)
                        raise TypeError, 'inputs must be arrays, lists/tuples or scalars (and they must all be of the same type)'
    return inx,iny,inz,isfloat,islist,istuple

def _convertback(isfloat,islist,istuple,inx,iny,inz=None):
    # if inputs were lists, tuples or floats, convert back to original type.
    if inz is not None:
        if isfloat:
            return inx[0],iny[0],inz[0]
        elif islist:
            return inx.tolist(),iny.tolist(),inz.tolist()
        elif istuple:
            return tuple(inx),tuple(iny),tuple(inz)
        else:
            return inx,iny,inz
    else:
        if isfloat:
            return inx[0],iny[0]
        elif islist:
            return inx.tolist(),iny.tolist()
        elif istuple:
            return tuple(inx),tuple(iny)
        else:
            return inx,iny

def test():
    """run the examples in the docstrings using the doctest module"""
    import doctest, pyproj
    doctest.testmod(pyproj,verbose=True)

if __name__ == "__main__": test()
