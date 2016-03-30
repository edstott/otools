
import os,inspect,sys
import argparse
import pyx
import np
import matplotlib._cntr as cntr

DEF_MAX_LAYERS = 15
PREF_INTERVALS = [1,2,5,7.5,10,15,20,25,50]
SCALE = 1.0/10000*(100)

lr_folder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile(inspect.currentframe() ))[0],"../contours")))
if lr_folder not in sys.path:
	sys.path.insert(0, lr_folder)
import lidarReader

parser = argparse.ArgumentParser()
parser.add_argument('--input','-i',nargs=1,default=['data'],type=str,help='Path to folder containing LIDAR data')
parser.add_argument('--map_bounds','-b',nargs=4,type=float,help='Map bounds in OS coordinates (W S E N)')
cargs = parser.parse_args()

if cargs.map_bounds:
	hdata = lidarReader.lidarReader(map_bounds=cargs.map_bounds)
else:
	hdata = lidarReader.lidarReader()
hdata.scanTiles(cargs.input[0])
z = hdata.createHMap()

np.savetxt("foo.csv", z, delimiter=",")

#Define contour levels
hlims = [np.amin(z), np.amax(z)]
hrange = np.ptp(z)
cint = max(PREF_INTERVALS)
layers = int(np.ceil(hrange/cint))
for try_i in PREF_INTERVALS:
	try_layers = int(np.ceil(hrange/try_i))
	if try_layers > layers and try_layers < DEF_MAX_LAYERS:
		cint = try_i
		layers = try_layers
print('{} layers. {}m interval'.format(layers,cint))
cheights = np.arange(np.floor(hlims[0]/cint)*cint, np.ceil(hlims[1]/cint)*cint, cint)

#Generate contours
contourdata = cntr.Cntr(hdata.x, hdata.y, z)

cvs = pyx.canvas.canvas()
cvs.text(0, 0, "Hello, world!")
cvs.stroke(pyx.path.line(0, 0, 2, 0))

for cheight in cheights:
	clist = contourdata.trace(cheight, cheight, 0)
	clist = clist[:len(clist)//2]
	print('Level {}m, {} contours'.format(cheight,len(clist)))
	for contour in clist:
		contour = contour*SCALE
		path = [pyx.path.moveto(*contour[0])] + [pyx.path.lineto(*c) for c in contour[1:]]
		cvs.stroke(pyx.path.path(*path))


cvs.writePDFfile('out')


