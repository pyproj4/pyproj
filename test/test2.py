"""run test.py first!"""
from pyproj import Proj
import time, cPickle
import numpy as N

nx = 349
ny = 277
dx = 32463.41
dy = dx
print("do it again, from pickled instance ...")
# find 4 lon/lat crnrs of AWIPS grid 221.
llcrnrx = 0.0
llcrnry = 0.0
lrcrnrx = dx * (nx - 1)
lrcrnry = 0.0
ulcrnrx = 0.0
ulcrnry = dy * (ny - 1)
urcrnrx = dx * (nx - 1)
urcrnry = dy * (ny - 1)
dx = (urcrnrx - llcrnrx) / (nx - 1)
dy = (urcrnry - llcrnry) / (ny - 1)
x = llcrnrx + dx * N.indices((ny, nx), "f")[1, :, :]
y = llcrnry + dy * N.indices((ny, nx), "f")[0, :, :]
awips221 = cPickle.load(open("test.pickle", "rb"))
t1 = time.clock()
lons, lats = awips221(x, y, inverse=True, radians=True)
t2 = time.clock()
print("compute lats/lons for all points on AWIPS 221 grid (%sx%s)" % (nx, ny))
print("max/min lons in radians")
print(N.minimum.reduce(N.ravel(lons)), N.maximum.reduce(N.ravel(lons)))
print("max/min lats in radians")
print(N.minimum.reduce(N.ravel(lats)), N.maximum.reduce(N.ravel(lats)))
print("took", t2 - t1, "secs")
# reverse transformation.
t1 = time.clock()
xx, yy = awips221(lons, lats, radians=True)
t2 = time.clock()
print("max abs error for x")
print(N.maximum.reduce(N.fabs(N.ravel(x - xx))))
print("max abs error for y")
print(N.maximum.reduce(N.fabs(N.ravel(y - yy))))
print("took", t2 - t1, "secs")
