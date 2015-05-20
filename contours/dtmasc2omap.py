
import os
import re
import numpy as np
import matplotlib.pyplot as pyplot
import matplotlib._cntr as cntr
import sys
import inspect
import argparse
from scipy import ndimage
from scipy import io as spio

omap_folder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile(inspect.currentframe() ))[0],"../omap")))
if omap_folder not in sys.path:
	sys.path.insert(0, omap_folder)
import omap

DTMCRScode = 'epsg:27700' #OSGB 1936 / British National Grid
OMAPCRScode = 'epsg:32631' #WGS 84 / UTM zone 31N
outFileName = 'test.xmap'

tilesize = 1000
resolution = 0.5
minclen = 40
cavgspan = 30
grad_smooth_win = 21
csmooth_max = 151 #Maximum smoothing window for contours
gradientFactor = 20E-3 #Higher for more smoothing
cwin_max = csmooth_max//2

eastlconv = {'A':0,'B':1,'C':2,'D':3,'E':3,'F':0,'G':1,'H':2,'J':3,'K':3,'L':0,'M':1,'N':2,'O':3,'P':3,'Q':0,'R':1,'S':2,'T':3,'U':3,'V':0,'W':1,'X':2,'Y':3,'Z':3}
northlconv = {'A':4,'B':4,'C':4,'D':4,'E':4,'F':3,'G':3,'H':3,'J':3,'K':3,'L':2,'M':2,'N':2,'O':2,'P':2,'Q':1,'R':1,'S':1,'T':1,'U':1,'V':0,'W':0,'X':0,'Y':0,'Z':0}
gborigin = [1000000,500000]

parser = argparse.ArgumentParser()
parser.add_argument('--input','-i',nargs=1,default=['DTM'],type=str,help='Path to folder containing LIDAR data')
parser.add_argument('--UTMorigin','-U',nargs=2,type=float,help='Origin of the map in UTM coordinates')
parser.add_argument('--output','-o',nargs=1,default=['test.xmap'],type=str,help='Name of the output file')
parser.add_argument('--helper','-H',nargs=1,default=[0],type=int,help='Number of helper contours to between each contour')
parser.add_argument('--datum','-d',nargs=1,default=[0.0],type=float,help='Height datum offset for contours')
parser.add_argument('--idatum','-D',nargs=1,default=[0],type=int,help='Height datum offset for index contours as an integer number of standard contours')
parser.add_argument('--index','-x',nargs=1,default=[0],type=int,help='Number of contours between index contours')
parser.add_argument('--interval','-c',nargs=1,default=[5.0],type=float,help='Contour interval')
parser.add_argument('--add_unfiltered','-u',action='store_true',default=False,help='Add unfiltered contours')
cargs = parser.parse_args()

files = os.listdir(cargs.input[0])
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

x = np.arange(maporigin[0], maporigin[0]+mapsize[0], resolution)
y = np.arange(maporigin[1], maporigin[1]+mapsize[1], resolution)
x,y = np.meshgrid(x,y)
z = np.zeros_like(x,dtype=np.float)

for (dtmfile, east, north) in zip(dtmfiles, easts, norths):
	print('Reading '+dtmfile)
	ieast = int((east-maporigin[0])/resolution)
	inorth = int((north-maporigin[1])/resolution)
	
	z[inorth:inorth+tilesize,ieast:ieast+tilesize] = np.flipud(np.genfromtxt(cargs.input[0] + '/' + dtmfile,dtype=np.float,delimiter=' ',skip_header=6))

#Calculate contour levels
cint = cargs.interval[0]
datum = cargs.datum[0] % cint	#Apply modulo cint to datum to get a contour offset
hrange = [np.amin(z), np.amax(z)]

contourLevels = {}

#Generate helper contour levels
if (cargs.helper[0] > 0):
	hint = cint/cargs.helper[0]
	hheights = np.arange(np.floor(hrange[0]/hint)*hint+datum, np.ceil(hrange[1]/hint)*hint+datum, hint)
	contourLevels.update({h:'101.1' for h in hheights})

#Generate normal contours (overwrite helper contours)	
cheights = np.arange(np.floor(hrange[0]/cint)*cint+datum, np.ceil(hrange[1]/cint)*cint+datum, cint)
contourLevels.update({c:'101' for c in cheights})

#Generate index contours (overwrite normal contours)
if (cargs.index[0] > 0):
	iint = cint*cargs.index[0]
	idatum = datum+cargs.idatum[0]*cint #Datum for index contours is main datum + a number of normal contour intervals
	iheights = np.arange(np.floor(hrange[0]/iint)*iint+idatum, np.ceil(hrange[1]/iint)*iint+idatum, iint)
	contourLevels.update({i:'102' for i in iheights})

#Set up contour class
contourdata = cntr.Cntr(x, y, z)

#Calculate window size map
grad = np.gradient(z)
grad = (grad[0]**2+grad[1]**2)**0.5
grad = ndimage.uniform_filter(grad,size=grad_smooth_win)
grad[grad==0] = 0.001
wsize = gradientFactor*cwin_max/grad
wsize[wsize>cwin_max] = cwin_max

#Initialise output
cOMAP = omap.omap(map_type='contour');
cOMAP.setGMLCRS(DTMCRScode)
cOMAP.setOMAPCRS(OMAPCRScode)

w = np.ones(cavgspan,'d')/cavgspan

for cheight in contourLevels:
	clist = contourdata.trace(cheight, cheight, 0)
	clist = clist[:len(clist)//2]
	print('Processing '+str(cheight)+'m contours as symbol '+contourLevels[cheight])
	
	for contour in clist:
		clen = np.shape(contour)[0]
		if  clen >= minclen:	#Check contour is longer than minimum length
			scontour = np.zeros_like(contour)	#Allocate output contour
			if np.linalg.norm(contour[0,:]-contour[-1,:]) > 1.0: #Is contour open?
				#Calculate the maximum smoothing window (limited by contour length)
				maxwin_c = min(cwin_max,clen)
				
				#Extend contour by reflecting ends
				xcontour = np.r_[2*contour[0,:]-contour[maxwin_c-1:0:-1,:],contour,2*contour[-1,:]-contour[-1:-maxwin_c:-1,:]]
				
				#Iterate over the original vectors
				for i in range(maxwin_c,maxwin_c+clen):
					#Find window size at this location in the map
					wsize_idx = np.int32((xcontour[i,:]-maporigin)/resolution)
					winsize_i = min(maxwin_c,wsize[wsize_idx[1],wsize_idx[0]])
					#Find mean over given window
					scontour[i-maxwin_c,:]=np.mean(xcontour[i-winsize_i:i+winsize_i,:],0)
					
			
			else:	#Contour is closed
				#Calculate the maximum smoothing window (limited by contour length)
				maxwin_c = min(cwin_max,clen-1)
				
				#Extend contour by looping ends
				xcontour = np.r_[contour[-maxwin_c:-1,:],contour[0:-1,:],contour[0:maxwin_c,:]]
				
				x = np.r_[contour[-cavgspan:,0],contour[:,0],contour[0:cavgspan-1,0]]
				y = np.r_[contour[-cavgspan:,1],contour[:,1],contour[0:cavgspan-1,1]]
								
				#Iterate over the original vectors
				for i in range(maxwin_c,maxwin_c+clen):
					#Find window size at this location in the map
					wsize_idx = np.int32((xcontour[i,:]-maporigin)/resolution)
					winsize_i = min(maxwin_c,wsize[wsize_idx[1],wsize_idx[0]])
					#Find mean over given window
					scontour[i-maxwin_c,:]=np.mean(xcontour[i-winsize_i:i+winsize_i,:],0)
					
				
			cOMAP.addLine(scontour,contourLevels[cheight])
			
		if cargs.add_unfiltered:
			cOMAP.addLine(contour,'101.2')

try:
	cOMAP.setMapOrigin(UTM_origin=tuple([float(n) for n in cargs.UTMorigin]))
except NameError:
	cOMAP.setMapOrigin()
print('Writing '+cargs.output[0])
cOMAP.write(cargs.output[0])
