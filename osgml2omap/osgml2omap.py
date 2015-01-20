from xml.dom import pulldom
import sys
import OS_ISSOM_MAP
import omap

GMLCRScode = 'epsg:27700'
OMAPCRScode = 'epsg:2040'

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
	
unrecognisedFeatures = {};
output = omap.omap();
output.setGMLCRS(GMLCRScode)
output.setOMAPCRS(OMAPCRScode)
	
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
			
		#Lookup feature code
		if featureCode in OS_ISSOM_MAP.map:
			ISSOMCode = OS_ISSOM_MAP.map[featureCode]
		else:
			unrecognisedFeatures[featureCode] = ''
			
		
		#Find GML objects
		GMLObjects = node.getElementsByTagName('gml:Polygon') + node.getElementsByTagName('gml:Point') + node.getElementsByTagName('gml:LineString')
		
		if len(GMLObjects)>0:
			output.addGMLObjects(GMLObjects,ISSOMCode)
		else:
			print('Feature does not have any geometry')
			print(node.toxml())
			continue

output.setMapOrigin()			
			
print('Unrecognised Features:')			
print(unrecognisedFeatures)

output.write('out.xmap')


