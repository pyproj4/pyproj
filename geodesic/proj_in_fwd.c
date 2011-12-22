/*
** Copyright (c) 2009   Gerald I. Evenden
*/
static const char
 PROJ_ID[] = "$Id: proj_in_fwd.c,v 5.1 2009/04/30 20:47:47 gie Exp gie $";
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
/** @file proj_in_fwd.c
 * @brief compute the forward geodesic for an ellipsoid
 */
#include <math.h>
#include <project.h>
#define  EPS 5e-14
/**
 * @brief forward geodesic computation
 * @param A pointer to geodesic line structure
 */
void proj_in_fwd(PROJ_LINE * A) {
    double c, d, e, r, x, y, cf, sa, cu, sf, cy, cz, su, tu, sy, c2a, flat;

/* *** SOLUTION OF THE GEODETIC DIRECT PROBLEM AFTER T.VINCENTY */
/* *** MODIFIED RAINSFORD'S METHOD WITH HELMERT'S ELLIPTICAL TERMS */
/* *** EFFECTIVE IN ANY AZIMUTH AND AT ANY DISTANCE SHORT OF ANTIPODAL */

/* *** A IS THE SEMI-MAJOR AXIS OF THE REFERENCE ELLIPSOID */
/* *** F IS THE FLATTENING OF THE REFERENCE ELLIPSOID */
/* *** LATITUDES AND LONGITUDES IN RADIANS POSITIVE NORTH AND EAST */
/* *** AZIMUTHS IN RADIANS CLOCKWISE FROM NORTH */
/* *** GEODESIC DISTANCE S ASSUMED IN UNITS OF SEMI-MAJOR AXIS A */

/* *** PROGRAMMED FOR CDC-6600 BY LCDR L.PFEIFER NGS ROCKVILLE MD 20FEB75 */
/* *** MODIFIED FOR SYSTEM 360 BY JOHN G GERGEN NGS ROCKVILLE MD 750608 */

    r = 1.0 - (flat = A->E->f);
    tu = r * sin(A->pt1->phi) / cos(A->pt1->phi);
    sf = sin(A->az12);
    cf = cos(A->az12);
    A->az21 = 0.0;
    if (cf != 0.0)
	A->az21 = atan2(tu, cf) * 2.0;
    cu = 1.0 / sqrt(tu * tu + 1.0);
    su = tu * cu;
    sa = cu * sf;
    c2a = -sa * sa + 1.0;
    x = sqrt((1.0 / r / r - 1.0) * c2a + 1.0) + 1.0;
    x = (x - 2.0) / x;
    c = 1.0 - x;
    c = (x * x / 4.0 + 1) / c;
    d = (x * .375 * x - 1.0) * x;
    tu = A->S / A->E->a / r / c;
    y = tu;
    do {
	sy = sin(y);
	cy = cos(y);
	cz = cos(A->az21 + y);
	e = cz * cz * 2.0 - 1.0;
	c = y;
	x = e * cy;
	y = e + e - 1.0;
	y = (((sy * sy * 4.0 - 3.0) * y * cz * d / 6.0 + x) * d / 4.0 - cz) *
	    sy * d + tu;
    } while (fabs(y - c) > EPS);
    A->az21 = cu * cy * cf - su * sy;
    A->pt2->phi = atan2(su * cy + cu * sy * cf, r * hypot(sa, A->az21));
    x = atan2(sy * sf, cu * cy - su * sy * cf);
    c = ((c2a * -3.0 + 4.0) * flat + 4.0) * c2a * flat / 16.0;
    d = ((e * cy * c + cz) * sy * c + y) * sa;
    A->pt2->lam = A->pt1->lam + x - (1.0 - c) * d * flat;
    A->az21 = atan2(sa, A->az21) + M_PI;
    A->az12 = proj_adjlon(A->az12);
    A->az21 = proj_adjlon(A->az21);
    return;
}

/*
 * $Log: proj_in_fwd.c,v $
 * Revision 5.1  2009/04/30 20:47:47  gie
 * *** empty log message ***
 *
*/
