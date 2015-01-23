otools
======

#contours
dtmasc2osm.py - convert ASCII digital terrain model height data to contours in OpenStreetMap format

usage: dtm2asc.py <path containg DTM tiles>

Additional package dependencies: numpy, matplotlib, OSMLayer (included), pyproj

parameters (defined in dtmasc2osm.py):
  * resolution - resolution of input data (metres)
  * cint - contour interval (metres)
  * minclen - minimum length of a closed contour (number of data points, where the data point spacing ~= resolution)
  * cavgspan - window for smoothing (number of data points)
  
#osgml2omap
osgml2omap.py - convert Ordnance Survey GML data to OpenOrienteering Mapper map

usage: osgml2omap.py <gml filename>

Additional package dependencies: omap (included), pyproj

##Feature to symbol conversion with OS\_ISSOM\_MAP
osgml2omap performs a conversion from Ordance Survey feature codes to ISSOM symbols. Each OS feature is tagged with a five digit number and the file OS\_ISSOM\_MAP lists a mapping from every feature code to a symbol code referenced by Mapper. Mapper symbol codes follow the symbol numbers in Section 5 of *International Specification for Sprint Orienteering Maps* but are not identical because Mapper uses sub-codes to represent thickness variants and bordered areas, for example.

Certain OS feature codes are used to tag features that could be drawn with more than one ISSOM symbol. In some cases there is additional metadata in the GML that can help select the correct symbol. In OS\_ISSOM\_MAP these feature codes map to a sub-map, where text strings found in the metadata select the appropriate symbol code. The text strings are extracted from any tags present in the GML feature description that are listed at the end of OS\_ISSOM\_MAP. For example, code 10056 refers to open land, which may be paved or unpaved. Such features are also tagged with a 'make', which can be 'Natural' or 'Manmade', and this selects whether the feature should be mapped as 'open land' or 'paved area'.

osgml2omap will notify the user if any features are encountered without a mapping in OS\_ISSOM\_MAP. These features are added to the map with the relevant default symbol specified in OS\_ISSOM\_MAP (overprinting symbols are used so make the features easy to identify on the map). This also applies to features where the code is present but a text sub-map failed to match any of the feature data. Any unrecognised features can be added to OS\_ISSOM\_MAP by following the existing formatting. Features which should not appear on the map are given a blank symbol field.

##Current conversion limitations
* OS feature 10185 is used for 'structures', which can include towers, jetties, walkways, bridges and ruins. Passable and unpassbale features are not distinguished and they are all mapped as paved areas with a border.
* Impassable boundaries are shown around and between areas of private land. These should be removed to declutter the map.
* A number of watercourse point features are given the waterhole symbol, even though they might not be significant.
* OS data maps railway lines with one feature per rail and so a double-track railway will be given be mapped as four railway lines
* Certain line features are mapped as impassbale walls if the OS data calls them an 'obstruction' this can include crossable walls and fences and vegetation boundaries
* Canopies are not recognised - they are often separate features to adjoining buildings but are still mapped as impassable buildings

#osgml2osm
osgml2osm.py - convert convert Ordnance Survey GML data to OpenStreetmap layers

usage osgml2osm.py <gml filename>

Additional package dependencies: OSMLayer (included), pyproj
