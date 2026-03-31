cdef str cstrdecode(const char *instring)
cpdef bytes cstrencode(str pystr)

### {{if IS_CPYTHON}}
from cpython cimport array
cdef array.array empty_array(int npts)
### {{else}}
# https://github.com/pyproj4/pyproj/issues/854
cdef empty_array(int npts)
### {{endif}}
