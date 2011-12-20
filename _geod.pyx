import math

cdef double _dg2rad, _rad2dg 

_dg2rad = math.radians(1.)
_rad2dg = math.degrees(1.)
_doublesize = sizeof(double)

cdef extern from "Python.h":
    int PyObject_AsWriteBuffer(object, void **rbuf, Py_ssize_t *len)

cdef extern from "project.h":
    # Earth's elliptical constants.
    # Element  a units, typically meters, defines the units for
    # all other length elements.
    ctypedef struct PROJ_ELLIPS:
        double a # semi-major axis or sphere radius
        double f # ellpsoid flattening, if == 0 then sphere
        double es # eccentricity squared, if == 0 then sphere
        double one_es # 1-es 
    # 3D Geographic coordinate 
    ctypedef struct PROJ_PT_LPH:
        double lam # longitude in radians
        double phi # latitude in radians
        double h # height above the ellpsoid
    # Geodesic line structure
    # Azimuths in radians clockwise from North.  Distance units the
    # same as element a in structure ellps.
    ctypedef struct PROJ_LINE:
        PROJ_PT_LPH *pt1 # pointer to geographic coord of first location
        double az12 # azimuth from pt1 to pt2 (forward) 
        PROJ_PT_LPH *pt2 # pointer to geographic coord of second location
        double az21 #  azimuth from pt2 to pt1 (back)
        double S # geodetic distance between points
        PROJ_ELLIPS *E # pointer to ellpsoid constants
    void proj_sp_inv(PROJ_LINE * A)
    void proj_sp_fwd(PROJ_LINE * A)
    void proj_in_fwd(PROJ_LINE * A)
    void proj_in_inv(PROJ_LINE * A)

cdef class Geod:
    cdef PROJ_LINE arc
    cdef PROJ_ELLIPS ellps
    cdef PROJ_PT_LPH pt1, pt2

    def __cinit__(self, object a, object f, object es, object sphere):
        self.sphere = sphere
        self.ellps.a = a
        self.ellps.f = f
        self.ellps.es = es
        self.ellps.one_es = 1.-es
        self.arc.E = &self.ellps

    def __reduce__(self):
        """special method that allows pyproj.Geod instance to be pickled"""
        initstring = '+a=%s +f=%s +es=%s' % (self.a, self.f, self.es)
        return (self.__class__,(initstring,))

    def _fwd(self, lons, lats, az, dist, radians=False):
        cdef Py_ssize_t buflenlons, buflenlats, buflenaz, buflend, ndim, i
        cdef double *lonsdata, *latsdata, *azdata, *distdata
        cdef void *londata, *latdata, *azdat, *distdat
        cdef int err
        # if buffer api is supported, get pointer to data buffers.
        if PyObject_AsWriteBuffer(lons, &londata, &buflenlons) <> 0:
            raise RuntimeError
        if PyObject_AsWriteBuffer(lats, &latdata, &buflenlats) <> 0:
            raise RuntimeError
        if PyObject_AsWriteBuffer(az, &azdat, &buflenaz) <> 0:
            raise RuntimeError
        if PyObject_AsWriteBuffer(dist, &distdat, &buflend) <> 0:
            raise RuntimeError
        # process data in buffer
        if not buflenlons == buflenlats == buflenaz == buflend:
            raise RuntimeError("Buffer lengths not the same")
        ndim = buflenlons//_doublesize
        lonsdata = <double *>londata
        latsdata = <double *>latdata
        azdata = <double *>azdat
        distdata = <double *>distdat
        for i from 0 <= i < ndim:
            if radians:
                self.pt1.lam = lonsdata[i]
                self.pt1.phi = latsdata[i]
                self.pt1.h = 0.
                self.arc.pt1 = &self.pt1
                self.arc.az12 = azdata[i]
                self.arc.S = distdata[i]
            else:
                self.pt1.lam = _dg2rad*lonsdata[i]
                self.pt1.phi = _dg2rad*latsdata[i]
                self.pt1.h = 0.
                self.arc.pt1 = &self.pt1
                self.arc.az12 = _dg2rad*azdata[i]
                self.arc.S = distdata[i]
# Computes the location of the second point in the structure
# based on the first point's location and the distance and
# forward azumuth
            if self.sphere:
                proj_sp_fwd(&self.arc)
            else:
                proj_in_fwd(&self.arc)
            if radians:
                self.pt2.lam = self.arc.pt2.lam
                self.pt2.phi = self.arc.pt2.phi
                lonsdata[i] = self.pt2.lam
                latsdata[i] = self.pt2.phi
                azdata[i] = self.arc.az21
            else:
                self.pt2.lam = _rad2dg*self.arc.pt2.lam
                self.pt2.phi = _rad2dg*self.arc.pt2.phi
                lonsdata[i] = self.pt2.lam
                latsdata[i] = self.pt2.phi
                azdata[i] = _rad2dg*self.arc.az21

    def _inv(self, object lons1, object lats1, object lons2, object lats2, radians=False):
        """
 inverse transformation - return forward and back azimuths, plus distance
 between an initial and terminus lat/lon pair.
 if radians=True, lons/lats are radians instead of degrees.
        """
        cdef Py_ssize_t buflenlons, buflenlats, buflenaz, buflend, ndim, i
        cdef double *lonsdata, *latsdata, *azdata, *distdata
        cdef void *londata, *latdata, *azdat, *distdat
        cdef int err
        # if buffer api is supported, get pointer to data buffers.
        if PyObject_AsWriteBuffer(lons1, &londata, &buflenlons) <> 0:
            raise RuntimeError
        if PyObject_AsWriteBuffer(lats1, &latdata, &buflenlats) <> 0:
            raise RuntimeError
        if PyObject_AsWriteBuffer(lons2, &azdat, &buflenaz) <> 0:
            raise RuntimeError
        if PyObject_AsWriteBuffer(lats2, &distdat, &buflend) <> 0:
            raise RuntimeError
        # process data in buffer
        if not buflenlons == buflenlats == buflenaz == buflend:
            raise RuntimeError("Buffer lengths not the same")
        ndim = buflenlons//_doublesize
        lonsdata = <double *>londata
        latsdata = <double *>latdata
        azdata = <double *>azdat
        distdata = <double *>distdat
        errmsg = 'undefined inverse geodesic (may be an antipodal point)'
        for i from 0 <= i < ndim:
            if radians:
                self.pt1.lam = lonsdata[i]
                self.pt1.phi = latsdata[i]
                self.pt1.h = 0.
                self.pt2.lam = azdata[i]
                self.pt2.phi = distdata[i]
                self.arc.pt1 = &self.pt1
                self.arc.pt2 = &self.pt2
            else:
                self.pt1.lam = _dg2rad*lonsdata[i]
                self.pt1.phi = _dg2rad*latsdata[i]
                self.pt1.h = 0.
                self.pt2.lam = _dg2rad*azdata[i]
                self.pt2.phi = _dg2rad*distdata[i]
                self.arc.pt1 = &self.pt1
                self.arc.pt2 = &self.pt2
# Computes distance, forward and back azimuths in structure
# for the two end points of the geodesic line
            if self.sphere:
                proj_sp_inv(&self.arc)
            else:
                proj_in_inv(&self.arc)
            if radians:
                lonsdata[i] = self.arc.az12
                latsdata[i] = self.arc.az21
            else:
                lonsdata[i] = _rad2dg*self.arc.az12
                latsdata[i] = _rad2dg*self.arc.az21
            azdata[i] = self.arc.S

    def _npts(self, double lon1, double lat1, double lon2, double lat2, int npts, radians=False):
        """
 given initial and terminus lat/lon, find npts intermediate points."""
        cdef int i
        cdef double del_s
        if radians:
            self.pt1.lam = lon1
            self.pt1.phi = lat1
            self.pt1.h = 0.
            self.pt2.lam = lon2     
            self.pt2.phi = lat2       
            self.arc.pt1 = &self.pt1
            self.arc.pt2 = &self.pt2
        else:
            self.pt1.lam = _dg2rad*lon1
            self.pt1.phi = _dg2rad*lat1
            self.pt1.h = 0.
            self.pt2.lam = _dg2rad*lon2
            self.pt2.phi = _dg2rad*lat2
            self.arc.pt1 = &self.pt1
            self.arc.pt2 = &self.pt2
        if self.sphere:
            proj_sp_inv(&self.arc)
        else:
            proj_in_inv(&self.arc)
        # distance increment.
        del_s = self.arc.S/(npts+1)
        # initialize output tuples.
        lats = ()
        lons = ()
        # loop over intermediate points, compute lat/lons.
        for i from 1 <= i < npts+1:
            self.arc.S = i*del_s
            if self.sphere:
                proj_sp_fwd(&self.arc)
            else:
                proj_in_fwd(&self.arc)
            if radians:
                lats = lats + (self.pt2.phi,)
                lons = lons + (self.pt2.lam.v,)
            else:
                lats = lats + (_rad2dg*self.pt2.phi,)
                lons = lons + (_rad2dg*self.pt2.lam,)
        return lons, lats   
