from itertools import count
import random, os, math

from pyproj import itransform, Proj, transform
import numpy as np

p1 = Proj(init='epsg:4326')
p2 = Proj(init='epsg:2100')

print 'List with tuples'
pts = [(23, 38), (24, 38), (24, 39)]

x2, y2 = transform(p1, p2, *zip(*pts)) # pyproj.transform
x1y1 = itransform(p1, p2, pts)

for xiyi , xj, yj in zip(x1y1, x2, y2):
	print xiyi , ' == ', (xj, yj)

print '2d numpy array of coordinates'
pts = np.array([(23, 38, 1), (24, 38, 0), (24, 39, 2)])

x2, y2, z2 = transform(p1, p2, *zip(*pts)) # pyproj.transform
x1y1z1 = itransform(p1, p2, pts)

for xiyizi, xj, yj, zj in zip(x1y1z1, x2, y2, z2):
	print xiyizi , ' == ', (xj, yj, zj)

print 'Read and write a file'
with open(os.path.join(os.path.dirname(__file__), 'itransform_coords.in.txt'),'r') as inf:
	
	coords_strings = (line.split() for line in inf)
	coords = ((float(x), float(y)) for x, y in coords_strings)
	transformed = itransform(p1, p2, coords)

	with open(os.path.join(os.path.dirname(__file__), 'itransform_coords.out.txt'),'w') as outf:
		for i, pt in enumerate(transformed):
			outf.write("Pt:%d, Coords:(%f, %f)\n" % (i, pt[0], pt[1]))



# def test_random(pt_num):
# 	pt_gen = ((random.uniform(23,29), random.uniform(34,40)) for i in xrange(10000))
# 	for pt2 in itransform(p1, p2, pt_gen):
# 		x1, y1 = pt2

# if __name__ == '__main__':
#     import timeit
#     print(timeit.timeit("test_random(10)", setup="from __main__ import test_random", number=1000))
