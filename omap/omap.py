from xml.dom.minidom import getDOMImplementation,parse
import pyproj
import math
import os
import numpy

DEFAULT_MAP_UNITS = 1E-6
DEFAULT_MAP_SCALE = 5000
DEFAULT_UTM_ZONE = 31
DEFAULT_CRS = 'epsg:32631' #WGS 84 / UTM zone 31N
GEO_CRS = 'epsg:4326' #WGS 84
MODULE_PATH = os.path.dirname(__file__)
#ISSOM_SYMBOLS_FILE = os.path.join(MODULE_PATH,'ISSOM_symbols.xml')
#ISSOM_COLOURS_FILE = os.path.join(MODULE_PATH,'ISSOM_colours.xml')
#CONTOUR_SYMBOLS_FILE = os.path.join(MODULE_PATH,'contour_symbols.xml')
#CONTOUR_COLOURS_FILE = os.path.join(MODULE_PATH,'contour_colours.xml')
OMAP_DEFAULTS_FILE = os.path.join(MODULE_PATH,'OMAP_defaults.xml')

mapTypes = {'ISSOM':('ISSOM_colours.xml','ISSOM_symbols.xml'),
	'contour':('ISSOM_colours.xml','contour_symbols.xml')}

DOMimpl = getDOMImplementation()

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

class omap:
	originX = 0
	originY = 0
	grivation = 0.0
	
	mapUnits = DEFAULT_MAP_UNITS
	mapScale = DEFAULT_MAP_SCALE
	symbolMap = {}

	def __init__(self,**kwargs):
		
		if ('map_type' in kwargs):
			try:
				(coloursFile,symbolsFile) = mapTypes[kwargs['map_type']]
			except KeyError:
				print('Bad map type given')
				raise
		else:
			(coloursFile,symbolsFile) = mapTypes['ISSOM']
	
		self.doc = DOMimpl.createDocument(None,"map",None)
		self.mapNode = self.doc.documentElement
		self.mapNode.setAttribute('xmlns','http://oorienteering.sourceforge.net/mapper/xml/v2')
		self.mapNode.setAttribute('version','5')
		
		self.mapNode.appendChild(self.doc.createElement('notes'))
		
		#Create georeferencing information
		self.initGeoreference()
		self.OMAPCRS = None
		self.geoCRS = pyproj.Proj(init=GEO_CRS)
		
		#Create colours
		colourDoc = parse(os.path.join(MODULE_PATH,coloursFile))
		self.mapNode.appendChild(colourDoc.documentElement)
		
		#Create symbols
		symbolDoc = parse(os.path.join(MODULE_PATH,symbolsFile))
		for symbolNode in symbolDoc.documentElement.getElementsByTagName('symbol'):
			symbolID = symbolNode.getAttribute('id')
			symbolCode = symbolNode.getAttribute('code')
			self.symbolMap[symbolCode] = symbolID
		self.mapNode.appendChild(symbolDoc.documentElement)
		
		#Create parts
		partsNode = self.doc.createElement('parts')
		partsNode.setAttribute('current','0')
		partsNode.setAttribute('count','1')
		self.mapNode.appendChild(partsNode)
		
		partNode = self.doc.createElement('part')
		partNode.setAttribute('name','default part')
		partsNode.appendChild(partNode)
		
		self.objectsNode = self.doc.createElement('objects')
		self.objectsNode.setAttribute('count','0')
		partNode.appendChild(self.objectsNode)
		
		#Create templates, view, print, barrier
		defaultsDoc = parse(OMAP_DEFAULTS_FILE)
		for defaultsNode in defaultsDoc.documentElement.childNodes:
			self.mapNode.appendChild(defaultsNode.cloneNode(deep=1))
		
		
	def setGMLCRS(self,**kwargs):
		self.GMLCRS = pyproj.Proj(**kwargs)
		print('Setting source CRS with Proj parameters')
		print(kwargs)
		
	def setOMAPCRS(self,**kwargs):
		self.OMAPCRS = pyproj.Proj(**kwargs)
		print('Setting map CRS with Proj parameters')
		print(kwargs)
		
	#Set the map origin to the south west corner of bounding box
	def setMapOrigin(self,**kwargs):
	
		#Convert new origin to map units
		if 'UTM_origin' in kwargs:
			newOrigin = kwargs['UTM_origin']
			NewOriginX = newOrigin[0]/(self.mapScale*self.mapUnits)-self.originX
			NewOriginY = -newOrigin[1]/(self.mapScale*self.mapUnits)-self.originY
		else: #Find new origin from bounding box if none is given
		
			NewOriginX = float('Inf')
			NewOriginY = -float('Inf')
	
			#Find offset of each coordinate from current origin
			for coordsNode in self.objectsNode.getElementsByTagName('coords'):
				for coordNode in coordsNode.childNodes:
					if float(coordNode.getAttribute('x')) < NewOriginX:
						NewOriginX = float(coordNode.getAttribute('x'))
					if float(coordNode.getAttribute('y')) > NewOriginY:
						NewOriginY = float(coordNode.getAttribute('y'))
				
		if NewOriginX < float('Inf') and NewOriginY > -float('Inf'):
			
			#Calculate new origin
			self.originX += NewOriginX*self.mapScale*self.mapUnits
			self.originY -= NewOriginY*self.mapScale*self.mapUnits
			self.projRefPointNode.setAttribute('x',str(self.originX))
			self.projRefPointNode.setAttribute('y',str(self.originY))
			
			#Calculate new geographic origin
			(lon,lat) = pyproj.transform(self.OMAPCRS,self.geoCRS,self.originX,self.originY)
			self.geoRefPointDegNode.setAttribute('lon',str(lon))
			self.geoRefPointDegNode.setAttribute('lat',str(lat))
			self.geoRefPointNode.setAttribute('lon',str(lon*math.pi/180))
			self.geoRefPointNode.setAttribute('lat',str(lat*math.pi/180))
			print('Setting map origin to '+str(lat)+'N '+str(lon)+'E')

			#Calculate grid convergence
			relLon = (self.UTMZone-30.5)*math.pi/30 - math.radians(lon)
			self.grivation = math.atan(math.tan(relLon)*math.sin(math.radians(lat)))
			print('Rotating map for grid convergence '+str(math.degrees(self.grivation))+chr(0x00B0))
			self.geoRefNode.setAttribute('grivation',str(math.degrees(self.grivation)))
			
			#Calculate rotation coefficients
			rota = math.cos(-self.grivation)
			rotb = math.sin(-self.grivation)
		
			for coordsNode in self.objectsNode.getElementsByTagName('coords'):
				for coordNode in coordsNode.childNodes:
					x = float(coordNode.getAttribute('x'))-NewOriginX
					y = float(coordNode.getAttribute('y'))-NewOriginY
					coordNode.setAttribute('x',str(int(rota*x-rotb*y)))
					coordNode.setAttribute('y',str(int(rota*y+rotb*x)))
			
	def addLine(self,Line,ISSOMCode):
	
		#Check ISSOMCode given
		if ISSOMCode == '':
			print('No ISSOM code given')
			return
		if not ISSOMCode in self.symbolMap:
			print('No symbol for ISSOM code '+ISSOMCode)
			return
		
		#Initialise node for new line
		objNode = self.doc.createElement('object')
		objNode.setAttribute('symbol',self.symbolMap[ISSOMCode])
		coordsNode = self.doc.createElement('coords')
		objNode.appendChild(coordsNode)
		
		#Add Line
		objNode.setAttribute('type','1')
		coordNodes = self.convertLine(Line)
		for coordNode in coordNodes:
				coordsNode.appendChild(coordNode)
		coordsNode.setAttribute('count',str(len(coordNodes)))
		objNode.appendChild(self.blankPatternNode())
		
		#Add to objects
		self.objectsNode.appendChild(objNode)
		
		#Increment object count
		self.objectsNode.setAttribute('count',str(int(self.objectsNode.getAttribute('count'))+1))		
		
	
	def addGMLObjects(self,GMLObjects,ISSOMCode):
		objcount = 0
		for GMLnode in GMLObjects:
			if ISSOMCode == '':
				print('No ISSOM code given')
				print(GMLnode.toxml())
				continue
			if not ISSOMCode in self.symbolMap:
				print('No symbol for ISSOM code '+ISSOMCode)
				break
			objNode = self.doc.createElement('object')
			objNode.setAttribute('symbol',self.symbolMap[ISSOMCode])
			coordsNode = self.doc.createElement('coords')
			objNode.appendChild(coordsNode)
			
			if GMLnode.tagName == 'gml:Point':
				coordsNode.setAttribute('count','1')
				objNode.setAttribute('type','0')
				coordsNode.appendChild(self.convertGMLcoords(GMLnode)[0])
				objNode.appendChild(coordsNode)
				
			elif GMLnode.tagName == 'gml:Polygon':
				coordCount = 0	
				objNode.setAttribute('type','1')
				outerCoordsNodes = self.convertGMLcoords(GMLnode.getElementsByTagName('gml:outerBoundaryIs')[0])			
				innerCoordsNodess = [self.convertGMLcoords(innerCoords) for innerCoords in  GMLnode.getElementsByTagName('gml:innerBoundaryIs')]
				for coordNode in outerCoordsNodes:
					coordsNode.appendChild(coordNode)
				coordCount += len(outerCoordsNodes)
				for innerCoordsNodes in innerCoordsNodess:
					coordCount += len(innerCoordsNodes)
					for coordNode in innerCoordsNodes:
						coordsNode.appendChild(coordNode)
				coordsNode.setAttribute('count',str(coordCount))
				objNode.appendChild(coordsNode)
				objNode.appendChild(self.blankPatternNode())
				
			else: #Line feature
				objNode.setAttribute('type','1')
				coordNodes = self.convertGMLcoords(GMLnode)
				for coordNode in coordNodes:
						coordsNode.appendChild(coordNode)
				coordsNode.setAttribute('count',str(len(coordNodes)))
				objNode.appendChild(coordsNode)
				objNode.appendChild(self.blankPatternNode())
			
			self.objectsNode.appendChild(objNode)
			objcount += 1
		
		self.objectsNode.setAttribute('count',str(int(self.objectsNode.getAttribute('count'))+objcount))
		return objcount
	
	def convertLine(self,line):
		coordNodes = []
		for xy in line:
			(UTMx,UTMy)=pyproj.transform(self.GMLCRS,self.OMAPCRS,float(xy[0]),float(xy[1]))
			x = int((UTMx-self.originX)/self.mapScale/self.mapUnits)
			y = -int((UTMy-self.originY)/self.mapScale/self.mapUnits)
					
			coordNode = self.doc.createElement('coord')
			coordNode.setAttribute('x',str(x))
			coordNode.setAttribute('y',str(y))
			coordNodes.append(coordNode)
		
		if numpy.linalg.norm(line[0,:]-line[-1,:]) < 1.0:
			coordNodes[-1].setAttribute('flags','18')
		
		return coordNodes
			
	
	def convertGMLcoords(self,GMLNode):
		coordNodes = []
		for GMLCoordNode in GMLNode.getElementsByTagName('gml:coordinates'):
			coords = getText(GMLCoordNode.childNodes).split(' ')
			for coord in coords:
				xy = coord.split(',')
				if len(xy)==2:
					(UTMx,UTMy)=pyproj.transform(self.GMLCRS,self.OMAPCRS,float(xy[0]),float(xy[1]))
					x = int((UTMx-self.originX)/self.mapScale/self.mapUnits)
					y = -int((UTMy-self.originY)/self.mapScale/self.mapUnits)
					
					coordNode = self.doc.createElement('coord')
					coordNode.setAttribute('x',str(x))
					coordNode.setAttribute('y',str(y))
					coordNodes.append(coordNode)
			if GMLCoordNode.parentNode.tagName == 'gml:LinearRing':
				coordNodes[-1].setAttribute('flags','18')
						
		return coordNodes	

			
	def getXML(self):
		return self.doc.toprettyxml(encoding='utf-8')
		
	def write(self,filename):
		xmapfile = open(filename,'wb')
		xmapfile.write(self.getXML())
		#self.mapNode.writexml(xmapfile)
		xmapfile.close()
	
	def initGeoreference(self):

		self.geoRefNode = self.doc.createElement('georeferencing')
		self.geoRefNode.setAttribute('scale',str(self.mapScale))
		self.geoRefNode.setAttribute('declination','0.00')
		self.geoRefNode.setAttribute('grivation','0.00')
		self.mapNode.appendChild(self.geoRefNode)
		
		self.mapRefPointNode = self.doc.createElement('ref_point')
		self.mapRefPointNode.setAttribute('x','0')
		self.mapRefPointNode.setAttribute('y','0')
		self.geoRefNode.appendChild(self.mapRefPointNode)
		
		projCRSNode = self.doc.createElement('projected_crs')
		projCRSNode.setAttribute('id','UTM')
		self.geoRefNode.appendChild(projCRSNode)
		
		self.projCRSSpecNode = self.doc.createElement('spec')
		self.projCRSSpecNode.setAttribute('language','PROJ.4')
		projCRSNode.appendChild(self.projCRSSpecNode)
		
		self.projCRSParamNode = self.doc.createElement('parameter')
		projCRSNode.appendChild(self.projCRSParamNode)
					
		self.projRefPointNode = self.doc.createElement('ref_point')
		projCRSNode.appendChild(self.projRefPointNode)
		
		geoCRSNode = self.doc.createElement('geographic_crs')
		geoCRSNode.setAttribute('id','Geographic coordinates')
		self.geoRefNode.appendChild(geoCRSNode)
		
		geoCRSSpecNode = self.doc.createElement('spec')
		geoCRSSpecNode.setAttribute('language','PROJ.4')
		geoCRSSpecNode.appendChild(self.doc.createTextNode('+proj=latlong +datum=WGS84'))
		geoCRSNode.appendChild(geoCRSSpecNode)
		
		self.geoRefPointNode = self.doc.createElement('ref_point')
		geoCRSNode.appendChild(self.geoRefPointNode)
		
		self.geoRefPointDegNode = self.doc.createElement('ref_point_deg')
		geoCRSNode.appendChild(self.geoRefPointDegNode)
		
	def updateGeoRef(self):
		self.geoRefPointDegNode.setAttribute('lat',str(self.originX))
		self.geoRefPointDegNode.setAttribute('lon',str(self.originY))
		self.geoRefPointNode.setAttribute('lat',str(self.originX))
		self.geoRefPointNode.setAttribute('lon',str(self.originY))
		self.projRefPointNode.setAttribute('x',str(self.originX))
		self.projRefPointNode.setAttribute('y',str(self.originY))
		self.projCRSParamNode.appendChild(self.doc.createTextNode(str(self.UTMZone)+' N'))
		self.projCRSSpecNode.appendChild(self.doc.createTextNode('+proj=utm +datum=WGS84 +zone='+str(self.UTMZone)))
		
	def blankPatternNode(self):
		patternNode = self.doc.createElement('pattern')
		patternNode.setAttribute('rotation','0')
		coordNode = self.doc.createElement('coord')
		coordNode.setAttribute('x','0')
		coordNode.setAttribute('y','0')
		patternNode.appendChild(coordNode)
		return patternNode
		
	def setUTMZoneFromCoord(self,node):
		coord = getText(node.childNodes).split(' ')[0].split(',')
		(lon,lat) = self.GMLCRS(float(coord[0]),float(coord[1]),inverse=True)
		self.UTMZone = math.floor((lon + 180)/6) + 1;
		print('UTM Zone '+str(self.UTMZone)+'N with meridian '+str((self.UTMZone-30.5)*6.0)+chr(0x00B0))
		self.setOMAPCRS(proj='utm',zone=self.UTMZone,ellps='WGS84')
		
		