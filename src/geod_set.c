
#define _IN_GEOD_SET

#include <stdlib.h>
#include <string.h>
#include "projects.h"
#include "geodesic.h"
#include "emess.h"

GEODESIC_T *
GEOD_init(int argc, char **argv, GEODESIC_T *GEODESIC)
{
  paralist *start = 0, *curr = 0;
	double es;
	char *name;
	int i;


    if(0 == GEODESIC)
    {
       GEODESIC = malloc(sizeof(GEODESIC_T));
    }
    memset(GEODESIC, 0, sizeof(GEODESIC_T));

    /* put arguments into internal linked list */
	if (argc <= 0)
		emess(1, "no arguments in initialization list");
	for (i = 0; i < argc; ++i)
		if (i)
			curr = curr->next = pj_mkparam(argv[i]);
		else
			start = curr = pj_mkparam(argv[i]);
	/* set elliptical parameters */
	if (pj_ell_set(start, &GEODESIC->A, &es)) emess(1,"ellipse setup failure");
	/* set units */
	if ((name = pj_param(start, "sunits").s)) {
		char *s;
                struct PJ_UNITS *unit_list = pj_get_units_ref();
		for (i = 0; (s = unit_list[i].id) && strcmp(name, s) ; ++i) ;
		if (!s)
			emess(1,"%s unknown unit conversion id", name);
		GEODESIC->FR_METER = 1. / (GEODESIC->TO_METER = atof(unit_list[i].to_meter));
	} else
		GEODESIC->TO_METER = GEODESIC->FR_METER = 1.;
	if ((GEODESIC->ELLIPSE = (es != 0.))) {
		GEODESIC->ONEF = sqrt(1. - es);
		GEODESIC->FLAT = 1 - GEODESIC->ONEF;
		GEODESIC->FLAT2 = GEODESIC->FLAT/2;
		GEODESIC->FLAT4 = GEODESIC->FLAT/4;
		GEODESIC->FLAT64 = GEODESIC->FLAT*GEODESIC->FLAT/64;
	} else {
		GEODESIC->ONEF = 1.;
		GEODESIC->FLAT = GEODESIC->FLAT2 = GEODESIC->FLAT4 = GEODESIC->FLAT64 = 0.;
	}
	/* check if line or arc mode */
	if (pj_param(start, "tlat_1").i) {
		double del_S;
#undef f

    GEODESIC->p1.u = pj_param(start, "rlat_1").f;
		GEODESIC->p1.v = pj_param(start, "rlon_1").f;
		if (pj_param(start, "tlat_2").i) {
			GEODESIC->p2.u = pj_param(start, "rlat_2").f;
			GEODESIC->p2.v = pj_param(start, "rlon_2").f;
			geod_inv(GEODESIC);
			geod_pre(GEODESIC);
		} else if ((GEODESIC->DIST = pj_param(start, "dS").f)) {
			GEODESIC->ALPHA12 = pj_param(start, "rA").f;
			geod_pre(GEODESIC);
			geod_for(GEODESIC);
		} else emess(1,"incomplete geodesic/arc info");
		if ((GEODESIC->n_alpha = pj_param(start, "in_A").i) > 0) {
			if (!(GEODESIC->del_alpha = pj_param(start, "rdel_A").f))
				emess(1,"del azimuth == 0");
		} else if ((del_S = fabs(pj_param(start, "ddel_S").f))) {
			GEODESIC->n_S = GEODESIC->DIST / del_S + .5;
		} else if ((GEODESIC->n_S = pj_param(start, "in_S").i) <= 0)
			emess(1,"no interval divisor selected");
	}
	/* free up linked list */
	for ( ; start; start = curr) {
		curr = start->next;
		pj_dalloc(start);
	}
  return GEODESIC;
}

GEODESIC_T *GEOD_init_plus(const char *definition, GEODESIC_T *geod)
{
#define MAX_ARG 200
  char	*argv[MAX_ARG];
  char	*defn_copy;
  int		argc = 0, i;
  GEODESIC_T *ret_geod;
  
    /* make a copy that we can manipulate */
  defn_copy = strdup(definition);
  
    /* split into arguments based on '+' and trim white space */
  
  for( i = 0; defn_copy[i] != '\0'; i++ )
  {
    switch( defn_copy[i] )
    {
      case '+':
        if( i == 0 || defn_copy[i-1] == '\0' )
        {
          if( argc+1 == MAX_ARG )
          {
              //pj_errno = -44;
            return NULL;
          }
          
          argv[argc++] = defn_copy + i + 1;
        }
        break;
        
      case ' ':
      case '\t':
      case '\n':
        defn_copy[i] = '\0';
        break;
        
      default:
        /* do nothing */;
    }
  }
  
    /* perform actual initialization */
  ret_geod = GEOD_init(argc, argv, geod);
  
  free( defn_copy );
  return ret_geod;
}

