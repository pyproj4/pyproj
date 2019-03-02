from pyproj import Geod
import commands, cPickle

g = Geod(ellps="clrk66")
lat1pt = 42.0 + (15.0 / 60.0)
lon1pt = -71.0 - (7.0 / 60.0)
lat2pt = 45.0 + (31.0 / 60.0)
lon2pt = -123.0 - (41.0 / 60.0)
print(lat1pt, lon1pt, lat2pt, lon2pt)
print("inverse transform")
print("from proj.4 invgeod:")
print(
    commands.getoutput(
        "echo \"42d15'N 71d07'W 45d31'N 123d41'W\" | geod +ellps=clrk66 -I -f \"%.3f\""
    )
)
print("from pyproj.Geod.inv:")
az12, az21, dist = g.inv(lon1pt, lat1pt, lon2pt, lat2pt)
print("%7.3f %6.3f %12.3f" % (az12, az21, dist))
print("forward transform")
print("from proj.4 geod:")
print(
    commands.getoutput(
        'echo "42d15\'N 71d07\'W -66d31\'50.141 4164192.708" | geod +ellps=clrk66 -f "%.3f"'
    )
)
endlon, endlat, backaz = g.fwd(lon1pt, lat1pt, az12, dist)
print("from pyproj.Geod.fwd:")
print("%6.3f  %6.3f %13.3f" % (endlat, endlon, backaz))
print("intermediate points:")
print("from geod with +lat_1,+lon_1,+lat_2,+lon_2,+n_S:")
points = "+lon_1=%s +lat_1=%s +lon_2=%s +lat_2=%s" % (lon1pt, lat1pt, lon2pt, lat2pt)
print(points)
print(commands.getoutput('geod +ellps=clrk66 -f "%.3f" +n_S=5 ' + points))
print("from pyproj.Geod.npts:")
npts = 4
lonlats = g.npts(lon1pt, lat1pt, lon2pt, lat2pt, npts)
lonprev = lon1pt
latprev = lat1pt
print(dist / (npts + 1))
print("%6.3f  %7.3f" % (lat1pt, lon1pt))
for lon, lat in lonlats:
    az12, az21, dist = g.inv(lonprev, latprev, lon, lat)
    print("%6.3f  %7.3f %11.3f" % (lat, lon, dist))
    latprev = lat
    lonprev = lon
az12, az21, dist = g.inv(lonprev, latprev, lon2pt, lat2pt)
print("%6.3f  %7.3f %11.3f" % (lat2pt, lon2pt, dist))

# specify the lat/lons of some cities.
boston_lat = 42.0 + (15.0 / 60.0)
boston_lon = -71.0 - (7.0 / 60.0)
portland_lat = 45.0 + (31.0 / 60.0)
portland_lon = -123.0 - (41.0 / 60.0)
newyork_lat = 40.0 + (47.0 / 60.0)
newyork_lon = -73.0 - (58.0 / 60.0)
london_lat = 51.0 + (32.0 / 60.0)
london_lon = -(5.0 / 60.0)
g1 = Geod(ellps="clrk66")
cPickle.dump(g1, open("geod1.pickle", "wb"), -1)
g2 = Geod(ellps="WGS84")
cPickle.dump(g2, open("geod2.pickle", "wb"), -1)
az12, az21, dist = g1.inv(boston_lon, boston_lat, portland_lon, portland_lat)
print("distance between boston and portland, clrk66:")
print("%7.3f %6.3f %12.3f" % (az12, az21, dist))
print("distance between boston and portland, WGS84:")
az12, az21, dist = g2.inv(boston_lon, boston_lat, portland_lon, portland_lat)
print("%7.3f %6.3f %12.3f" % (az12, az21, dist))
print("testing pickling of Geod instance")
g3 = cPickle.load(open("geod1.pickle", "rb"))
g4 = cPickle.load(open("geod2.pickle", "rb"))
az12, az21, dist = g3.inv(boston_lon, boston_lat, portland_lon, portland_lat)
print("distance between boston and portland, clrk66 (from pickle):")
print("%7.3f %6.3f %12.3f" % (az12, az21, dist))
az12, az21, dist = g4.inv(boston_lon, boston_lat, portland_lon, portland_lat)
print("distance between boston and portland, WGS84 (from pickle):")
print("%7.3f %6.3f %12.3f" % (az12, az21, dist))
g3 = Geod("+ellps=clrk66")  # proj4 style init string
print("inverse transform")
print("from proj.4 invgeod:")
print(
    commands.getoutput(
        "echo \"42d15'N 71d07'W 45d31'N 123d41'W\" | geod +ellps=clrk66 -I -f \"%.3f\""
    )
)
print("from pyproj.Geod.inv:")
az12, az21, dist = g3.inv(lon1pt, lat1pt, lon2pt, lat2pt)
print("%7.3f %6.3f %12.3f" % (az12, az21, dist))
