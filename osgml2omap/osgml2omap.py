#!/usr/bin/python

from xml.dom import pulldom
import sys,os,inspect
import OS_ISSOM_MAP

omap_folder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile(inspect.currentframe() ))[0],"../omap")))
if omap_folder not in sys.path:
	sys.path.insert(0, omap_folder)
import omap

GMLCRScode = 'epsg:27700' #OSGB 1936 / British National Grid
OMAPCRScode = 'epsg:32631' #WGS 84 / UTM zone 31N

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

if len(sys.argv) > 1:
	gmlname = sys.argv[1]
else:
	gmlname = 'test.gml'

print('Reading features from '+gmlname)
unrecognisedFeatures = {};
#misfitOMAPs = {};
mainOMAP = omap.omap();
mainOMAP.setGMLCRS(init=GMLCRScode)
#mainOMAP.setOMAPCRS(OMAPCRScode)
objectCount = 0

#Setup streaming XML reader
srcstrm = pulldom.parse(gmlname)

#Find a coordinate (any coordinate) to choose the UTM Zone
for event,node in srcstrm:
	if event == pulldom.START_ELEMENT and node.tagName == 'gml:coordinates':
		srcstrm.expandNode(node)
		mainOMAP.setUTMZoneFromCoord(node)
		break
		

#Setup streaming XML reader again
srcstrm = pulldom.parse(gmlname)

for event,node in srcstrm:
	#Find topographicMembers
	if event == pulldom.START_ELEMENT and node.tagName == 'osgb:topographicMember':
		srcstrm.expandNode(node)
		
		#Get feature code
		featureNodes = node.getElementsByTagName('osgb:featureCode')
		if len(featureNodes) == 1:
			featureCode = getText(featureNodes[0].childNodes)
		else:
			print('Feature does not have exactly one feature code')
			print(node.toxml())
			continue
			
		#Find GML objects
		GMLObjects = node.getElementsByTagName('gml:Polygon') + node.getElementsByTagName('gml:Point') + node.getElementsByTagName('gml:LineString')
		
		if len(GMLObjects) == 0:
			print('Feature does not have any geometry')
			print(node.toxml())
			continue
		
		#Lookup feature code
		ISSOMCode = 'none'
		featureStrings = []
		if featureCode in OS_ISSOM_MAP.map:
			if isinstance(OS_ISSOM_MAP.map[featureCode],str):
				ISSOMCode = OS_ISSOM_MAP.map[featureCode]
			else:		
				featureDataNodes = [element for featureTag in OS_ISSOM_MAP.addFeatureTags for element in node.getElementsByTagName(featureTag)] 
				featureStrings = [getText(featureDataNode.childNodes) for featureDataNode in featureDataNodes]
				for featureString in featureStrings:
					if featureString in OS_ISSOM_MAP.map[featureCode]:
						ISSOMCode = OS_ISSOM_MAP.map[featureCode][featureString]	
		
		if ISSOMCode == 'none':
			if len(featureStrings):
				print('Warning: using default symbol for feature '+featureCode)
				print('Feature Strings:')
				print(featureStrings)
			descTextNode = node.getElementsByTagName('osgb:descriptiveGroup')[0].childNodes[0]
			unrecognisedFeatures[featureCode] = descTextNode.data
			if GMLObjects[0].tagName == 'gml:Point':
				ISSOMCode = OS_ISSOM_MAP.map['defaultpoint']
			elif GMLObjects[0].tagName == 'gml:Polygon':	
				ISSOMCode = OS_ISSOM_MAP.map['defaultarea']
			else:	
				ISSOMCode = OS_ISSOM_MAP.map['defaultline']
		
		if not ISSOMCode == '':
			objectCount += mainOMAP.addGMLObjects(GMLObjects,ISSOMCode)
			print('\r'+str(objectCount)+' features mapped',end="")
			

print()
fileSplit = gmlname.split('.')
fileSplit[-1] = 'xmap'
outFileName = '.'.join(fileSplit)

mainOMAP.setMapOrigin()
mainOMAP.updateGeoRef()
print('Writing '+outFileName)
mainOMAP.write(outFileName)

# for misfitCode in misfitOMAPs:
	# fileSplit[-1] = misfitCode
	# outFileName = '.'.join(fileSplit)+'.xmap'
	# print('Writing data for unrecognised code '+misfitCode+' to '+outFileName)
	# misfitOMAPs[misfitCode].setMapOrigin()
	# misfitOMAPs[misfitCode].write(outFileName)

if len(unrecognisedFeatures):			
	print('Some features were unrecognised. They have been added to the map in the default style for points, lines or areas as appropriate. Please add the codes to the feature map in OS_ISSOM_MAP.py with the appropriate ISSOM symbols.')			
	for featCode in unrecognisedFeatures:
		print('Code: ' + featCode + ' OS feature discription: ' + unrecognisedFeatures[featCode])



