
import os
import re

srcdir = 'd:\estott\Stuff\omaps\maryon\DTM'
tilesize = 1000
cint = 2.5

eastlconv = {'A':0,'B':1,'C':2,'D':3,'E':3,'F':0,'G':1,'H':2,'J':3,'K':3,'L':0,'M':1,'N':2,'O':3,'P':3,'Q':0,'R':1,'S':2,'T':3,'U':3,'V':0,'W':1,'X':2,'Y':3,'Z':3}
northlconv = {'A':4,'B':4,'C':4,'D':4,'E':4,'F':3,'G':3,'H':3,'J':3,'K':3,'L':2,'M':2,'N':2,'O':2,'P':2,'Q':1,'R':1,'S':1,'T':1,'U':1,'V':0,'W':0,'X':0,'Y':0,'Z':0}

files = os.listdir(srcdir)
dtmfiles = []
north = []
east = []
for file in files:
	print file
	m = re.match('([A-Z])([A-Z])(\d{2})(\d{2})([ns])([ew])_DTM_50CM\.asc',file)
	if m:
		dtmfiles.append(file)
		east.append(eastlconv[m.group(1)]*500000 + eastlconv[m.group(2)]*100000 + int(m.group(3))*1000 + (m.group(6)=='e')*500)
		north.append(northlconv[m.group(1)]*500000 + northlconv[m.group(2)]*100000 + int(m.group(4))*1000 + (m.group(5)=='n')*500)

print dtmfiles
print east
print north
		
		