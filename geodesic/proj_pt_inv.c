/*
** Copyright (c) 2009   Gerald I. Evenden
*/
static const char
 PROG_ID[] = "$Id: proj_pt_inv.c,v 5.1 2009/04/30 20:47:47 gie Exp gie $";
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
 * @file proj_pt_inv.c
 * @brief Thomas Inverse Geodetic Function
 * @author Gerald I. Evenden
 */
#include <math.h>
#include <project.h>
# define DTOL	1e-12
/**
 * @brief Inverse geodesic function
 * @param Arc pointer to geodetic line structure
 * 
 * Procedure determins distance and forward/back azimuth between
 * points pt1 and pt2 in stucture Arc based upon an ellipsoidal
 * Earth.
 *
 * Based upon "Spherical Geodesics, Reference Systems, & Local
 * Geometry", USNOO SP-138, 1970, Paul Thomas.
 */
void proj_pt_inv(PROJ_LINE * Arc) {
    double th1, th2, thm, dthm, dlamm, dlam, sindlamm, costhm, sinthm, cosdthm,
	sindthm, L, E, cosd, d, X, Y, T, sind, tandlammp, u, v, D, A, B, f2, f4,
	f64, onef;

    f4 = 0.5 * (f2 = 0.5 * (onef = Arc->E->f));
    f64 = 0.25 * f4 * f4;
    onef = 1. - onef;
    th1 = atan(onef * tan(Arc->pt1->phi));
    th2 = atan(onef * tan(Arc->pt2->phi));
    thm = .5 * (th1 + th2);
    dthm = .5 * (th2 - th1);
    dlamm = .5 * (dlam = proj_adjlon(Arc->pt2->lam - Arc->pt1->lam));
    if (fabs(dlam) < DTOL && fabs(dthm) < DTOL) {	// pt1 == pt2
	Arc->az12 = Arc->az21 = Arc->S = 0.;
	return;
    }
    sindlamm = sin(dlamm);
    costhm = cos(thm);
    sinthm = sin(thm);
    cosdthm = cos(dthm);
    sindthm = sin(dthm);
    L = sindthm * sindthm + (cosdthm * cosdthm - sinthm * sinthm)
	* sindlamm * sindlamm;
    d = acos(cosd = 1 - L - L);
    E = cosd + cosd;
    sind = sin(d);
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
    Arc->S = sind * (T - f4 * (T * X - Y) +
		     f64 * (X * (A + (T - .5 * (A - E)) * X) -
			    Y * (B + E * Y) + D * X * Y));
    tandlammp = tan(.5 * (dlam - .25 * (Y + Y - E * (4. - X)) *
			  (f2 * T + f64 * (32. * T - (20. * T - A)
					   * X - (B + 4.) * Y)) * tan(dlam)));
    u = atan2(sindthm, (tandlammp * costhm));
    v = atan2(cosdthm, (tandlammp * sinthm));
    Arc->az12 = proj_adjlon((2 * M_PI) + v - u);
    Arc->az21 = proj_adjlon((2 * M_PI) - v - u);
}

/*
 * $Log: proj_pt_inv.c,v $
 * Revision 5.1  2009/04/30 20:47:47  gie
 * *** empty log message ***
 *
*/
