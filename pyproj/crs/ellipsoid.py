from pyproj._crs import Ellipsoid


class CustomEllipsoid(Ellipsoid):
    """
    .. versionadded:: 2.5.0

    Class to build a custom ellipsoid.
    """

    def __new__(
        cls,
        semi_major_axis=None,
        inverse_flattening=None,
        semi_minor_axis=None,
        radius=None,
    ):
        """
        Parameters
        ----------
        semi_major_axis: float, optional
            The semi major axis in meters. Required if missing radius.
        inverse_flattening: float, optional
            The inverse flattening in meters.
            Required if missing semi_minor_axis and radius.
        semi_minor_axis: float, optional
            The semi minor axis in meters.
            Required if missing inverse_flattening and radius.
        radius: float, optional
            The radius in meters. Can only be used alone.
            Cannot be mixed with other parameters.
        """
        ellipsoid_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "Ellipsoid",
            "name": "undefined",
        }
        if semi_major_axis is not None:
            ellipsoid_json["semi_major_axis"] = semi_major_axis
        if inverse_flattening is not None:
            ellipsoid_json["inverse_flattening"] = inverse_flattening
        if semi_minor_axis is not None:
            ellipsoid_json["semi_minor_axis"] = semi_minor_axis
        if radius is not None:
            ellipsoid_json["radius"] = radius
        return cls.from_json_dict(ellipsoid_json)
