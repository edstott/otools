
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
outFileName = 'test.xmap'

minclen = 25
grad_smooth_win = 11
csmooth_max = 301 #Maximum smoothing window for contours
gradientFactor = 6E-3 #Higher for more smoothing
cwin_max = csmooth_max//2


parser = argparse.ArgumentParser()
parser.add_argument('--input','-i',nargs=1,default=['DTM'],type=str,help='Path to folder containing LIDAR data')
parser.add_argument('--UTMorigin','-U',nargs=2,type=float,help='Origin of the map in UTM coordinates')
parser.add_argument('--output','-o',nargs=1,default=['test.xmap'],type=str,help='Name of the output file')
parser.add_argument('--helper','-H',nargs=1,default=[0],type=int,help='Number of helper contours to add between each contour')
parser.add_argument('--datum','-d',nargs=1,default=[0.0],type=float,help='Height datum offset for contours')
parser.add_argument('--idatum','-D',nargs=1,default=[0],type=int,help='Height datum offset for index contours as an integer number of standard contours')
parser.add_argument('--index','-x',nargs=1,default=[0],type=int,help='Number of contours between index contours')
parser.add_argument('--interval','-c',nargs=1,default=[5.0],type=float,help='Contour interval')
parser.add_argument('--add_unfiltered','-u',action='store_true',default=False,help='Add unfiltered contours')
parser.add_argument('--map_bounds','-b',nargs=4,type=float,help='Map bounds in UTM coordinates (W S E N)')
parser.add_argument('--UTMZone','-z',nargs=1,default=[30],type=int,help='UTM Zone of map (e.g 30)')
cargs = parser.parse_args()

files = os.listdir(cargs.input[0])
maptiles = []
bounds = [+np.inf,+np.inf,-np.inf,-np.inf]

#Initialise output
cOMAP = omap.omap(map_type='contour')
cOMAP.UTMZone = cargs.UTMZone[0]
cOMAP.setGMLCRS(init=DTMCRScode)
cOMAP.setOMAPCRS(proj='utm',zone=cargs.UTMZone[0],ellps='WGS84')

for file in files:
	m = re.match('([a-z])([a-z])(\d{2})(\d{2})_DTM_1m\.asc',file)
	if m:
		with open(os.path.join(cargs.input[0],file)) as mapfile:	#Find metadata for each data file
			metadata = {'filename':file}
			while True:
				line = mapfile.readline().strip().split()
				if len(line) > 2: #Break when we finish the header and reach the data
					break
				metadata[line[0]] = int(line[1])
			
			#Create bounds
			metadata['W_GB'] = metadata['xllcorner']
			metadata['S_GB'] = metadata['yllcorner']
			metadata['E_GB'] = metadata['xllcorner']+metadata['ncols']*metadata['cellsize']
			metadata['N_GB'] = metadata['yllcorner']+metadata['nrows']*metadata['cellsize']
			UTM_SW = cOMAP.convertToUTM((metadata['W_GB'],metadata['S_GB']))
			UTM_NE = cOMAP.convertToUTM((metadata['E_GB'],metadata['N_GB']))
			metadata['W_UTM'] = UTM_SW[0]
			metadata['S_UTM'] = UTM_SW[1]
			metadata['E_UTM'] = UTM_NE[0]
			metadata['N_UTM'] = UTM_NE[1]
			
			if cargs.map_bounds: #Check if file is within map bounds
				if (cargs.map_bounds[0]<UTM_NE[0]) & (cargs.map_bounds[1]<UTM_NE[1]) & (cargs.map_bounds[2]>UTM_SW[0]) & (cargs.map_bounds[3]>UTM_SW[1]):
					maptiles.append(metadata)
			else:
				maptiles.append(metadata)

if len(maptiles) == 0:
	print('No valid height map tiles')
	exit()
	
print (str(len(maptiles))+' tiles overlap the map')				
for tile in maptiles:
	if tile['W_GB'] < bounds[0]:
		bounds[0] = tile['W_GB']
	if tile['S_GB'] < bounds[1]:
		bounds[1] = tile['S_GB']
	if tile['E_GB'] > bounds[2]:
		bounds[2] = tile['E_GB']
	if tile['N_GB'] > bounds[3]:
		bounds[3] = tile['N_GB']
				
maporigin = (bounds[0],bounds[1])
mapsize = (bounds[2]-bounds[0],bounds[3]-bounds[1])
tilesize = maptiles[0]['ncols']
resolution = maptiles[0]['cellsize']

print ('OSGB origin: '+str(bounds[0])+','+str(bounds[1]))
print ('Contour map size: '+str(mapsize[0])+'x'+str(mapsize[1]))

x = np.arange(maporigin[0], maporigin[0]+mapsize[0], resolution)
y = np.arange(maporigin[1], maporigin[1]+mapsize[1], resolution)
x,y = np.meshgrid(x,y)
z = np.zeros_like(x,dtype=np.float)

for tile in maptiles:
	print('Reading '+tile['filename'])
	ieast = int((tile['W_GB']-maporigin[0])/resolution)
	inorth = int((tile['S_GB']-maporigin[1])/resolution)
	
	z[inorth:inorth+tilesize,ieast:ieast+tilesize] = np.flipud(np.genfromtxt(os.path.join(cargs.input[0],tile['filename']),dtype=np.float,delimiter=' ',skip_header=6))

#Calculate contour levels
cint = cargs.interval[0]
datum = cargs.datum[0] % cint	#Apply modulo cint to datum to get a contour offset
hrange = [np.amin(z), np.amax(z)]

contourLevels = {}

#Generate helper contour levels
if (cargs.helper[0] > 0):
	hint = cint/(cargs.helper[0]+1)
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
				maxwin_c = min(cwin_max,int(clen/4))
				
				#Extend contour by looping ends
				xcontour = np.r_[contour[-maxwin_c:-1,:],contour[0:-1,:],contour[0:maxwin_c,:]]
								
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

if cargs.UTMorigin:
	cOMAP.setMapOrigin(UTM_origin=tuple([float(n) for n in cargs.UTMorigin]))
else:
	cOMAP.setMapOrigin()
print('Writing '+cargs.output[0])
cOMAP.write(cargs.output[0])
