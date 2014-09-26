import xml.etree.ElementTree as ElementTree
import pyproj
import os
import numpy

bng = pyproj.Proj(init='epsg:27700')
wgs84 = pyproj.Proj(init='epsg:4326')
idcount = 0
outdir = 'output'

class OSMLayer:
	root = None
	bounds = None
	tree = None
	wayroot = None
	relroot = None
	name = ''
	code = '0'
	featurecount = 0
	ftype = ''
	minlat = 180.0
	maxlat = -180.0
	minlon = 90.0
	maxlon = -90.0

	def __init__(self,code,name):
		self.root = ElementTree.Element('osm',{'version':'0.6','generator':'osgml2osm'})
		self.bounds = ElementTree.Element('bounds',{'minlat':'0','minlon':'0','maxlat':'0','maxlon':'0'})
		self.tree = ElementTree.ElementTree()
		self.wayroot = ElementTree.Element('osm')
		self.relroot = ElementTree.Element('osm')
		self.tree._setroot(self.root)
		self.root.append(self.bounds)
		self.code = code
		self.name = name

	def setbounds(self):
		self.bounds.set('maxlat',str(self.maxlat))
		self.bounds.set('minlat',str(self.minlat))
		self.bounds.set('maxlon',str(self.maxlon))
		self.bounds.set('minlon',str(self.minlon))

	def write(self):
		if not os.path.exists(outdir):
			os.makedirs(outdir)
		self.setbounds()
		self.root.extend(self.wayroot)
		self.root.extend(self.relroot)
		self.tree.write(outdir+'/'+self.code+'-'+self.ftype+'-'+self.name.replace(' ','_')+'.osm','UTF-8')
		
	def addway(self,polyelem):
		global idcount
		
		#Get coordinates
		if type(polyelem) is list:
			east = [float(i.split(',')[0]) for i in polyelem]
			north = [float(i.split(',')[1]) for i in polyelem]
		else:
			east = polyelem[:,0]
			north = polyelem[:,1]
		
		(lon,lat) = pyproj.transform(bng,wgs84,east,north)
		
		if max(lat)>self.maxlat:
			self.maxlat = max(lat)
		if min(lat)<self.minlat:
			self.minlat = min(lat)
		if max(lon)>self.maxlon:
			self.maxlon = max(lon)
		if min(lon)<self.minlon:
			self.minlon = min(lon)
		
		#Create a new way element
		way = ElementTree.Element('way',{'id': str(idcount)})
		wayid = idcount
		idcount += 1
	
		for (x,y) in zip(lat,lon):
			self.root.append(ElementTree.Element('node',{'id':str(idcount), 'lat':str(x), 'lon':str(y)}))
			way.append(ElementTree.Element('nd',{'ref':str(idcount)}))
			idcount += 1
	
		self.wayroot.append(way)
		self.featurecount += 1
		return wayid
			
	def addrel(self,rel):
		self.relroot.append(rel)
		
	def addpoint(self,point,size):
		global idcount
		size = size/2.0
		if type(point) is list:
			east = float(point[0].split(',')[0])
			north = float(point[0].split(',')[1])
		else:
			east = point[0]
			north = point[1]
		
		self.addway(numpy.array([[east-size, north], [east+size, north]]))
		self.addway(numpy.array([[east, north-size], [east, north+size]]))
		
		