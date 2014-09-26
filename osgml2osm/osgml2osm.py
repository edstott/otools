
import xml.etree.ElementTree as ElementTree
import pyproj
import os
import sys
import inspect

OSMLayer_folder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile(inspect.currentframe() ))[0],"../OSMLayer")))
if OSMLayer_folder not in sys.path:
	sys.path.insert(0, OSMLayer_folder)	 
import OSMLayer

pointsize = 4.0
outdir = 'output'
bng = pyproj.Proj(init='epsg:27700')
wgs84 = pyproj.Proj(init='epsg:4326')

if len(sys.argv) > 1:
	gmlname = sys.argv[1]
else:
	gmlname = 'test.gml'

if not os.path.exists(outdir):
    os.makedirs(outdir)

srctree = ElementTree.parse(gmlname)
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
			typedict[code] = OSMLayer.OSMLayer(code,desctext)
			typedict[code].ftype = 'line'


		for polygon in linefeature.iter('{http://www.opengis.net/gml}coordinates'):
			typedict[code].addway(polygon.text.split())

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
			typedict[code] = OSMLayer.OSMLayer(code,desctext)
			typedict[code].ftype = 'point'


		for polygon in pointfeature.iter('{http://www.opengis.net/gml}coordinates'):
			typedict[code].addpoint(polygon.text.split(),pointsize)

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
			typedict[code] = OSMLayer.OSMLayer(code,desctext)
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
					wayid = typedict[code].addway(polyelem.text.split())
					rel.append(ElementTree.Element('member',{'type':'way','ref':str(wayid),'role':'outer'}))
					waycount += 1
		
		#Get inner polygons
		for inpoly in areafeature.iter('{http://www.opengis.net/gml}innerBoundaryIs'):
			ringelem = inpoly.find('{http://www.opengis.net/gml}LinearRing')
			if not ringelem == None:
				polyelem = ringelem.find('{http://www.opengis.net/gml}coordinates')
				if not polyelem == None:
					wayid = typedict[code].addway(polyelem.text.split())
					rel.append(ElementTree.Element('member',{'type':'way','ref':str(wayid),'role':'inner'}))	
					waycount += 1
					
		if waycount > 1:
			typedict[code].addrel(rel)
		
		


for layer in typedict:
	print typedict[layer].name, typedict[layer].ftype, typedict[layer].featurecount, 'items'
	typedict[layer].write()
	
