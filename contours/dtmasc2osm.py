
import os
import re
import numpy
import matplotlib.pyplot as pyplot
import matplotlib._cntr as cntr
import sys
import inspect

OSMLayer_folder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile(inspect.currentframe() ))[0],"../OSMLayer")))
if OSMLayer_folder not in sys.path:
	sys.path.insert(0, OSMLayer_folder)
import OSMLayer

if len(sys.argv) > 1:
	srcdir = sys.argv[1]
else:
	srcdir = 'DTM'

tilesize = 1000
resolution = 0.5
cint = 2.5
minclen = 40
cavgspan = 30

eastlconv = {'A':0,'B':1,'C':2,'D':3,'E':3,'F':0,'G':1,'H':2,'J':3,'K':3,'L':0,'M':1,'N':2,'O':3,'P':3,'Q':0,'R':1,'S':2,'T':3,'U':3,'V':0,'W':1,'X':2,'Y':3,'Z':3}
northlconv = {'A':4,'B':4,'C':4,'D':4,'E':4,'F':3,'G':3,'H':3,'J':3,'K':3,'L':2,'M':2,'N':2,'O':2,'P':2,'Q':1,'R':1,'S':1,'T':1,'U':1,'V':0,'W':0,'X':0,'Y':0,'Z':0}
gborigin = [1000000,500000]

files = os.listdir(srcdir)
dtmfiles = []
norths = []
easts = []
for file in files:
	m = re.match('([A-Z])([A-Z])(\d{2})(\d{2})([ns])([ew])_DTM_50CM\.asc',file)
	if m:
		dtmfiles.append(file)
		easts.append(eastlconv[m.group(1)]*500000 + eastlconv[m.group(2)]*100000 + int(m.group(3))*1000 + (m.group(6)=='e')*500 - gborigin[0])
		norths.append(northlconv[m.group(1)]*500000 + northlconv[m.group(2)]*100000 + int(m.group(4))*1000 + (m.group(5)=='n')*500 - gborigin[1])
		
maporigin = [min(easts),min(norths)]
mapsize = [max(easts)-maporigin[0]+tilesize*resolution,max(norths)-maporigin[1]+tilesize*resolution]

x = numpy.arange(maporigin[0], maporigin[0]+mapsize[0], resolution)
y = numpy.arange(maporigin[1], maporigin[1]+mapsize[1], resolution)
x,y = numpy.meshgrid(x,y)
z = numpy.zeros_like(x,dtype=numpy.float)

for (dtmfile, east, north) in zip(dtmfiles, easts, norths):
	print 'reading',dtmfile
	ieast = int((east-maporigin[0])/resolution)
	inorth = int((north-maporigin[1])/resolution)
	
	z[inorth:inorth+tilesize,ieast:ieast+tilesize] = numpy.flipud(numpy.genfromtxt(srcdir + '/' + dtmfile,dtype=numpy.float,delimiter=' ',skip_header=6))

hrange = [numpy.amin(z), numpy.amax(z)]
cheights = numpy.arange(numpy.ceil(hrange[0]/cint)*cint, numpy.ceil(hrange[1]/cint)*cint, cint)

contourdata = cntr.Cntr(x, y, z)

clayer = OSMLayer.OSMLayer('0','contour')
clayer.ftype = 'line'
w = numpy.ones(cavgspan,'d')/cavgspan

for cheight in cheights:
	clist = contourdata.trace(cheight, cheight, 0)
	clist = clist[:len(clist)//2]
	for contour in clist:
		if numpy.shape(contour)[0] >= minclen:
			if numpy.linalg.norm(contour[0,:]-contour[-1,:]) > 1.0:
				x = numpy.r_[2*contour[0,0]-contour[cavgspan-1:0:-1,0],contour[:,0],2*contour[-1,0]-contour[-1:-cavgspan:-1,0]]
				y = numpy.r_[2*contour[0,1]-contour[cavgspan-1:0:-1,1],contour[:,1],2*contour[-1,1]-contour[-1:-cavgspan:-1,1]]
				
				x=numpy.convolve(w,x,mode='same')
				y=numpy.convolve(w,y,mode='same')
				
				contour = numpy.transpose(numpy.vstack((x[cavgspan:-cavgspan+1],y[cavgspan:-cavgspan+1])))
			
			else:
				x = numpy.r_[contour[-cavgspan:,0],contour[:,0],contour[0:cavgspan-1,0]]
				y = numpy.r_[contour[-cavgspan:,1],contour[:,1],contour[0:cavgspan-1,1]]
								
				x=numpy.convolve(w,x,mode='same')
				y=numpy.convolve(w,y,mode='same')
				
				contour = numpy.transpose(numpy.vstack((x[cavgspan:-cavgspan+1],y[cavgspan:-cavgspan+1])))
				
				
			clayer.addway(contour)

clayer.name, clayer.ftype, clayer.featurecount, 'items'
clayer.write()