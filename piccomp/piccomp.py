from PIL import Image, ImageDraw, ImageFont
from glob import glob
import re

PAGE_SIZE = (2,4)
IM_SIZE = (800,600)

IMPAGE_SIZE = (PAGE_SIZE[0]*IM_SIZE[0],PAGE_SIZE[1]*IM_SIZE[1])

font = ImageFont.truetype('arialbd.ttf',size=52)
#font = ImageFont.load_default()

RE_filen = re.compile('.*?(\d+)\.[jJ][pP][gG]')

files = glob('./[0-9][0-9][0-9].jpg')
controls = []
for file in files:
	m = RE_filen.match(file)
	if m:
		controls.append(m.group(1))
		
controls.sort()

print(str(len(controls))+' control photos')

pageindex = 0
xindex = 0
yindex = 0
impage = Image.new('RGB',IMPAGE_SIZE,'white')

for c in controls:
	with Image.open(c+'.jpg') as im:
		draw = ImageDraw.Draw(im)
		draw.text((20,30),c,fill='red',font=font)
		impage.paste(im,(xindex*IM_SIZE[0],yindex*IM_SIZE[1],(xindex+1)*IM_SIZE[0],(yindex+1)*IM_SIZE[1]))
		
		
	#Increment image position and page	
	xindex += 1
	if xindex == PAGE_SIZE[0]:
		xindex = 0
		yindex += 1
		if yindex == PAGE_SIZE[1]:
			yindex = 0
			impage.save('page'+str(pageindex)+'.jpg')
			impage = Image.new('RGB',IMPAGE_SIZE,'white')
			pageindex += 1

#Write page with dangling images			
if xindex != 0 or yindex != 0:
	impage.save('page'+str(pageindex)+'.jpg')
