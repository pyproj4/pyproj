# include "projects.h"
# include "geodesic.h"
# define MERI_TOL 1e-9


// input: al12, ELLIPSE, ONEF, phi1, FLAT, FLAT4
// output: al12 (ajusting) and!!! double s1, D, P, c1, M, N, cosa12, sina12, sinth1, costh1, th1, int signS, merid

void
geod_pre(GEODESIC_T *GEODESIC) {
	GEODESIC->ALPHA12 = adjlon(GEODESIC->ALPHA12); /* reduce to  +- 0-PI */
	GEODESIC->signS = fabs(GEODESIC->ALPHA12) > HALFPI ? 1 : 0;
	GEODESIC->th1 = GEODESIC->ELLIPSE ? atan(GEODESIC->ONEF * tan(GEODESIC->p1.u)) : GEODESIC->p1.u;
	GEODESIC->costh1 = cos(GEODESIC->th1);
	GEODESIC->sinth1 = sin(GEODESIC->th1);
	if ((GEODESIC->merid = fabs(GEODESIC->sina12 = sin(GEODESIC->ALPHA12)) < MERI_TOL)) {
		GEODESIC->sina12 = 0.;
		GEODESIC->cosa12 = fabs(GEODESIC->ALPHA12) < HALFPI ? 1. : -1.;
		GEODESIC->M = 0.;
	} else {
		GEODESIC->cosa12 = cos(GEODESIC->ALPHA12);
		GEODESIC->M = GEODESIC->costh1 * GEODESIC->sina12;
	}
	GEODESIC->N = GEODESIC->costh1 * GEODESIC->cosa12;
	if (GEODESIC->ELLIPSE) {
		if (GEODESIC->merid) {
			GEODESIC->c1 = 0.;
			GEODESIC->c2 = GEODESIC->FLAT4;
			GEODESIC->D = 1. - GEODESIC->c2;
			GEODESIC->D *= GEODESIC->D;
			GEODESIC->P = GEODESIC->c2 / GEODESIC->D;
		} else {
			GEODESIC->c1 = GEODESIC->FLAT * GEODESIC->M;
			GEODESIC->c2 = GEODESIC->FLAT4 * (1. - GEODESIC->M * GEODESIC->M);
			GEODESIC->D = (1. - GEODESIC->c2)*(1. - GEODESIC->c2 - GEODESIC->c1 * GEODESIC->M);
			GEODESIC->P = (1. + .5 * GEODESIC->c1 * GEODESIC->M) * GEODESIC->c2 / GEODESIC->D;
		}
	}
	if (GEODESIC->merid) GEODESIC->s1 = HALFPI - GEODESIC->th1;
	else {
		GEODESIC->s1 = (fabs(GEODESIC->M) >= 1.) ? 0. : acos(GEODESIC->M);
		GEODESIC->s1 =  GEODESIC->sinth1 / sin(GEODESIC->s1);
		GEODESIC->s1 = (fabs(GEODESIC->s1) >= 1.) ? 0. : acos(GEODESIC->s1);
	}
}

// input: ELLIPSE, DIST, A and!!! D, signS, s1
// output:

void
geod_for(GEODESIC_T *GEODESIC) {
	double d,sind,u,V,X,ds,cosds,sinds,ss = 0,de;

	if (GEODESIC->ELLIPSE) {
		d = GEODESIC->DIST / (GEODESIC->D * GEODESIC->A);
		if (GEODESIC->signS) d = -d;
		u = 2. * (GEODESIC->s1 - d);
		V = cos(u + d);
		X = GEODESIC->c2 * GEODESIC->c2 * (sind = sin(d)) * cos(d) * (2. * V * V - 1.);
		ds = d + X - 2. * GEODESIC->P * V * (1. - 2. * GEODESIC->P * cos(u)) * sind;
		ss = GEODESIC->s1 + GEODESIC->s1 - ds;
	} else {
		ds = GEODESIC->DIST / GEODESIC->A;
		if (GEODESIC->signS) ds = - ds;
	}
	cosds = cos(ds);
	sinds = sin(ds);
	if (GEODESIC->signS) sinds = - sinds;
	GEODESIC->ALPHA21 = GEODESIC->N * cosds - GEODESIC->sinth1 * sinds;
	if (GEODESIC->merid) {
		GEODESIC->p2.u = atan( tan(HALFPI + GEODESIC->s1 - ds) / GEODESIC->ONEF);
		if (GEODESIC->ALPHA21 > 0.) {
			GEODESIC->ALPHA21 = PI;
			if (GEODESIC->signS)
				de = PI;
			else {
				GEODESIC->p2.u = - GEODESIC->p2.u;
				de = 0.;
			}
		} else {
			GEODESIC->ALPHA21 = 0.;
			if (GEODESIC->signS) {
				GEODESIC->p2.u = - GEODESIC->p2.u;
				de = 0;
			} else
				de = PI;
		}
	} else {
		GEODESIC->ALPHA21 = atan(GEODESIC->M / GEODESIC->ALPHA21);
		if (GEODESIC->ALPHA21 > 0)
			GEODESIC->ALPHA21 += PI;
		if (GEODESIC->ALPHA12 < 0.)
			GEODESIC->ALPHA21 -= PI;
		GEODESIC->ALPHA21 = adjlon(GEODESIC->ALPHA21);
		GEODESIC->p2.u = atan(-(GEODESIC->sinth1 * cosds + GEODESIC->N * sinds) * sin(GEODESIC->ALPHA21) /
			(GEODESIC->ELLIPSE ? GEODESIC->ONEF * GEODESIC->M : GEODESIC->M));
		de = atan2(sinds * GEODESIC->sina12 ,
			(GEODESIC->costh1 * cosds - GEODESIC->sinth1 * sinds * GEODESIC->cosa12));
		if (GEODESIC->ELLIPSE)
    {
			if (GEODESIC->signS)
				de += GEODESIC->c1 * ((1. - GEODESIC->c2) * ds +
					GEODESIC->c2 * sinds * cos(ss));
			else
				de -= GEODESIC->c1 * ((1. - GEODESIC->c2) * ds -
					GEODESIC->c2 * sinds * cos(ss));
    }
	}
	GEODESIC->p2.v = adjlon( GEODESIC->p1.v + de );
}
