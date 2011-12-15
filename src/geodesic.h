#ifndef __GEODESIC_H__
#define __GEODESIC_H__
#endif

#include "projects.h"

#ifndef lint
static char GEODESIC_H_ID[] = "@(#)geodesic.h	4.3	95/08/19	GIE	REL";
#endif

#ifdef __cplusplus
extern "C" {
#endif

#ifndef _IN_GEOD_SET
#  define GEOD_EXTERN extern
#else
#  define GEOD_EXTERN
#endif

typedef struct geodesic {
	double	A;
 
   projUV p1, p2;
 
   double	ALPHA12;
 	double	ALPHA21;
   
	double	DIST;
	double	ONEF, FLAT, FLAT2, FLAT4, FLAT64;
	int	ELLIPSE;
   double FR_METER, TO_METER, del_alpha;
   int n_alpha, n_S;
 
 
   double th1,costh1,sinth1,sina12,cosa12,M,N,c1,c2,D,P,s1;
   int merid, signS;
 } GEODESIC_T;

  GEODESIC_T *GEOD_init(int, char **, GEODESIC_T *g);
  GEODESIC_T *GEOD_init_plus(const char *args, GEODESIC_T *g);
  void geod_for(GEODESIC_T *g);
  void  geod_pre(GEODESIC_T *g);
  int geod_inv(GEODESIC_T *g);

#ifdef __cplusplus
}
#endif
