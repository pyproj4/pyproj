/*
** Copyright (c) 2009   Gerald I. Evenden
*/
static const char
 PROG_ID[] = "$Id: proj_pt_fwd.c,v 5.1 2009/04/30 20:47:47 gie Exp gie $";
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
/**
 * @file proj_pt_fwd.c
 * @brief Thomas Forward geodesic function
 * @author Gerald I. Evenden
 */
#include <math.h>
#include <project.h>
# define MERI_TOL 1e-9
/**
 * @brief Forward geodesic function
 * @param Arc pointer to geodetic line structure
 * 
 * Procedure determins point point 2 and azimuth at distance
 * and azimuth from pt1 upon an ellipsoidal Earth.
 *
 * Based upon "Spherical Geodesics, Reference Systems, & Local
 * Geometry", USNOO SP-138, 1970, Paul Thomas.
 */
void proj_pt_fwd(PROJ_LINE * Arc) {
    double d, sind, u, V, X, ds, cosds, sinds, ss, de, al12, f2, f4, f, onef;
    double th1, costh1, sinth1, sina12, cosa12, M, N, c1, c2, D, P, s1, al21,
	phi2;
    int merid, signS;

    f4 = 0.5 * (f2 = 0.5 * (f = Arc->E->f));
    onef = 1. - f;
    al12 = proj_adjlon(Arc->az12);	/* reduce to  +- 0-PI */
    signS = fabs(al12) > M_PI_2 ? 1 : 0;
    th1 = atan(onef * tan(Arc->pt1->phi));
    costh1 = cos(th1);
    sinth1 = sin(th1);
    if ((merid = fabs(sina12 = sin(al12)) < MERI_TOL)) {
	sina12 = 0.;
	cosa12 = fabs(al12) < M_PI_2 ? 1. : -1.;
	M = 0.;
    } else {
	cosa12 = cos(al12);
	M = costh1 * sina12;
    }
    N = costh1 * cosa12;
    if (merid) {
	c1 = 0.;
	c2 = f4;
	D = 1. - c2;
	D *= D;
	P = c2 / D;
    } else {
	c1 = f * M;
	c2 = f4 * (1. - M * M);
	D = (1. - c2) * (1. - c2 - c1 * M);
	P = (1. + .5 * c1 * M) * c2 / D;
    }
    if (merid)
	s1 = M_PI_2 - th1;
    else {
	s1 = (fabs(M) >= 1.) ? 0. : acos(M);
	s1 = sinth1 / sin(s1);
	s1 = (fabs(s1) >= 1.) ? 0. : acos(s1);
    }
    d = Arc->S / (D * Arc->E->a);
    if (signS)
	d = -d;
    u = 2. * (s1 - d);
    V = cos(u + d);
    X = c2 * c2 * (sind = sin(d)) * cos(d) * (2. * V * V - 1.);
    ds = d + X - 2. * P * V * (1. - 2. * P * cos(u)) * sind;
    ss = s1 + s1 - ds;
    cosds = cos(ds);
    sinds = sin(ds);
    if (signS)
	sinds = -sinds;
    al21 = N * cosds - sinth1 * sinds;
    if (merid) {
	phi2 = atan(tan(M_PI_2 + s1 - ds) / onef);
	if (al21 > 0.) {
	    al21 = M_PI;
	    if (signS)
		de = M_PI;
	    else {
		phi2 = -phi2;
		de = 0.;
	    }
	} else {
	    al21 = 0.;
	    if (signS) {
		phi2 = -phi2;
		de = 0;
	    } else
		de = M_PI;
	}
    } else {
	al21 = atan(M / al21);
	if (al21 > 0.)
	    al21 += M_PI;
	if (al12 < 0.)
	    al21 -= M_PI;
	Arc->az21 = proj_adjlon(al21);
	Arc->pt2->phi = atan(-(sinth1 * cosds + N * sinds) * sin(al21) /
			     (onef * M));
	de = atan2(sinds * sina12, (costh1 * cosds - sinth1 * sinds * cosa12));
	if (signS)
	    de += c1 * ((1. - c2) * ds + c2 * sinds * cos(ss));
	else
	    de -= c1 * ((1. - c2) * ds - c2 * sinds * cos(ss));
    }
    Arc->pt2->lam = proj_adjlon(Arc->pt1->lam + de);
}

/*
 * $Log: proj_pt_fwd.c,v $
 * Revision 5.1  2009/04/30 20:47:47  gie
 * *** empty log message ***
 *
*/
