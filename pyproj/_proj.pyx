include "base.pxi"

import warnings

cimport cython

from pyproj._datadir cimport pyproj_context_initialize
from pyproj.compat import cstrencode, pystrdecode
from pyproj.exceptions import ProjError

# # version number string for PROJ
proj_version_str = "{0}.{1}.{2}".format(
    PROJ_VERSION_MAJOR,
    PROJ_VERSION_MINOR,
    PROJ_VERSION_PATCH
)

cdef class Proj:
    def __cinit__(self):
        self.projobj = NULL
        self.context = NULL

    def __init__(self, const char *projstring):
        self.context = proj_context_create()
        pyproj_context_initialize(self.context, False)
        self.srs = pystrdecode(projstring)
        # initialize projection
        self.projobj = proj_create(self.context, projstring)
        if self.projobj is NULL:
            raise ProjError("Invalid projection {}.".format(projstring))
        self.projobj_info = proj_pj_info(self.projobj)
        ProjError.clear()

    def __dealloc__(self):
        """destroy projection definition"""
        if self.projobj is not NULL:
            proj_destroy(self.projobj)
        if self.context != NULL:
            proj_context_destroy(self.context)

    @property
    def definition(self):
        return self.projobj_info.definition

    @property
    def has_inverse(self):
        """Returns true if this projection has an inverse"""
        return self.projobj_info.has_inverse == 1

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def _fwd(self, object lons, object lats, bint errcheck=False):
        """
        forward transformation - lons,lats to x,y (done in place).
        if errcheck=True, an exception is raised if the forward transformation is invalid.
        if errcheck=False and the forward transformation is invalid, no exception is
        raised and 'inf' is returned.
        """
        cdef PyBuffWriteManager lonbuff = PyBuffWriteManager(lons)
        cdef PyBuffWriteManager latbuff = PyBuffWriteManager(lats)

        # process data in buffer
        if lonbuff.len != latbuff.len:
            raise ProjError("Buffer lengths not the same")

        cdef PJ_COORD projxyout
        cdef PJ_COORD projlonlatin = proj_coord(0, 0, 0, HUGE_VAL)
        cdef Py_ssize_t iii
        cdef int errno

        with nogil:
            proj_errno_reset(self.projobj)
            for iii in range(latbuff.len):
                # if inputs are nan's, return big number.
                if lonbuff.data[iii] != lonbuff.data[iii] or latbuff.data[iii] != latbuff.data[iii]:
                    lonbuff.data[iii] = HUGE_VAL
                    latbuff.data[iii] = HUGE_VAL
                    if errcheck:
                        with gil:
                            raise ProjError("projection_undefined")
                    continue
                if proj_angular_input(self.projobj, PJ_FWD):
                    projlonlatin.uv.u = _DG2RAD * lonbuff.data[iii]
                    projlonlatin.uv.v = _DG2RAD * latbuff.data[iii]
                else:
                    projlonlatin.uv.u = lonbuff.data[iii]
                    projlonlatin.uv.v = latbuff.data[iii]
                projxyout = proj_trans(self.projobj, PJ_FWD, projlonlatin)
                errno = proj_errno(self.projobj)
                if errcheck and errno:
                    raise ProjError("proj error: {}".format(
                        pystrdecode(proj_errno_string(errno))))
                elif errcheck:
                    with gil:
                        if ProjError.internal_proj_error is not None:
                            raise ProjError("proj error")
                # since HUGE_VAL can be 'inf',
                # change it to a real (but very large) number.
                # also check for NaNs.
                if projxyout.xy.x == HUGE_VAL or\
                        projxyout.xy.x != projxyout.xy.x or\
                        projxyout.xy.y == HUGE_VAL or\
                        projxyout.xy.x != projxyout.xy.x:
                    if errcheck:
                        with gil:
                            raise ProjError("Projection undefined.")
                    lonbuff.data[iii] = HUGE_VAL
                    latbuff.data[iii] = HUGE_VAL
                elif proj_angular_output(self.projobj, PJ_FWD):
                    lonbuff.data[iii] = _RAD2DG * projxyout.xy.x
                    latbuff.data[iii] = _RAD2DG * projxyout.xy.y
                else:
                    lonbuff.data[iii] = projxyout.xy.x
                    latbuff.data[iii] = projxyout.xy.y
        ProjError.clear()


    @cython.boundscheck(False)
    @cython.wraparound(False)
    def _inv(self, object xx, object yy, bint errcheck=False):
        """
        inverse transformation - x,y to lons,lats (done in place).
        if errcheck=True, an exception is raised if the inverse transformation is invalid.
        if errcheck=False and the inverse transformation is invalid, no exception is
        raised and 'inf' is returned.
        """
        if not self.has_inverse:
            raise ProjError('inverse projection undefined')

        cdef PyBuffWriteManager xbuff = PyBuffWriteManager(xx)
        cdef PyBuffWriteManager ybuff = PyBuffWriteManager(yy)

        # process data in buffer
        if xbuff.len != ybuff.len:
            raise ProjError("Array lengths not the same.")

        cdef PJ_COORD projxyin = proj_coord(0, 0, 0, HUGE_VAL)
        cdef PJ_COORD projlonlatout
        cdef Py_ssize_t iii
        cdef int errno

        with nogil:
            # reset errors potentially left over
            proj_errno_reset(self.projobj)
            for iii in range(xbuff.len):
                # if inputs are nan's, return big number.
                if xbuff.data[iii] != xbuff.data[iii] or ybuff.data[iii] != ybuff.data[iii]:
                    xbuff.data[iii] = HUGE_VAL
                    ybuff.data[iii] = HUGE_VAL
                    if errcheck:
                        with gil:
                            raise ProjError("projection_undefined")
                    continue
                if proj_angular_input(self.projobj, PJ_INV):
                    projxyin.xy.x = _DG2RAD * xbuff.data[iii]
                    projxyin.xy.y = _DG2RAD * ybuff.data[iii]
                else:
                    projxyin.xy.x = xbuff.data[iii]
                    projxyin.xy.y = ybuff.data[iii]
                projlonlatout = proj_trans(self.projobj, PJ_INV, projxyin)
                errno = proj_errno(self.projobj)
                if errcheck and errno:
                    with gil:
                        raise ProjError("proj error: {}".format(
                            pystrdecode(proj_errno_string(errno))))
                elif errcheck:
                    with gil:
                        if ProjError.internal_proj_error is not None:
                            raise ProjError("proj error")
                # since HUGE_VAL can be 'inf',
                # change it to a real (but very large) number.
                # also check for NaNs.
                if projlonlatout.uv.u == HUGE_VAL or \
                        projlonlatout.uv.u != projlonlatout.uv.u or \
                        projlonlatout.uv.v == HUGE_VAL or \
                        projlonlatout.uv.v != projlonlatout.uv.v:
                    if errcheck:
                        with gil:
                            raise ProjError("projection_undefined")
                    xbuff.data[iii] = HUGE_VAL
                    ybuff.data[iii] = HUGE_VAL
                elif proj_angular_output(self.projobj, PJ_INV):
                    xbuff.data[iii] = _RAD2DG * projlonlatout.uv.u
                    ybuff.data[iii] = _RAD2DG * projlonlatout.uv.v
                else:
                    xbuff.data[iii] = projlonlatout.uv.u
                    ybuff.data[iii] = projlonlatout.uv.v
        ProjError.clear()

    def __repr__(self):
        return "Proj('{srs}', preserve_units=True)".format(srs=self.srs)

    def _is_exact_same(self, Proj other):
        return proj_is_equivalent_to(
            self.projobj, other.projobj, PJ_COMP_STRICT) == 1

    def _is_equivalent(self, Proj other):
        return proj_is_equivalent_to(
            self.projobj, other.projobj, PJ_COMP_EQUIVALENT) == 1

    def is_exact_same(self, other):
        """Compares Proj objects to see if they are exactly the same."""
        if not isinstance(other, Proj):
            return False
        return self._is_exact_same(other)
