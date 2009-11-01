# include "projects.h"
# include "geodesic.h"
# define DTOL	1e-12

int
geod_inv(GEODESIC_T *GEODESIC)
{
	double	th1,th2,thm,dthm,dlamm,dlam,sindlamm,costhm,sinthm,cosdthm,
		sindthm,L,E,cosd,d,X,Y,T,sind,tandlammp,u,v,D,A,B;

	if (GEODESIC->ELLIPSE) {
		th1 = atan(GEODESIC->ONEF * tan(GEODESIC->p1.u));
		th2 = atan(GEODESIC->ONEF * tan(GEODESIC->p2.u));
	} else {
		th1 = GEODESIC->p1.u;
		th2 = GEODESIC->p2.u;
	}
	thm = .5 * (th1 + th2);
	dthm = .5 * (th2 - th1);
	dlamm = .5 * ( dlam = adjlon(GEODESIC->p2.v - GEODESIC->p1.v) );
	if (fabs(dlam) < DTOL && fabs(dthm) < DTOL) {
		GEODESIC->ALPHA12 =  GEODESIC->ALPHA21 = GEODESIC->DIST = 0.;
		return -1;
	}
	sindlamm = sin(dlamm);
	costhm = cos(thm);	sinthm = sin(thm);
	cosdthm = cos(dthm);	sindthm = sin(dthm);
	L = sindthm * sindthm + (cosdthm * cosdthm - sinthm * sinthm)
		* sindlamm * sindlamm;
	d = acos(cosd = 1 - L - L);
	if (GEODESIC->ELLIPSE) {
		E = cosd + cosd;
		sind = sin( d );
		Y = sinthm * cosdthm;
		Y *= (Y + Y) / (1. - L);
		T = sindthm * costhm;
		T *= (T + T) / L;
		X = Y + T;
		Y -= T;
		T = d / sind;
		D = 4. * T * T;
		A = D * E;
		B = D + D;
		GEODESIC->DIST = GEODESIC->A * sind * (T - GEODESIC->FLAT4 * (T * X - Y) +
                                           GEODESIC->FLAT64 * (X * (A + (T - .5 * (A - E)) * X) -
                                                               Y * (B + E * Y) + D * X * Y));
		tandlammp = tan(.5 * (dlam - .25 * (Y + Y - E * (4. - X)) *
                          (GEODESIC->FLAT2 * T + GEODESIC->FLAT64 * (32. * T - (20. * T - A)
                                                                     * X - (B + 4.) * Y)) * tan(dlam)));
	} else {
		GEODESIC->DIST = GEODESIC->A * d;
		tandlammp = tan(dlamm);
	}
	u = atan2(sindthm , (tandlammp * costhm));
	v = atan2(cosdthm , (tandlammp * sinthm));
	GEODESIC->ALPHA12 = adjlon(TWOPI + v - u);
	GEODESIC->ALPHA21 = adjlon(TWOPI - v - u);
  return 0;
}
