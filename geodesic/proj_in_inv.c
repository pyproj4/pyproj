/*
** Copyright (c) 2009   Gerald I. Evenden
*/
static const char
 PROJ_ID[] = "$Id: proj_in_inv.c,v 5.2 2009/05/06 18:46:51 gie Exp gie $";
/*
** Permission is hereby granted, free of charge, to any person obtaining
** a copy of this software and associated documentation files (the
** "Software"), to deal in the Software without restriction, including
** without limitation the rights to use, copy, modify, merge, publish,
** distribute, sublicense, and/or sell copies of the Software, and to
** permit persons to whom the Software is furnished to do so, subject to
** the following conditions:
**
** The above copyright notice and this permission notice shall be
** included in all copies or substantial portions of the Software.
**
** THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
** EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
** MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
** IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
** CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
** TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
** SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/
/** @file proj_in_inv.c
 * @brief compute the forward geodesic for an ellipsoid
 */
#include <stdlib.h>
#include <math.h>
#include <project.h>
#define TOL0  5e-15
#define TOL1  5e-14
#define TOL2  .007
#define TT 5e-13
#define TTA 5e-15
/**
 * @brief Distance along meridian
 * @param[in] esq ellipsoid eccentricity squared
 * @param[in] phi1 first latitude
 * @param[in] phi2 second latitude
 * @return distance along meridian between phi1 and phi2
 */
static double merid_arc(double esq, double phi1, double phi2) {
    double a, b, c, d, e, f, e2, e4, e6, e8, s1, s2, t1, t2,
	t3, t4, t5, da, db, dc, dd, de, df, ex;
    int flag;
/* INPUT PARAMETERS: */
/* ----------------- */
/* ESQ          ECCENTRICITY SQUARED FOR REFERENCE ELLIPSOID */
/* P1           LAT STATION 1 */
/* P2           LAT STATION 2 */
/* return value */
/* ------------------ */
/* ARC          GEODETIC DISTANCE or unit ellipse  */
/*     CHECK FOR A 90 DEGREE LOOKUP */
    flag = 0;
    s1 = fabs(phi1);
    s2 = fabs(phi2);
    flag = (s1 <= TTA) && (fabs(s2 - M_PI_2) < TTA);
    da = phi2 - phi1;
    s1 = 0.;
    s2 = 0.;
/*     COMPUTE THE LENGTH OF A MERIDIONAL ARC BETWEEN TWO LATITUDES */
    e2 = esq;
    e4 = e2 * e2;
    e6 = e4 * e2;
    e8 = e6 * e2;
    ex = e8 * e2;
    t1 = e2 * .75;
    t2 = e4 * .234375;
    t3 = e6 * .068359375;
    t4 = e8 * .01922607421875;
    t5 = ex * .00528717041015625;
    a = t1 + 1. + t2 * 3. + t3 * 10. + t4 * 35. + t5 * 126.;
    if (!flag) {
	b = t1 + t2 * 4. + t3 * 15. + t4 * 56. + t5 * 210.;
	c = t2 + t3 * 6. + t4 * 28. + t5 * 120.;
	d = t3 + t4 * 8. + t5 * 45.;
	e = t4 + t5 * 10.;
	f = t5;
	db = sin(phi2 * 2.) - sin(phi1 * 2.);
	dc = sin(phi2 * 4.) - sin(phi1 * 4.);
	dd = sin(phi2 * 6.) - sin(phi1 * 6.);
	de = sin(phi2 * 8.) - sin(phi1 * 8.);
	df = sin(phi2 * 10.) - sin(phi1 * 10.);
	/*     COMPUTE THE S2 PART OF THE SERIES EXPANSION */
	s2 = -db * b / 2. + dc * c / 4. - dd * d / 6. +
	    de * e / 8. - df * f / 10.;
    }
/*     COMPUTE THE S1 PART OF THE SERIES EXPANSION */
    s1 = da * a;
/*     COMPUTE THE ARC LENGTH */
    return ((1. - esq) * (s1 + s2));
}

/**
 * @brief Determines internal factors
 * @param[in] flat ellipsoid flattening
 * @param[in] esq ellipsoid eccentricity squared
 * @param[in] dlam difference in longitude between points
 * @param[in] az12 azimuth from p1 to p2
 * @param[out] az21 azimuth from p2 to p1
 * @param[out] ao constant
 * @param[out] bo constant
 * @param[out] sms equitorial geodesic
 */
static void
func_loa(double flat, double esq, double dlam, double az12,
	 double *az21, double *ao, double *bo, double *sms) {
    /* Local variables */
    double s, c2, t1, t2, u2, t4, u4, t6, u6, t8, u8, cs, az, dlon, cons;
    int iter;
    double esqp;

/* INPUT PARAMETERS: */
/* ----------------- */
/* FLAT		 FLATTENING (0.0033528 ... ) */
/* ESQ		  ECCENTRICITY SQUARED FOR REFERENCE ELLIPSOID */
/* DLAM		 LON DIFFERENCE */
/* AZ12		 AZI AT STA 1 -> STA 2 */

/* OUTPUT PARAMETERS: */
/* ------------------ */
/* AZ21		 AZ2 AT STA 2 -> STA 1 */
/* AO		   CONST */
/* BO		   CONST */
/* SMS		  DISTANCE ... EQUATORIAL - GEODESIC  (S - s)   "SMS" */

    dlon = fabs(dlam);
    cons = (M_PI - dlon) / (M_PI * flat);
/*	 COMPUTE AN APPROXIMATE AZ */
    az = asin(cons);
    t1 = 1.;
    t2 = flat * -.25 * (flat + 1. + flat * flat);
    t4 = flat * .1875 * flat * (flat * 2.25 + 1.);
    t6 = flat * -.1953125 * flat * flat;
    iter = 0;
    do {
	s = cos(az);
	c2 = s * s;
	/*       COMPUTE NEW AO */
	*ao = t1 + c2 * (t2 + c2 * (t4 + c2 * t6));
	cs = cons / *ao;
	s = asin(cs);
	if (fabs(s - az) < TT)
	    break;
	az = s;
    } while (++iter <= 6);
    az12 = s;
    if (dlam < 0.)
	az12 = M_PI * 2. - az12;
    *az21 = M_PI * 2. - az12;
/*	 EQUATORIAL - GEODESIC  (S - s)   "SMS" */
    esqp = esq / (1. - esq);
    s = cos(az12);
    u2 = esqp * s * s;
    u4 = u2 * u2;
    u6 = u4 * u2;
    u8 = u6 * u2;
    t1 = 1.;
    t2 = u2 * .25;
    t4 = u4 * -.046875;
    t6 = u6 * .01953125;
    t8 = u8 * -.01068115234375;
    *bo = t1 + t2 + t4 + t6 + t8;
    s = sin(az12);
    *sms = M_PI * (1. - flat * fabs(s) * *ao - *bo * (1. - flat));
    return;
}

/**
 * @brief inverse geodesic computation for elliptical earth
 * @param A pointer to geodesic line structure
 */
void proj_in_inv(PROJ_LINE * A) {
    double b, w, z, a2, b2, a4, f0, f2, f3, f4, a6, b4, b6, r1, f, esq,
	r2, q2, u1, u2, t4, q4, t6, q6, r3, aa, ab, bb, ao, bo, qo, ss,
	xy, xz, cu1, cu2, su1, su2, arc, sig, equ, sms, csig, clon, dlon,
	ssig, epsq, slon, tana1, tana2, sina1, sina2;
    int kount;
    double sinalf, alimit;
/*     solution of the geodetic inverse problem after t. vincenty */
/*     modified rainsford's method with helmert's elliptical terms */
/*     effective in any azimuth and at any distance short of antipocal */
/*     from/to stations must not be the geographic pole. */
/*     parameter a is the semi-major axis of the reference ellipsoid */
/*     finv=1/f is the inverse flattening of the reference ellipsoid */
/*     latitudes and longitudes in radians positive north and west */
/*     forward and back azimuths returned in radians clockwise from south */
/*     geodesic distance s returned in units of semi-major axis a */
/*     programmed for ibm 360-195   09/23/75 */

/*     note - note - note - */
/*     1. do not use for meridional arcs and be careful on the equator. */
/*     2. azimuths are from north(+) clockwise and */
/*     3. longitudes are positive east(+) */

/* input parameters: */
/* ----------------- */
/* a            semi-major axis of reference ellipsoid      meters */
/* f            flattening (0.0033528...) */
/* esq          eccentricity squared */
/* p1           lat station 1                               radians */
/* e1           lon station 1                               radians */
/* p2           lat station 2                               radians */
/* e2           lon station 2                               radians */

/* output parameters: */
/* ------------------ */
/* az1          azi at sta 1 -> sta 2                       radians */
/* az2          azi at sta 2 -> sta 1                       radians */
/* s            geodetic dist between sta(s) 1 & 2          meters */

/* local variables and constants: */
/* ------------------------------ */
/* aa               constant from subroutine gpnloa */
/* alimit           equatorial arc distance along the equator   (radians) */
/* arc              meridional arc distance latitude p1 to p2 (in meters) */
/* az1              azimuth forward                          (in radians) */
/* az2              azimuth back                             (in radians) */
/* bb               constant from subroutine gpnloa */
/* dlon             temporary value for difference in longitude (radians) */
/* equ              equatorial distance                       (in meters) */
/* r1,r2            temporary variables */
/* s                ellipsoid distance                        (in meters) */
/* sms              equatorial - geodesic distance (S - s) "Sms" */
/* ss               temporary variable */
/* TOL0             tolerance for checking computation value */
/* TOL1             tolerance for checking a real zero value */
/* TOL2             tolerance for close to zero value */

/*     test the longitude difference with TOL1 */
/*     TOL1 is approximately 0.000000001 arc seconds */
    f = A->E->f;
    esq = A->E->es;
    ss = A->pt2->lam - A->pt1->lam;
    if (fabs(ss) < TOL1) {
	r2 = A->pt2->phi;
	r1 = A->pt1->phi;
	arc = merid_arc(esq, r1, r2);
	A->S = A->E->a * fabs(arc);
	if (A->pt2->phi > A->pt1->phi) {
	    A->az12 = 0.;
	    A->az21 = M_PI;
	} else {
	    A->az12 = M_PI;
	    A->az21 = 0.;
	}
	return;
    }
/*     test for longitude over 180 degrees */
    dlon = A->pt2->lam - A->pt1->lam;

    if (dlon >= 0.) {
	if ((M_PI <= dlon) && (dlon < (2. * M_PI)))
	    dlon -= (2. * M_PI);
    } else {
	ss = fabs(dlon);
	if (M_PI <= ss && ss < (2. * M_PI))
	    dlon += (2. * M_PI);
    }
    ss = fabs(dlon);
    if (ss > M_PI)
	ss = (2. * M_PI) - ss;
/*     compute the limit in longitude (alimit), it is equal */
/*     to twice the distance from the equator to the pole, */
/*     as measured along the equator (east/west) */
    alimit = M_PI * (1. - f);
/*     test for anti-nodal difference */
    if (ss >= alimit) {
	r1 = fabs(A->pt1->phi);
	r2 = fabs(A->pt2->phi);
	/*       latitudes r1 & r2 are not near the equator */
	if (!(r1 > TOL2 && r2 > TOL2) &&
	    /*       longitude difference is greater than lift-off point */
	    /*       now check to see if  "both"  r1 & r2 are on equator */
	    !(r1 < TOL1 && r2 > TOL2) && !(r2 < TOL1 && r1 > TOL2)) {
	    /*       check for either r1 or r2 just off the equator but < TOL2 */
	    if (r1 > TOL1 || r2 > TOL1) {
		A->az12 = 0.;
		A->az21 = 0.;
		A->S = 0.;
		return;
	    }
	    /*       compute the azimuth to anti-nodal point */
	    func_loa(f, esq, dlon, A->az12, &(A->az21), &aa, &bb, &sms);
	    /*       compute the equatorial distance & geodetic */
	    equ = fabs(dlon);
	    A->S = equ - sms;
	    return;
	}
    }
    f0 = 1. - f;
    b = f0;
    epsq = esq / (1. - esq);
    f2 = f * f;
    f3 = f * f2;
    f4 = f * f3;
/*     the longitude difference */
    dlon = A->pt2->lam - A->pt1->lam;
    ab = dlon;
/*     the reduced latitudes */
    u1 = f0 * sin(A->pt1->phi) / cos(A->pt1->phi);
    u2 = f0 * sin(A->pt2->phi) / cos(A->pt2->phi);
    u1 = atan(u1);
    u2 = atan(u2);
    su1 = sin(u1);
    cu1 = cos(u1);
    su2 = sin(u2);
    cu2 = cos(u2);
/*     counter for the iteration operation */
    kount = 0;
    do {
	clon = cos(ab);
	slon = sin(ab);
	csig = su1 * su2 + cu1 * cu2 * clon;
	ssig = hypot(slon * cu2, su2 * cu1 - su1 * cu2 * clon);
	sig = atan2(ssig, csig);
	sinalf = cu1 * cu2 * slon / ssig;
	w = 1. - sinalf * sinalf;
	t4 = w * w;
	t6 = w * t4;
	/*     the coefficients of type a */
	ao = f - f2 * (f + 1. + f2) * w / 4. + f3 * 3. * (f * 9. / 4. + 1.) *
	    t4 / 16. - f4 * 25. * t6 / 128.;
	a2 = f2 * (f + 1. + f2) * w / 4. - f3 * (f * 9. / 4. + 1.) * t4 / 4. +
	    f4 * 75. * t6 / 256.;
	a4 = f3 * (f * 9. / 4. + 1.) * t4 / 32. - f4 * 15. * t6 / 256.;
	a6 = f4 * 5. * t6 / 768.;
	/*     the multiple angle functions */
	qo = 0.;
	if (w > TOL0)
	    qo = su1 * -2. * su2 / w;
	q2 = csig + qo;
	q4 = q2 * 2. * q2 - 1.;
	q6 = q2 * (q2 * 4. * q2 - 3.);
	r2 = ssig * 2. * csig;
	r3 = ssig * (3. - ssig * 4. * ssig);
	/*     the longitude difference */
	A->S =
	    sinalf * (ao * sig + a2 * ssig * q2 + a4 * r2 * q4 + a6 * r3 * q6);
	xz = dlon + A->S;
	xy = fabs(xz - ab);
	ab = dlon + A->S;
    } while (xy >= 5e-14 && ++kount <= 7);
/*     the coefficients of type b */
    z = epsq * w;
    bo = z * (z * (z * (.01953125 - z * 175. / 16384.) - .046875) + .25) + 1.;
    b2 = z * (z * (z * (z * 35. / 2048. - .029296875) + .0625) - .25);
    b4 = z * z * (z * (.005859375 - z * 35. / 8192.) - .0078125);
    b6 = z * z * z * (z * 5. / 6144. - 6.5104166666666663e-4);
/*     distance */
    A->S = A->E->a * b *
	(bo * sig + b2 * ssig * q2 + b4 * r2 * q4 + b6 * r3 * q6);
/*     first compute the az12 & az21 for along the equator */
    if (dlon > M_PI)
	dlon -= M_PI * 2.;
    if (fabs(dlon) > M_PI)
	dlon += M_PI * 2.;
    A->az12 = M_PI / 2.;
    if (dlon < 0.)
	A->az12 *= 3.;
    A->az21 = A->az12 + M_PI;
    if (A->az21 > M_PI * 2.)
	A->az21 -= M_PI * 2.;
/*     now compute the az1 & az2 for latitudes not on the equator */
    if (!(fabs(su1) < TOL0 && fabs(su2) < TOL0)) {
	tana1 = slon * cu2 / (su2 * cu1 - clon * su1 * cu2);
	tana2 = slon * cu1 / (su1 * cu2 - clon * su2 * cu1);
	sina1 = sinalf / cu1;
	sina2 = -sinalf / cu2;
	/* azimuths from north,longitudes positive east */
	A->az12 = atan2(sina1, sina1 / tana1);
	A->az21 = M_PI - atan2(sina2, sina2 / tana2);
    }
    if (A->az12 < 0.)
	A->az12 += (2. * M_PI);
    if (A->az21 < 0.)
	A->az21 += (2. * M_PI);
    return;
}

/*
 * $Log: proj_in_inv.c,v $
 * Revision 5.2  2009/05/06 18:46:51  gie
 * updates for Doxygen
 *
 * Revision 5.1  2009/04/30 20:47:47  gie
 * *** empty log message ***
 *
*/
