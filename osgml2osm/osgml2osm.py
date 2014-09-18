
import xml.etree.ElementTree as ElementTree
import pyproj
import os

outdir = 'output'
bng = pyproj.Proj(init='epsg:27700')
wgs84 = pyproj.Proj(init='epsg:4326')

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
		self.setbounds()
		self.root.extend(self.wayroot)
		self.root.extend(self.relroot)
		self.tree.write(outdir+'/'+self.code+'-'+self.ftype+'-'+self.name.replace(' ','_')+'.osm','UTF-8')
		
	def addway(self,polyelem):
		global idcount
		
		#Get coordinates
		nodelist = polyelem.text.split()
		east = [float(i.split(',')[0]) for i in nodelist]
		north = [float(i.split(',')[1]) for i in nodelist]
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
		
		

if not os.path.exists(outdir):
    os.makedirs(outdir)

srctree = ElementTree.parse('test.gml')
srcroot = srctree.getroot()
print srcroot.tag

idcount = 0
typedict = {}

#Look for line features
for linefeature in srcroot.iter('{http://www.ordnancesurvey.co.uk/xml/namespaces/osgb}TopographicLine'):

	#Get feature code
	codeelem = linefeature.find('{http://www.ordnancesurvey.co.uk/xml/namespaces/osgb}featureCode')
	if not codeelem == None:
		code = codeelem.text
		
		#Check if feature code has been seen before, create new layer tree if not
		if not code in typedict:
			desctype = linefeature.find('{http://www.ordnancesurvey.co.uk/xml/namespaces/osgb}descriptiveGroup')
			if not desctype == None:
				desctext = desctype.text
			else:
				desctext = 'none'
			typedict[code] = OSMLayer(code,desctext)
			typedict[code].ftype = 'line'


		for polygon in linefeature.iter('{http://www.opengis.net/gml}coordinates'):
			typedict[code].addway(polygon)

#Look for point features
for pointfeature in srcroot.iter('{http://www.ordnancesurvey.co.uk/xml/namespaces/osgb}TopographicPoint'):

	#Get feature code
	codeelem = pointfeature.find('{http://www.ordnancesurvey.co.uk/xml/namespaces/osgb}featureCode')
	if not codeelem == None:
		code = codeelem.text
		
		#Check if feature code has been seen before, create new layer tree if not
		if not code in typedict:
			desctype = pointfeature.find('{http://www.ordnancesurvey.co.uk/xml/namespaces/osgb}descriptiveGroup')
			if not desctype == None:
				desctext = desctype.text
			else:
				desctext = 'none'
			typedict[code] = OSMLayer(code,desctext)
			typedict[code].ftype = 'point'


		for polygon in pointfeature.iter('{http://www.opengis.net/gml}coordinates'):
			typedict[code].addway(polygon)

#Look for area features
for areafeature in srcroot.iter('{http://www.ordnancesurvey.co.uk/xml/namespaces/osgb}TopographicArea'):
	
	#Get feature code
	codeelem = areafeature.find('{http://www.ordnancesurvey.co.uk/xml/namespaces/osgb}featureCode')
	if not codeelem == None:
		code = codeelem.text
		
		#Check if feature code has been seen before, create new layer tree if not
		if not code in typedict:
			desctype = areafeature.find('{http://www.ordnancesurvey.co.uk/xml/namespaces/osgb}descriptiveGroup')
			if not desctype == None:
				desctext = desctype.text
			else:
				desctext = 'none'
			typedict[code] = OSMLayer(code,desctext)
			typedict[code].ftype = 'area'
			
		rel = ElementTree.Element('relation',{'id': str(idcount)})
		rel.append(ElementTree.Element('tag',{'k':'type','v':'multipolygon'}))
		idcount += 1
		waycount = 0

		#Get outer polygons
		for outpoly in areafeature.iter('{http://www.opengis.net/gml}outerBoundaryIs'):
			ringelem = outpoly.find('{http://www.opengis.net/gml}LinearRing')
			if not ringelem == None:
				polyelem = ringelem.find('{http://www.opengis.net/gml}coordinates')
				if not polyelem == None:
					wayid = typedict[code].addway(polyelem)
					rel.append(ElementTree.Element('member',{'type':'way','ref':str(wayid),'role':'outer'}))
					waycount += 1
		
		#Get inner polygons
		for inpoly in areafeature.iter('{http://www.opengis.net/gml}innerBoundaryIs'):
			ringelem = inpoly.find('{http://www.opengis.net/gml}LinearRing')
			if not ringelem == None:
				polyelem = ringelem.find('{http://www.opengis.net/gml}coordinates')
				if not polyelem == None:
					wayid = typedict[code].addway(polyelem)
					rel.append(ElementTree.Element('member',{'type':'way','ref':str(wayid),'role':'inner'}))	
					waycount += 1
					
		if waycount > 1:
			typedict[code].addrel(rel)
		
		


for layer in typedict:
	print typedict[layer].name, typedict[layer].ftype, typedict[layer].featurecount, 'items'
	typedict[layer].write()
	
