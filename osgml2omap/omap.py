from xml.dom.minidom import getDOMImplementation,parse
import pyproj
import math

DEFAULT_MAP_UNITS = 1E-6
DEFAULT_MAP_SCALE = 5E3
DEFAULT_UTM_ZONE = 31
DEFAULT_CRS = 'epsg:2040'
GEO_CRS = 'epsg:4326'
ISSOM_SYMBOLS_FILE = 'ISSOM_symbols.xml'
ISSOM_COLOURS_FILE = 'ISSOM_colours.xml'

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
	UTMZone = DEFAULT_UTM_ZONE
	
	mapUnits = DEFAULT_MAP_UNITS
	mapScale = DEFAULT_MAP_SCALE
	symbolMap = {}

	def __init__(self):
		self.doc = DOMimpl.createDocument(None,"map",None)
		self.mapNode = self.doc.documentElement
		self.mapNode.setAttribute('xmlns','http://oorienteering.sourceforge.net/mapper/xml/v2')
		self.mapNode.setAttribute('version','5')
		
		self.mapNode.appendChild(self.doc.createElement('notes'))
		
		#Create georeferencing information
		self.initGeoreference()	
		self.OMAPCRS = pyproj.Proj(init=DEFAULT_CRS)
		self.geoCRS = pyproj.Proj(init=GEO_CRS)
		
		#Create colours
		colourDoc = parse(ISSOM_COLOURS_FILE)
		self.mapNode.appendChild(colourDoc.documentElement)
		
		#Create symbols
		symbolDoc = parse(ISSOM_SYMBOLS_FILE)
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
		
	def setGMLCRS(self,CRSdef):
		self.GMLCRS = pyproj.Proj(init=CRSdef)
		
	def setOMAPCRS(self,CRSdef):
		self.OMAPCRS = pyproj.Proj(init=CRSdef)
		
	#Set the map origin to the south west corner of bounding box
	def setMapOrigin(self):
		NewOriginX = float('Inf')
		NewOriginY = float('Inf')
	
		for coordNode in self.objectsNode.getElementsByTagName('coord'):
			if float(coordNode.getAttribute('x')) < NewOriginX:
				NewOriginX = float(coordNode.getAttribute('x'))
			if float(coordNode.getAttribute('y')) < NewOriginY:
				NewOriginY = float(coordNode.getAttribute('y'))
				
		if NewOriginX < float('Inf') and NewOriginX < float('Inf'):					
			for coordNode in self.objectsNode.getElementsByTagName('coord'):
				x = float(coordNode.getAttribute('x'))-NewOriginX
				y = float(coordNode.getAttribute('y'))-NewOriginY
				coordNode.setAttribute('x',str(x))
				coordNode.setAttribute('y',str(y))
				
			self.originX += NewOriginX*self.mapScale*self.mapUnits
			self.originY += NewOriginY*self.mapScale*self.mapUnits
			self.projRefPointNode.setAttribute('x',str(self.originX))
			self.projRefPointNode.setAttribute('y',str(self.originY))
			
			(lon,lat) = pyproj.transform(self.OMAPCRS,self.geoCRS,self.originX,self.originY)
			self.geoRefPointDegNode.setAttribute('lon',str(lon))
			self.geoRefPointDegNode.setAttribute('lat',str(lat))
			self.geoRefPointNode.setAttribute('lon',str(lon*math.pi/180))
			self.geoRefPointNode.setAttribute('lat',str(lat*math.pi/180))
			
			
	def addGMLObjects(self,GMLObjects,ISSOMCode):
		objcount = 0
		for GMLnode in GMLObjects:
			if not ISSOMCode in self.symbolMap:
				print('No symbol for code '+ISSOMCode)
				break
			objNode = self.doc.createElement('object')
			objNode.setAttribute('symbol',self.symbolMap[ISSOMCode])
			coordsNode = self.doc.createElement('coords')
			objNode.appendChild(coordsNode)
			
			if GMLnode.tagName == 'gml:Point':
				coordsNode.setAttribute('count','1')
				objNode.setAttribute('type','0')
				coordsNode.appendChild(self.convertGMLcoords(GMLnode)[0])
				
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
				
			else: #Line feature
				objNode.setAttribute('type','1')
				coordNodes = self.convertGMLcoords(GMLnode)
				for coordNode in coordNodes:
						coordsNode.appendChild(coordNode)
				coordsNode.setAttribute('count',str(len(coordNodes)))
			
			objNode.appendChild(coordsNode)
			self.objectsNode.appendChild(objNode)
			objcount += 1
		
		self.objectsNode.setAttribute('count',str(int(self.objectsNode.getAttribute('count'))+objcount))
			
	def convertGMLcoords(self,GMLNode):
		coordNodes = []
		for GMLCoordNode in GMLNode.getElementsByTagName('gml:coordinates'):
			coords = getText(GMLCoordNode.childNodes).split(' ')
			for coord in coords:
				xy = coord.split(',')
				if len(xy)==2:
					(UTMx,UTMy)=pyproj.transform(self.GMLCRS,self.OMAPCRS,float(xy[0]),float(xy[1]))
					x = (UTMx-self.originX)/self.mapScale/self.mapUnits
					y = (UTMy-self.originY)/self.mapScale/self.mapUnits
					
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

		geoRefNode = self.doc.createElement('georeferencing')
		geoRefNode.setAttribute('scale',str(self.mapScale))
		geoRefNode.setAttribute('declination','0.00')
		geoRefNode.setAttribute('grivation','0.00')
		self.mapNode.appendChild(geoRefNode)
		
		mapRefPointNode = self.doc.createElement('ref_point')
		mapRefPointNode.setAttribute('x','0')
		mapRefPointNode.setAttribute('y','0')
		geoRefNode.appendChild(mapRefPointNode)
		
		projCRSNode = self.doc.createElement('projected_crs')
		projCRSNode.setAttribute('id','UTM')
		geoRefNode.appendChild(projCRSNode)
		
		projCRSSpecNode = self.doc.createElement('spec')
		projCRSSpecNode.setAttribute('language','PROJ.4')
		projCRSSpecNode.appendChild(self.doc.createTextNode('+proj=utm +datum=WGS84 +zone='+str(self.UTMZone)))
		projCRSNode.appendChild(projCRSSpecNode)
		
		projCRSParamNode = self.doc.createElement('parameter')
		projCRSParamNode.appendChild(self.doc.createTextNode(str(self.UTMZone)+' N'))
		projCRSNode.appendChild(projCRSParamNode)
					
		self.projRefPointNode = self.doc.createElement('ref_point')
		self.projRefPointNode.setAttribute('x',str(self.originX))
		self.projRefPointNode.setAttribute('y',str(self.originY))
		projCRSNode.appendChild(self.projRefPointNode)
		
		geoCRSNode = self.doc.createElement('geographic_crs')
		geoCRSNode.setAttribute('id','Geographic coordinates')
		geoRefNode.appendChild(geoCRSNode)
		
		geoCRSSpecNode = self.doc.createElement('spec')
		geoCRSSpecNode.setAttribute('language','PROJ.4')
		geoCRSSpecNode.appendChild(self.doc.createTextNode('+proj=utm +datum=WGS84'))
		geoCRSNode.appendChild(geoCRSSpecNode)
		
		self.geoRefPointNode = self.doc.createElement('ref_point')
		self.geoRefPointNode.setAttribute('lat',str(self.originX))
		self.geoRefPointNode.setAttribute('lon',str(self.originY))
		geoCRSNode.appendChild(self.geoRefPointNode)
		
		self.geoRefPointDegNode = self.doc.createElement('ref_point_deg')
		self.geoRefPointDegNode.setAttribute('lat',str(self.originX))
		self.geoRefPointDegNode.setAttribute('lon',str(self.originY))
		geoCRSNode.appendChild(self.geoRefPointDegNode)
		
		