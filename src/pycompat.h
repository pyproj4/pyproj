#include "Python.h"

/* Suggested by M. v. Loewis: http://mail.python.org/pipermail/python-dev/2006-March/062561.html */

#if (PY_VERSION_HEX < 0x02050000)
typedef int Py_ssize_t;
#endif
