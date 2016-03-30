import os
import re
import np

class lidarReader:

	def __init__(self,**kwargs):
		self.maptiles = []
		self.bounds = [+np.inf,+np.inf,-np.inf,-np.inf]
		if 'map_bounds' in kwargs:
			self.map_bounds = kwargs['map_bounds']
		else:
			self.map_bounds = None
		
	def scanTiles(self,path):
		files = os.listdir(path)
		for file in files:
			m = re.match('([a-z])([a-z])(\d{2})(\d{2})_DTM_2m\.asc',file)
			if m:
				metadata = self.getMetadata(os.path.join(path,file))
				if self.map_bounds: #Check if file is within map bounds
					if (self.map_bounds[0]<metadata['E_GB']) & (self.map_bounds[1]<metadata['N_GB']) & (self.map_bounds[2]>metadata['W_GB']) & (self.map_bounds[3]>metadata['S_GB']):
						self.maptiles.append(metadata)
				else:
					self.maptiles.append(metadata)
				
		if len(self.maptiles) == 0:
			print('No valid height map tiles')
			return
			
		print (str(len(self.maptiles))+' tiles overlap the map')				
		for tile in self.maptiles:
			if tile['W_GB'] < self.bounds[0]:
				self.bounds[0] = tile['W_GB']
			if tile['S_GB'] < self.bounds[1]:
				self.bounds[1] = tile['S_GB']
			if tile['E_GB'] > self.bounds[2]:
				self.bounds[2] = tile['E_GB']
			if tile['N_GB'] > self.bounds[3]:
				self.bounds[3] = tile['N_GB']
				
	def createHMap(self):				
		self.maporigin = (self.bounds[0],self.bounds[1])
		self.mapsize = (self.bounds[2]-self.bounds[0],self.bounds[3]-self.bounds[1])
		self.tilesize = self.maptiles[0]['ncols']
		self.resolution = self.maptiles[0]['cellsize']

		print ('OSGB origin: '+str(self.bounds[0])+','+str(self.bounds[1]))
		print ('Contour map size: '+str(self.mapsize[0])+'x'+str(self.mapsize[1]))
		
		self.x = np.arange(0, self.mapsize[0], self.resolution)
		self.y = np.arange(0, self.mapsize[1], self.resolution)
		self.x,self.y = np.meshgrid(self.x,self.y)
		self.z = np.zeros_like(self.x,dtype=np.float)
		
		for tile in self.maptiles:
			ieast = int((tile['W_GB']-self.maporigin[0])/self.resolution)
			inorth = int((tile['S_GB']-self.maporigin[1])/self.resolution)
			self.z[inorth:inorth+self.tilesize,ieast:ieast+self.tilesize] = np.flipud(np.genfromtxt(tile['filename'],dtype=np.float,delimiter=' ',skip_header=6))
			
		print ('Read {} files'.format(len(self.maptiles)))
	
		
		self.z[self.z<0.0] = 0.0
		return self.z
		
				
	def getMetadata(self,file):
		with open(file) as mapfile:	#Find metadata for each data file
			metadata = {'filename':file}
			while True:
				line = mapfile.readline().strip().split()
				if len(line) > 2: #Break when we finish the header and reach the data
					break
				metadata[line[0]] = int(line[1])
			
			#Create bounds
			metadata['W_GB'] = metadata['xllcorner']
			metadata['S_GB'] = metadata['yllcorner']
			metadata['E_GB'] = metadata['xllcorner']+metadata['ncols']*metadata['cellsize']
			metadata['N_GB'] = metadata['yllcorner']+metadata['nrows']*metadata['cellsize']
		
		return metadata

			
