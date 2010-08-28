import commands
from pyproj import Proj, transform
p1 = Proj(proj='latlong',datum='WGS84')
s_1 = -111.5
s_2 = 45.25919444444
p2 = Proj(proj="utm",zone=10,datum='NAD27')
cstr='echo "-111.5 45.25919444444" | cs2cs +proj=latlong +datum=WGS84 +to '+\
     '+proj=utm +zone=10 +datum=NAD27 -f "%.12f"'
print 'test datum shift (requires cs2cs proj4 command line tool)'
x1,y1,z1 = tuple( [float(x) for x in commands.getoutput(cstr).split()] )
x2,y2 = transform(p1, p2, s_1, s_2)
print 'is',x1,y1,'=',x2,y2,'?'
print '%12.3f,%12.3f' % (x1,y1) == '%12.3f,%12.3f' % (x2,y2)
