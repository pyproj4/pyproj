/*
** libgeodesy -- library of geodesy functions
**
** Copyright (c) 2003, 2006, 2009   Gerald I. Evenden
*/
static const char
 PROG_ID[] = "$Id: proj_adjlon.c,v 5.4 2009/05/05 23:40:30 gie Exp gie $";
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
 * @file proj_adjlon.c
 * @brief Reduce argument to range +/- PI
 * @author Gerald I. Evenden
*/
#include <math.h>
#define DBL_EPSILON 1e-14
/**
 * @brief reduce longitude to a range of +- 180 (+- pi)
 * @param lon longitude
 * @return reduced longitude value
 *
 * This seems like an expensive means of doing this problem where an
 * iterative add/subtraction might seem the more reasonable approach:
 * However, cases where a carelessly entered and quite large number
 * can bring a program to its knees with the iterative method.
 * May be a bit slower but it is safer.
 */
double proj_adjlon(double lon) {
    double x;

    if ((fabs(x = lon * M_1_PI) - 1.) > 3.*DBL_EPSILON) {
	x = 0.5 * (x + 1.0);
	lon = ((x - floor(x)) - 0.5) * 2 * M_PI;
    }
    return (lon);
}

/*
** $Log: proj_adjlon.c,v $
** Revision 5.4  2009/05/05 23:40:30  gie
** restored config.h header
**
** Revision 5.3  2009/05/03 01:00:29  gie
** removed config.h reference
**
** Revision 5.2  2009/05/01 17:54:48  gie
** added conditional compile
**
** Revision 5.1  2009/04/30 20:47:47  gie
** *** empty log message ***
**
*/
