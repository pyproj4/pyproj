/*
** Copyright (c) 2009   Gerald I. Evenden
**
** "$Id: project.h,v 1.2 2009/05/17 15:16:34 gie Exp gie $"
**
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
/** @file project.h
 * @brief The header file for the geodesic library routines
 * @author Gerald I. Evenden
 */
#ifndef PROJECT_incl
#define PROJECT_incl 1
#include <math.h>
#include <stddef.h>
#include <stdlib.h>
/** @brief Geographic coordinate */
typedef struct {
    double lam;     /**< longitude in radians */
    double phi;     /**< latitude in radians */
} PROJ_LP;
/** @brief Cartesian coordinate */
typedef struct {
    double x;	/**< Easting */
    double y;	/**< Northing */
} PROJ_XY;
/** @brief 3D Geographic coordinate */
typedef struct {
    double lam;	    /**< longitude in radians */
    double phi;	    /**< latitude in radians */
    double h;	    /**< height above the ellipsoid */
} PROJ_PT_LPH;
/**
 * @brief Geocentric Cartesian coordinate
 *
 * Each element in same units as \a a in structure \link ellips \endlink
 */
typedef struct {
    double x;	  /**< X axis */
    double y;	  /**< Y axis */
    double z;	  /**< Z axis */
} PROJ_PT_XYZ;
/**
 * @brief Earth's elliptical constants.
 *
 * Element \a a units, typically meters, defines the units for
 * all other length elements.
 */
typedef struct {
    double a;		/**< semi-major axis or sphere radius */
    double f;	    /**< ellipsoid flattening, if == 0 then sphere */
    double es;		/**< eccentricity squared, if == 0 then sphere */
    double one_es;     /**< 1-es */
} PROJ_ELLIPS;
/**
 * @brief Geodesic line structure
 *
 * Azimuths in radians clockwise from North.  Distance units the
 * same as element \a a in structure \link ellips \endlink.
 */
typedef struct {
    PROJ_PT_LPH *pt1;	  /**< pointer to geographic coord of first location */
    double az12;	/**< azimuth from pt1 to pt2 (forward) */
    PROJ_PT_LPH *pt2;	  /**< pointer to geographic coord of second location */
    double az21;	/**< azimuth from pt2 to pt1 (back) */
    double S;			/**< geodetic distance between points */
    PROJ_ELLIPS *E;	 /**< pointer to ellipsoid constants */
} PROJ_LINE;
/**
 * @brief linked argument list
 *
 * The size of param means nothing and is only of use so that
 * the debugger will dump at least that many characters.
 */
    /* parameter list struct */
typedef struct proj_arg_list {
    struct proj_arg_list *next;	    /**< pointer to next entry if !NULL */
    char used;			/**< if not 0 then argument referenced */
    char param[5];	/**< character string of argument */
} PROJ_PARAM_ITEM;
/**
 * @brief list of ellipsoid parameters
 */
struct PROJ_ELLPS_LIST {
    char *id;		/**< ellipse keyword name */
    char *major;	/**< a= major-axis value */
    char *ell;		/**< elliptical parameter */
    char *name;		/**< comments */
};

#ifndef PROJ_ELLPS_LIST_FLAG
extern const struct PROJ_ELLPS_LIST proj_ellps[];
#endif // end of PROJ_ELLPS_LIST_FLAG

/**
 * @brief list of prime meridians
 */
struct PROJ_PRIMES_LIST {
	char *name;		/**< prime meridian name */
	char *del_lon;	/**< longitude offset from Greenwich */
};

#ifndef PROJ_PRIMES_LIST_FLAG
extern const struct PROJ_PRIMES_LIST proj_pm_list[];
#endif // end of PROJ_PRIMES_LIST_FLAG

struct PROJ_DERIVS {
		double x_l, x_p; /* derivatives of x for lambda-phi */
		double y_l, y_p; /* derivatives of y for lambda-phi */
};
struct PROJ_FACTORS {
	struct PROJ_DERIVS der;
	double h, k;	/* meridinal, parallel scales */
	double omega, thetap;	/* angular distortion, theta prime */
	double conv;	/* convergence */
	double s;		/* areal scale factor */
	double a, b;	/* max-min scale error */
	int code;		/* info as to analytics, see following */
};
#define DERIVS(name) static int name(PROJ *P, PROJ_LP lp, struct PROJ_DERIVS *der) {

#define IS_ANAL_XL_YL 01	/* derivatives of lon analytic */
#define IS_ANAL_XP_YP 02	/* derivatives of lat analytic */
#define IS_ANAL_HK	04		/* h and k analytic */
#define IS_ANAL_CONV 010	/* convergence analytic */
struct PROJ_UNITS {
	char	*id;	/* units keyword */
	char	*to_meter;	/* multiply by value to get meters */
	char	*name;	/* comments */
};

typedef struct { double r, i; }	PROJ_COMPLEX;

/**
 * @brief basic projection control structure
 */
typedef struct PROJconsts {
	PROJ_XY  (*fwd)(PROJ_LP, struct PROJconsts *); /**< forward projection */
	PROJ_LP  (*inv)(PROJ_XY, struct PROJconsts *); /**< inverse projection */
	void (*spc)(PROJ_LP, struct PROJconsts *, struct PROJ_FACTORS *); /**< projection factors */
	int  (*derivs)(struct PROJconsts *, PROJ_LP, struct PROJ_DERIVS *); /**< drivatives entry */
	void (*pfree)(struct PROJconsts *); /**< free this structure memory */
	const char *descr; /**< string of projection characteristics */
	PROJ_PARAM_ITEM *params;   /**< parameter list */
	int over;   /**< over-range flag */
	double
		a,  /**< major axis or radius if es==0 */
		e,  /**< eccentricity */
		es, /**< e ^ 2 */
		ra, /**< 1/a */
		one_es, /**< 1 - e^2 */
		rone_es, /**< 1/one_es */
		primer, /**< prime meridian */
		netlam0, /**< net adjustment to I/O longitude value */
		lam0, phi0, /**< central longitude, latitude */
		x0, y0, /**< false easting and northing */
		k0,	/**< general scaling factor */
		to_meter, fr_meter; /**< Cartesian scaling */
#ifdef PROJ_PARMS__
PROJ_PARMS__
#endif /* end of optional extensions */
} PROJ;
/**
 * @brief structure listing the available projection entries
 */
struct PROJ_LIST {
	char	*id;		/**< projection keyword */
	PROJ	*(*proj)(PROJ *);	/**< projection entry point */
	char 	* const *descr;	/**< description text */
};

/* Generate proj_list external or make list from include file */
#ifndef PROJ_LIST_H
extern const struct PROJ_LIST proj_list[];
#else
#define PROJ_HEAD(id, name) \
	extern PROJ *proj_##id(PROJ *); extern char * const proj_s_##id;
#include PROJ_LIST_H
#undef PROJ_HEAD
#define PROJ_HEAD(id, name) {#id, proj_##id, &proj_s_##id},
	const struct PROJ_LIST
proj_list[] = {
#include PROJ_LIST_H
		{0,     0,  0},
	};
#undef PROJ_HEAD
#endif // end of PROJ_LIST_H

typedef struct {int errnum; char * name; } PROJ_ERR_LIST;
#ifndef PROJ_UNITS__
extern const struct PROJ_UNITS proj_units[];
#endif // end of PROJ_UNITS

extern int * proj_errno_loc(void);
#define proj_errno (*proj_errno_loc())
#ifdef PROJ_LIB__
    /* repeatative projection code */
#define PROJ_HEAD(id, name) static const char des_##id [] = name
#define ENTRYA(name) const char * const proj_s_##name = des_##name; \
	PROJ *proj_##name(PROJ *P) { if (!P) { \
	if ((P = (PROJ *)malloc(sizeof(PROJ)))) { \
	P->pfree = freeup; P->fwd = 0; P->inv = 0; \
	P->spc = 0; P->descr = des_##name;
#define ENTRYX } return P; } else {
#define ENTRY0(name) ENTRYA(name) ENTRYX
#define ENTRY1(name, a) ENTRYA(name) P->a = 0; ENTRYX
#define ENTRY2(name, a, b) ENTRYA(name) P->a = 0; P->b = 0; ENTRYX
#define ENDENTRY(p) } return (p); }
#define E_ERROR(err) { proj_errno = err; freeup(P); return(0); }
#define E_ERROR_0 { freeup(P); return(0); }
#define F_ERROR { proj_errno = -20; return(xy); }
#define I_ERROR { proj_errno = -20; return(lp); }
#define FORWARD(name) static PROJ_XY name(PROJ_LP lp,PROJ*P) {PROJ_XY xy={0.,0.}
#define INVERSE(name) static PROJ_LP name(PROJ_XY xy,PROJ*P) {PROJ_LP lp={0.,0.}
#define FREEUP static void freeup(PROJ *P) {
#define SPECIAL(name) static void name(PROJ_LP lp, PROJ *P, struct PROJ_FACTORS *fac)
#endif // end of PROJ_LIB__

/**
* \defgroup local Locally developed procedures
 * @brief General purpose procedures.
 *
 */
/*@{*/
PROJ *proj_init(int, char **); 
void proj_free(PROJ *);
PROJ *proj_initstr(const char *);
int proj_ell_set(PROJ_PARAM_ITEM *, double *, double *);
PROJ_PARAM_ITEM *proj_mkparam(const char *, const char **);
PROJ_PARAM_ITEM *proj_free_param(PROJ_PARAM_ITEM *);
int proj_param(PROJ_PARAM_ITEM *, const char *, void *);
double proj_adjlon(double ang);
void proj_sp_inv(PROJ_LINE *);
void proj_sp_fwd(PROJ_LINE *);
void proj_pt_inv(PROJ_LINE *);
void proj_pt_fwd(PROJ_LINE *);
int proj_gforward(PROJ_LINE *);
int proj_ginverse(PROJ_LINE *);
double proj_dms2rad(const char *, char **);
int proj_rad2dms(char *, size_t, const char *, double, const char *);
int proj_casecmp(const char *, const char *);
int proj_ncasecmp(const char *, const char *, size_t);
int proj_factors(PROJ_LP, PROJ *, double, struct PROJ_FACTORS *);
double proj_qsfn(double, const void *);
void *proj_auth_ini(double, double *);
double proj_auth_lat(double, const void *);
double proj_auth_inv(double, const void *);
int proj_deriv(PROJ_LP, double h, PROJ *, struct PROJ_DERIVS *);
int *proj_errno_loc(void);
int proj_factors(PROJ_LP, PROJ *, double h, struct PROJ_FACTORS *);
void *proj_gauss_ini(double, double phi0, double *, double *);
PROJ_LP proj_gauss(PROJ_LP, const void *);
PROJ_LP proj_inv_gauss(PROJ_LP, const void *);
int proj_gdinverse(PROJ *, PROJ_LP *est, PROJ_XY, double);
void *proj_mdist_ini(double);
double proj_mdist(double, double sphi, double cphi, const void *);
double proj_inv_mdist(double, const void *);
double proj_msfn(double, double cosphi, double);
double proj_phi2(double, double);
double proj_psi(double, double sphi, double);
double proj_apsi(double, double);
const char *proj_strerrno(int);
int proj_strerror_r(int, char *, int);
double proj_asin(double);
double proj_acos(double);
double proj_sqrt(double);
double proj_atan2(double, double);
PROJ_LP proj_translate(PROJ_LP, const void *);
PROJ_LP proj_inv_translate(PROJ_LP, const void *);
void *proj_translate_ini(double, double);
double proj_tsfn(double, double sinphi, double);
PROJ_COMPLEX proj_zpoly1(PROJ_COMPLEX, PROJ_COMPLEX *, int);
PROJ_COMPLEX proj_zpolyd1(PROJ_COMPLEX, PROJ_COMPLEX *, int n, PROJ_COMPLEX *);

void proj_pr_list(PROJ *);
PROJ_XY proj_fwd(PROJ_LP, PROJ *);
PROJ_LP proj_inv(PROJ_XY, PROJ *);
/*@}*/

/** \defgroup imported Imported and translated procedures
 * @brief Procedures converted from FORTRAN to C
 *
 * These routines were extracted from FORTRAN programs located at
 * http://www.ngs.noaa.gov/PC_PROD/Inv_Fwd/ .
 * They are based upon mathematics by Vincenty:
 * http://www.ngs.noaa.gov/PUBS_LIB/inverse.pdf .
 *
 * The applicable procedures were extracted from the composite
 * program FORTRAN files FORWARD.FOR and INVERSE.FOR and
 * converted to C by the f2c program.  The converted procedures
 * were further edited to remove f2c dependencies and clean up
 * translation "noise."  Original FORTRAN code comments were
 * preserved when possible.
 *
 * The so called 3D versions of the geodesic procedures were not
 * translated because there seemed to be constants and other factors
 * that were limited to one ellipsoid and thus the procedures could not
 * be considered general purpose routines.
 *
 * Note: the original FORTRAN files were successfully compiled
 * by gfortran and served as a benchmark for the converted C code.
 */
/*@{ */
void proj_lph2xyz(PROJ_PT_LPH * p1, PROJ_PT_XYZ * p2, PROJ_ELLIPS * E);
int proj_xyz2lph(PROJ_PT_XYZ * p1, PROJ_PT_LPH * p2, PROJ_ELLIPS * E);
void proj_in_fwd(PROJ_LINE * A);
void proj_in_inv(PROJ_LINE * A);
/*@}*/
#endif				/* PROJECT_incl */
/*
 * $Log: project.h,v $
 * Revision 1.2  2009/05/17 15:16:34  gie
 * corrected list conditional
 *
 * Revision 1.1  2009/05/15 17:17:28  gie
 * Initial revision
 *
 * Revision 2.7  2009/04/03 19:46:43  gie
 * removed *fig.h from project.h
 *
 * Revision 2.6  2009/04/01 16:07:02  gie
 * corrected type_t to size_t --- what details, details, grr.
 *
 * Revision 2.5  2009/04/01 15:36:00  gie
 * added typedefs for PROJ_LP and _XY
 *
 * Revision 2.4  2009/03/27 20:08:47  gie
 * updates regarding proj_casecmp
 *
 * Revision 2.3  2009/03/20 00:15:29  gie
 * minor doxygen control change
 *
 * Revision 2.2  2009/02/23 22:44:27  gie
 * *** empty log message ***
 *
 * Revision 2.1  2009/02/01 19:27:11  gie
 * *** empty log message ***
 *
 * Revision 1.4  2009/01/09 21:35:23  gie
 * some additions
 *
 * Revision 1.3  2009/01/08 01:48:13  gie
 * prep for release
 *
 * Revision 1.2  2008/12/07 18:55:14  gie
 * initial
 *
 * Revision 1.1  2008/12/03 02:54:58  gie
 * Initial revision
 *
 */
