
import xml.etree.ElementTree as ElementTree
import pyproj

class OSMLayer:
	root = None
	bounds = None
	tree = None
	wayroot = None
	name = ''
	code = '0'
	featurecount = 0
	ftype = ''

	def __init__(self,code,name):
		self.root = ElementTree.Element('osm',{'version':'0.6','generator':'osgml2osm'})
		self.bounds = ElementTree.Element('bounds',{'minlat':'0','minlon':'0','maxlat':'0','maxlon':'0'})
		self.tree = ElementTree.ElementTree()
		self.wayroot = ElementTree.Element('osm')
		self.tree._setroot(self.root)
		self.root.append(self.bounds)
		self.code = code
		self.name = name

	def setbounds(self,maxlat,maxlon,minlat,minlon):
		self.bounds.set('maxlat',str(maxlat))
		self.bounds.set('minlat',str(minlat))
		self.bounds.set('maxlon',str(maxlon))
		self.bounds.set('minlon',str(minlon))

	def write(self):
		self.root.extend(self.wayroot)
		self.tree.write(self.code+'-'+self.ftype+'-'+self.name.replace(' ','_')+'.osm','UTF-8')
		
		
buildings = ('10021')
others = ('10185')

bng = pyproj.Proj(init='epsg:27700')
wgs84 = pyproj.Proj(init='epsg:4326')

srctree = ElementTree.parse('test.gml')
srcroot = srctree.getroot()
print srcroot.tag

idcount = 0
featurecount = 0
minlat = 180.0
maxlat = -180.0
minlon = 90.0
maxlon = -90.0
typedict = {}

for feature in srcroot.iter('{http://www.ordnancesurvey.co.uk/xml/namespaces/osgb}topographicMember'):
	featuretype = feature.find('{http://www.ordnancesurvey.co.uk/xml/namespaces/osgb}TopographicLine')
	ftype = 'line'
	if featuretype == None:
		featuretype = feature.find('{http://www.ordnancesurvey.co.uk/xml/namespaces/osgb}TopographicArea')
		ftype = 'area'
	if featuretype == None:
		break


	for desccode in featuretype.iter('{http://www.ordnancesurvey.co.uk/xml/namespaces/osgb}featureCode'):
		code = desccode.text
		if not code in typedict:
			desctype = featuretype.find('{http://www.ordnancesurvey.co.uk/xml/namespaces/osgb}descriptiveGroup')
			if not desctype == None:
				desctext = desctype.text
			else:
				desctext = 'none'
			typedict[code] = OSMLayer(code,desctext)
			typedict[code].ftype = ftype


		for polygon in featuretype.iter('{http://www.opengis.net/gml}coordinates'):
			nodelist = polygon.text.split()
			way = ElementTree.Element('way',{'id': str(idcount)})
			idcount += 1
			east = [float(i.split(',')[0]) for i in nodelist]
			north = [float(i.split(',')[1]) for i in nodelist]
			(lon,lat) = pyproj.transform(bng,wgs84,east,north)
			if max(lat)>maxlat:
				maxlat = max(lat)
			if min(lat)<minlat:
				minlat = min(lat)
			if max(lon)>maxlon:
				maxlon = max(lon)
			if min(lon)<minlon:
				minlon = min(lon)				

			for (x,y) in zip(lat,lon):
				typedict[code].root.append(ElementTree.Element('node',{'id':str(idcount), 'lat':str(x), 'lon':str(y)}))
				way.append(ElementTree.Element('nd',{'ref':str(idcount)}))
				idcount += 1
			
			typedict[code].wayroot.append(way)
			typedict[code].featurecount += 1

for layer in typedict:
	print typedict[layer].name, typedict[layer].featurecount, 'items'
	typedict[layer].setbounds(str(maxlat),str(maxlon),str(minlat),str(minlon))
	typedict[layer].write()
	
