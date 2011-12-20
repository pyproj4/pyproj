/*
** Copyright (c) 2009   Gerald I. Evenden
*/
static const char
 PROJ_ID[] = "$Id: proj_sp_inv.c,v 5.1 2009/04/30 20:47:47 gie Exp gie $";
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
/* Procedure to compute the distance, dist, along a great circle
 * between point A->pt1.phi-A->pt1.lam and point A->pt2.phi-A->pt2.lam.  In addition,
 * the forward azimuth, Az_01, of the great circle at point 0 and
 * the back azimuth, Az_10, at point 1 are returned.  All arguments
 * and results are in radians.
 *
 * Computation for a spherical earth based upon formulas in "Map
 * Projections--A Working Manual," USGS Bulletin 1395, p. 30-31,
 * 1987 by John P. Snyder.
*/
/** @file proj_sp_inv.c
 * @brief compute the inverse geodesic for a spherical earth.
 * @author Gerald I. Evenden
 */
#include <math.h>
#include <project.h>
/** @brief Inverse geodesic computation - spherical earth
 * @param A pointer to geodesic line structure
 * @author Gerald I. Evenden
 *
 * Computes distance, forward and back azimuths in structure
 * for the two end points of the geodesic line
 *
 * Algorithm based upon J. Snyder's method, described in "Map Projection---
 * A Working Manual", USGS Prof. Paper 1396, p. 30, which minimized
 * loss of precision for closely spaced points.
 * Comments in body of procedure note alternative computation to maintain
 * precision at the apod.
 */
void proj_sp_inv(PROJ_LINE * A) {
    double dlam, dphi, shp, shl, c1, c0, s1, s0;

    dlam = A->pt2->lam - A->pt1->lam;
    dphi = A->pt2->phi - A->pt1->phi;
    c1 = cos(A->pt2->phi);
    c0 = cos(A->pt1->phi);
    s1 = sin(A->pt2->phi);
    s0 = sin(A->pt1->phi);
    shp = sin(0.5 * dphi);
    shl = sin(0.5 * dlam);
/*
 * the following is suggestion of JP Snyder for greater precision
 * for points close together compared to the cosine version.
 */
    A->S = 2. * A->E->a * asin(sqrt(shp * shp + c0 * c1 * shl * shl));
/*
 * the follewing is purported to maintain precison at both nearby
 * points and those at apodal distances.  However, limited testing
 * shows precious little difference at the apode it remains as
 * a referenced alternative.
 */
//      { double t = cos(dlam);
//      A->S = A->E->a * atan2(hypot(c1*sin(dlam), c0*s1-s0*c1*t),
//                      s0*s1 + c0*c1*t);
//      }

    A->az12 = atan2(c1 * (shp = sin(dlam)),
		    c0 * s1 - s0 * c1 * (shl = cos(dlam)));
    if (A->az12 < 0.)
	A->az12 += 2.*M_PI;
    A->az21 = -atan2(c0 * shp, c1 * s0 - s1 * c0 * shl);
    if (A->az21 < 0.)
	A->az21 += 2.*M_PI;
    A->az12 = proj_adjlon(A->az12);
    A->az21 = proj_adjlon(A->az21);
}

/*
 * $Log: proj_sp_inv.c,v $
 * Revision 5.1  2009/04/30 20:47:47  gie
 * *** empty log message ***
 *
*/
