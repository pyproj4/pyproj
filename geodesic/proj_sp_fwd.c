/*
** Copyright (c) 2009   Gerald I. Evenden
*/
static const char
 PROJ_ID[] = "$Id: proj_sp_fwd.c,v 5.1 2009/04/30 20:47:47 gie Exp gie $";
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
/* Procedure to compute the geographic location of a point 1 at
 * azimuth A->az12 and distance A->S along a great circle from
 * point 0.  In addition the back azimuth from 1 to 0 is determined.
 * All arguments in radians.
 *
 * Computation for a spherical earth based upon formulas in "Map
 * Projections--A Working Manual," USGS Bulletin 1395, p. 30-31,
 * 1987 by John P. Snyder.
*/
/** @file proj_sp_fwd.c
 * @brief compute the forward geodesic for a spherical earth.
 * @author Gerald I. Evenden
 */
#include <math.h>
#include <project.h>
/** @brief Forward geodesic computation - spherical earth
 * @param A pointer to geodesic line structure
 *
 * Computes the location of the second point in the structure
 * based on the first point's location and the distance and
 * forward azumuth
 */
void proj_sp_fwd(PROJ_LINE * A) {
    double cc, sc, cp, sp, ca, dl, S;

    cc = cos(S = A->S / A->E->a);
    sc = sin(S);
    cp = cos(A->pt1->phi);
    sp = sin(A->pt1->phi);
    ca = cos(A->az12);

    A->pt2->phi = asin(sp * cc + cp * sc * ca);
    A->pt2->lam = A->pt1->lam +
	atan2(sc * sin(A->az12), cp * cc - sp * sc * ca);
    dl = A->pt1->lam - A->pt2->lam;
    A->az21 = atan2(cp * sin(dl),
		    cos(A->pt2->phi) * sp - sin(A->pt2->phi) * cp * cos(dl));
    if (fabs(A->pt2->lam) > M_PI)
	A->pt2->lam -= copysign(2.*M_PI, A->pt2->lam);
}

/*
 * $Log: proj_sp_fwd.c,v $
 * Revision 5.1  2009/04/30 20:47:47  gie
 * *** empty log message ***
 *
*/
