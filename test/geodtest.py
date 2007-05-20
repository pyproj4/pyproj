from pyproj import Geod
import commands
g = Geod(ellps='clrk66')
lat1pt = 42.+(15./60.)
lon1pt = -71.-(7./60.)
lat2pt = 45.+(31./60.)
lon2pt = -123.-(41./60.)
print lat1pt,lon1pt,lat2pt,lon2pt
print 'inverse transform'
print 'from proj.4 invgeod:'
print commands.getoutput('echo "42d15\'N 71d07\'W 45d31\'N 123d41\'W" | geod +ellps=clrk66 -I -f "%.3f"')
print 'from pyproj._Geod._inv:'
az12,az21,dist = g.inv(lon1pt,lat1pt,lon2pt,lat2pt)
print "%7.3f %6.3f %12.3f" % (az12,az21,dist)
print 'forward transform'
print 'from proj.4 geod:'
print commands.getoutput('echo "42d15\'N 71d07\'W -66d31\'50.141 4164192.708" | geod +ellps=clrk66 -f "%.3f"')
endlon,endlat,backaz = g.fwd(lon1pt,lat1pt,az12,dist)
print 'from pyproj._Geod._fwd:'
print "%6.3f  %6.3f %13.3f" % (endlat,endlon,backaz)
print 'intermediate points:'
print 'from geod with +lat_1,+lon_1,+lat_2,+lon_2,+n_S:'
points = '+lon_1=%s +lat_1=%s +lon_2=%s +lat_2=%s' % (lon1pt,lat1pt,lon2pt,lat2pt,)
print points
print commands.getoutput('geod +ellps=clrk66 -f "%.3f" +n_S=5 '+points)
print 'from pyproj._Geod._npts:'
npts = 4
lonlats = g.npts(lon1pt,lat1pt,lon2pt,lat2pt,npts)
lonprev = lon1pt
latprev = lat1pt
print dist/(npts+1)
print '%6.3f  %7.3f' % (lat1pt, lon1pt)
for lon, lat in lonlats:
    az12,az21,dist = g.inv(lonprev,latprev,lon,lat)
    print '%6.3f  %7.3f %11.3f' % (lat, lon, dist)
    latprev = lat; lonprev = lon
az12,az21,dist = g.inv(lonprev,latprev,lon2pt,lat2pt)
print '%6.3f  %7.3f %11.3f' % (lat2pt, lon2pt, dist)

# should raise exception (antipodal point)
try:
    print 'testing antipodal point, should raise exception ...'
    az12,az21,dist = g.inv(0.,90.,0.,-90.,0.)
except ValueError:
    print 'OK'
else:
    print 'not OK, no exception raised!'

# should raise exception (equatorial arc)
try:
    print 'testing equatorial arc, should raise execption ...'
    az12,az21,dist = g.inv(180.,0.0,200.,0.)
    endlon,endlat,backaz = g.fwd(180.,0.0,az12,0.)
except ValueError:
    print 'OK'
else:
    print 'not OK, no exception raised!'
