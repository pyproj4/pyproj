#include "proj.h"

#if PROJ_VERSION_MAJOR < 9 && PROJ_VERSION_MINOR < 1
    PJ* proj_trans_get_last_used_operation(PJ *P) {
        return nullptr;
    }
#endif
