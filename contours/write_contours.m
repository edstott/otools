
docNode = com.mathworks.xml.XMLUtils.createDocument('osm');
root = docNode.getDocumentElement;
root.setAttribute('version','0.6');
root.setAttribute('generator','edcontour');

noderoot = docNode.createElement('tocitem');
wayroot = docNode.createElement('tocitem');



