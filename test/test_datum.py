import commands
from pyproj import Proj, transform
p1 = Proj(proj='latlong',datum='WGS84')
s_1 = -111.5
s_2 = 45.25919444444
p2 = Proj(proj="utm",zone=10,datum='NAD27')
#cstr='echo "-111.5 45.25919444444" | cs2cs +proj=latlong +to '+\
cstr='echo "-111.5 45.25919444444" | /opt/local/bin/cs2cs -v +proj=latlong +datum=WGS84 +to '+\
     '+proj=utm +zone=10 +datum=NAD27 -f "%.12f"'
print commands.getoutput(cstr)
print transform(p1, p2, s_1, s_2)
