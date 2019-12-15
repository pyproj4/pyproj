from pyproj._crs import Datum, Ellipsoid, PrimeMeridian


class CustomDatum(Datum):
    """
    .. versionadded:: 2.5.0

    Class to build a datum based on an ellipsoid and prime meridian.
    """

    def __new__(cls, ellipsoid="WGS 84", prime_meridian="Greenwich"):
        """
        Parameters
        ----------
        ellipsoid: Any, optional
            Anything accepted by :meth:`pyproj.crs.Ellipsoid.from_user_input`
            or a :class:`pyproj.crs.ellipsoid.CustomEllipsoid`.
        prime_meridian: Any, optional
            Anything accepted by :meth:`pyproj.crs.PrimeMeridian.from_user_input`.
        """
        datum_json = {
            "type": "GeodeticReferenceFrame",
            "name": "unknown",
            "ellipsoid": Ellipsoid.from_user_input(ellipsoid).to_json_dict(),
            "prime_meridian": PrimeMeridian.from_user_input(
                prime_meridian
            ).to_json_dict(),
        }
        return cls.from_json_dict(datum_json)
