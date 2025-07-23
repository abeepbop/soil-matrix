import sys, pygame, math
import numpy as np
from numpy import random
from array import array
from scipy.signal import convolve2d
import graphlib

def temp_color(temp):
    #in celsius
    color = [255, -(255/60)*temp+425, 0]
    if temp <= 40:
        color = [(255/20)*temp-255, 255, 0]
    if temp <= 20:
        color = [0, 255, -(255/20)*temp+255]
    if temp <= 0:
        color = [0, (255/273)*temp+255, 255]
    
    color = [max(0,min(color[0],255)),max(0,min(color[1],255)),max(0,min(color[2],255))]
    return color

class Vivo:
    def __init__(self,position):
        self.position = position
        self.size = 30
    def draw(self,surface):
        color = 10,10,10
        pygame.draw.circle(surface,color,self.position,self.size//2)
    def update(self,dt,data):
        new_data = data
        new_data[0]*=0.99 #light is absorbed
        return new_data
    
class Material: 
    def __init__(self, material):
        self.type = material
        self.L_H2O = 0
        self.G_H2O = 0
        #self. other nutrients too, eventually. 
    def update(self,dt):
        #TO DO: at each timestep, the nutrients contained change in composition and flow amongst each other. 
        pass 

class Substrate:
    def __init__(self, w, h, width, height, sources):
        self.vivos = []
        self.num_squares = w * h
        self.grid = np.zeros(shape=(w,h))
        self.temps = np.zeros(shape=(w,h))
        
        #there are a number of sources that will always have a certain strength.
        self.light_strength = 100
        self.sources = sources
        for source in sources:
            self.grid[source[0]][source[1]] = self.light_strength
        
        self.border_width = 1 #the space between rects
        self.grid_height = len(self.grid) #the number of rows
        self.grid_width = len(self.grid[0]) #the number of columns.
        self.height_inc = height/self.grid_height #the height of individual squares (pixels.) 
        self.width_inc = width/self.grid_width #the width of individual squares. 
        
        self.objgrid = []
        for j in range(self.grid_height):
            sublist = []
            top = j * self.height_inc
            for k in range(self.grid_width):
                left = k * self.width_inc
                grid_object = Material('air')
                sublist.append(grid_object)
            self.objgrid.append(sublist)

        self.rect_grid = []
        for j in range(self.grid_height):
            sublist = []
            top = j * self.height_inc
            for k in range(self.grid_width):
                left = k * self.width_inc
                rect = pygame.Rect((left+(self.border_width/2), top+(self.border_width/2)), (self.width_inc-(self.border_width), self.height_inc-(self.border_width)))
                sublist.append(rect)
            self.rect_grid.append(sublist)
            
        self.displaytemp = False

    def find_grid_spot(self,plant):
        plant_position = plant.get_root()
        grid_location = [int(plant_position[1]//self.height_inc),int(plant_position[0]//self.width_inc)]
        grid_location[0] = min(grid_location[0],self.grid_height-1)
        grid_location[0] = max(grid_location[0],0)
        grid_location[1] = min(grid_location[1],self.grid_width-1)
        grid_location[1] = max(grid_location[1],0)
        return grid_location

    def draw(self,surface):
        #draw RECTS
        for j in range(self.grid_height):
            for k in range(self.grid_width):
                if self.displaytemp:
                    val = self.temps[j][k] #the temperature
                    col = temp_color(val)
                    pygame.draw.rect(surface,col,self.rect_grid[j][k])
                else:
                    val = self.grid[j][k] * 2.5 # 0-100 => 0-255
                    minnum = 50
                    val = min(255,val)
                    val = max(minnum,val)
                    col = val,min(val+50,255),180
                    pygame.draw.rect(surface,col,self.rect_grid[j][k])
                    if self.objgrid[j][k].type == 'air':
                        pass
                    elif self.objgrid[j][k].type == 'water':
                        pygame.draw.rect(surface,(0,0,200),self.rect_grid[j][k])
                    elif self.objgrid[j][k].type == 'soil':
                        pygame.draw.rect(surface,(0,0,0),self.rect_grid[j][k])
            #draw PLANTS
        for vivo in self.vivos:
            vivo.draw(surface)


    def diffuse(self,dt):
        # TODO... look into numpy matrix things.
        mod = 1e-3
        """
        self.grid+=mod*np.roll(self.grid,shift=1,axis=1) # right
        self.grid+=mod*np.roll(self.grid,shift=-1,axis=1) # left
        self.grid+=mod*np.roll(self.grid,shift=1,axis=0) # down
        self.grid+=mod*np.roll(self.grid,shift=-1,axis=0) # up
        """
        """
        mapArr=array(map)
        kernel=array([[0  , 0.2,   0],
              [0.2,   0, 0.2],
              [0  , 0.2,   0]])
        self.grid=convolve2d(self.grid,kernel,boundary='wrap')
        """
        np.pad(self.grid, [(0, 1), (0, 1)], mode='constant')
        contrib = (self.grid * dt)
        #w = contrib / 8.0
        w = contrib / 5.0
        r = self.grid - contrib
        #N = np.roll(w, shift=-1, axis=0)
        S = np.roll(w, shift=1, axis=0)
        E = np.roll(w, shift=1, axis=1)
        W = np.roll(w, shift=-1, axis=1)
        #NW = np.roll(N, shift=-1, axis=1)
        #NE = np.roll(N, shift=1, axis=1)
        SW = np.roll(S, shift=-1, axis=1)
        SE = np.roll(S, shift=1, axis=1)
        #self.grid = r + N + S + E + W + NW + NE + SW + SE
        self.grid = r + S + E + W + SW + SE
        #self.grid = self.grid[:-1][:-1]
        
        np.pad(self.temps, [(0, 1), (0, 1)], mode='constant')
        contrib = (self.temps * dt)
        w = contrib / 8.0
        r = self.temps - contrib
        N = np.roll(w, shift=-1, axis=0)
        S = np.roll(w, shift=1, axis=0)
        E = np.roll(w, shift=1, axis=1)
        W = np.roll(w, shift=-1, axis=1)
        NW = np.roll(N, shift=-1, axis=1)
        NE = np.roll(N, shift=1, axis=1)
        SW = np.roll(S, shift=-1, axis=1)
        SE = np.roll(S, shift=1, axis=1)
        self.temps = r + N + S + E + W + NW + NE + SW + SE
        #self.temps = self.temps[:-1][:-1]
        return None
    
    def find_grid_spot(self,plant):
        plant_position = plant.position
        grid_location = [int(plant_position[1]//self.height_inc),int(plant_position[0]//self.width_inc)]
        grid_location[0] = min(grid_location[0],self.grid_height-1)
        grid_location[0] = max(grid_location[0],0)
        grid_location[1] = min(grid_location[1],self.grid_width-1)
        grid_location[1] = max(grid_location[1],0)
        return grid_location
    
    def light_at(self,plant):
        value = -1 # dummy
        grid_pos = self.find_grid_spot(plant)
        value = self.grid[grid_pos[0],grid_pos[1]]
        return value
    
    def update(self,dt):
        #light updates
        for source in self.sources:
            self.grid[source[0]][source[1]] = self.light_strength
            
        #life continues
        for vivo in self.vivos: 
            #ideally their data should be from all squares they touch,
            spots_included = self.find_grid_spot(vivo)
            # if the vivo's edges are inside other grid spots,
            # (if the distance from vivo.position to a given edge OR vertex < vivo.size/2
                #vertexes are sufficient because touching two vertexes means touching the edge in-between. 
                #then include those grid spots as well. 
                #end will be a square of grid coordinates.
                #data supplied to vivo will be a square array of data for each grid spot. 
            #including a line to potential daughter cell... this part would require point in quadrilateral area calculation.
            data = [self.light_at(vivo)]
            new_data = vivo.update(dt,data)
            grid_spot = self.find_grid_spot(vivo)
            self.grid[grid_spot[0],grid_spot[1]] = new_data[0] #does not work
        
        #TODO: this is where the spot at? or below? any obstruction has some light removed.
        for j in range(self.grid_height):
            for k in range(self.grid_width):
                if self.objgrid[j][k].type == 'water':
                    if self.grid[j][k] >= 10: #AND LIGHT IS ABSORBED AS HEAT
                        self.grid[j][k] -= 10
                        self.temps[j][k] += 1
        
        #light travels down.
        self.diffuse(dt)
        
        #death

    def num_cells(self):
        return len(self.vivos)
    
    def add_vivo(self,position):
        new_vivo = Vivo(position)
        self.vivos.append(new_vivo)
        
    def obstruct(self,position):
        grid_location = [int(position[1]//self.height_inc),int(position[0]//self.width_inc)]
        grid_location[0] = min(grid_location[0],self.grid_height-1)
        grid_location[0] = max(grid_location[0],0)
        grid_location[1] = min(grid_location[1],self.grid_width-1)
        grid_location[1] = max(grid_location[1],0)
        if self.objgrid[grid_location[0]][grid_location[1]].type == 'air':
            self.objgrid[grid_location[0]][grid_location[1]].type = 'water'
        elif self.objgrid[grid_location[0]][grid_location[1]].type == 'water':
            self.objgrid[grid_location[0]][grid_location[1]].type = 'air'
        
