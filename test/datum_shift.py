from pyproj import Proj, transform

# illustrates the use of the transform function to
# perform coordinate transformations with datum shifts.
#
#  This example is from Roberto Vidmar
#
#        Test point is Trieste, Molo Sartorio
#
#  This data come from the Istituto Geografico Militare (IGM), as well as
#  the 7 parameters to transform from Gauss-Boaga (our reference frame)
#  to WGS84
#
#                WGS84 Lat:  45d38'49.879" (45.647188611)
#                WGS84 Lon:  13d45'34.397" (13.759554722)
#                WGS84 z:    52.80;
#                UTM 33:     403340.97   5055597.17
#                GB:         2423346.99  5055619.87

UTM_x = 403340.97
UTM_y = 5055597.17
GB_x = 2423346.99
GB_y = 5055619.87
WGS84_lat = 45.647188611  # Degrees
WGS84_lon = 13.759554722  # Degrees
UTM_z = WGS84_z = 52.8  # Ellipsoidical height in meters

wgs84 = Proj(proj="latlong", datum="WGS84")
print("proj4 library version = ", wgs84.proj_version)
utm33 = Proj(proj="utm", zone="33")
gaussb = Proj(
    init="epsg:26592", towgs84="-122.74,-34.27,-22.83,-1.884,-3.400,-3.030,-15.62"
)

print("\nWGS84-->UTM")
print("Trieste, Molo Sartorio WGS84:", WGS84_lon, WGS84_lat, WGS84_z)
print("Trieste, Molo Sartorio UTM33 (from IGM):", UTM_x, UTM_y)
xutm33, yutm33, zutm33 = transform(wgs84, utm33, WGS84_lon, WGS84_lat, WGS84_z)
print("Trieste, Molo Sartorio UTM33 (converted):", xutm33, yutm33, zutm33)
print("Difference (meters):", xutm33 - UTM_x, yutm33 - UTM_y, zutm33 - UTM_z)

print("\nWGS84-->Gauss-Boaga")
print("Trieste, Molo Sartorio Gauss-Boaga (from IGM):", GB_x, GB_y)
z = 0  # No ellipsoidical height for Gauss-Boaga
xgb, ygb, zgb = transform(wgs84, gaussb, WGS84_lon, WGS84_lat, z)
print("Trieste, Molo Sartorio Gauss-Boaga (converted):", xgb, ygb)
print("Difference (meters):", xgb - GB_x, ygb - GB_y)

print("\nUTM-->WGS84")
print("Trieste, Molo Sartorio UTM33 (converted):", xutm33, yutm33, zutm33)
back_lon, back_lat, back_z = transform(utm33, wgs84, xutm33, yutm33, zutm33)
print("Trieste, Molo Sartorio WGS84 (converted back):", back_lon, back_lat, back_z)
print(
    "Difference (seconds):",
    (back_lon - WGS84_lon) * 3600,
    (back_lat - WGS84_lat) * 3600,
    back_z - WGS84_z,
    "(m)",
)

print("\nGauss-Boaga-->WGS84")
print("Trieste, Molo Sartorio Gauss-Boaga (converted):", xgb, ygb, zgb)
back_lon, back_lat, back_z = transform(gaussb, wgs84, xgb, ygb, zgb)
print("Trieste, Molo Sartorio WGS84 (converted back):", back_lon, back_lat, back_z)
print(
    "Difference (seconds):",
    (back_lon - WGS84_lon) * 3600,
    (back_lat - WGS84_lat) * 3600,
    back_z - WGS84_z,
    "(m)",
)

print("\nUTM (from IGM) --> WGS84")
print("Trieste, Molo Sartorio UTM33 (from IGM):", UTM_x, UTM_y)
conv_lon, conv_lat, conv_z = transform(utm33, wgs84, UTM_x, UTM_y, UTM_z)
print("Trieste, Molo Sartorio WGS84 (converted):", conv_lon, conv_lat, conv_z)
print(
    "Difference (seconds):",
    (conv_lon - WGS84_lon) * 3600,
    (conv_lat - WGS84_lat) * 3600,
    conv_z - WGS84_z,
    "(m)",
)


print("\nGauss-Boaga (from IGM) --> WGS84")
print("Trieste, Molo Sartorio Gauss-Boaga (from IGM):", GB_x, GB_y)
GB_z = 0  # No ellipsoidical height for Gauss-Boaga
conv_lon, conv_lat, conv_z = transform(gaussb, wgs84, GB_x, GB_y, GB_z)
print("Trieste, Molo Sartorio WGS84 (converted):", conv_lon, conv_lat)
print(
    "Difference (seconds):",
    (conv_lon - WGS84_lon) * 3600,
    (conv_lat - WGS84_lat) * 3600,
)
