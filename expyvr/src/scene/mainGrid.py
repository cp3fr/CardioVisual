'''
Displays a 3D GL grid plane in XY, XZ, YZ

@author: Nathan Evans
'''

from pyglet.gl import *

from abstract.AbstractClasses import DrawableModule


class ModuleMain(DrawableModule):
    defaultInitConf = {
        'name': 'glgrid'
    }
    
    defaultRunConf = {
        'XY': True,                #draw a grid in the XY plane
        'XZ': False,               #draw a grid in the XZ plane
        'YZ': False,                #draw a grid in the YZ plane  
        'numLines': 20,              #how many lines in 1D of grid?
        'color': '(.3,.3,.3)'       #color
    }
    
    confDescription = [
       ('name', 'str', "Module displaying a 3D grid."),
       ('XY', 'bool', "Draw a grid in the XY plane", True),
       ('XZ', 'bool', "Draw a grid in the XZ plane", False),
       ('YZ', 'bool', "Draw a grid in the YZ plane", False),              
       ('numLines', 'int', "Number of lines to draw in each dimension"),
       ('color', 'str', "RGB color of grid (0->1.0, 0->1.0, 0-1.0)")       
   ]
        
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableModule.__init__(self, controller, initConfig, runConfigs)
        
                                             
    def draw(self, window_width, window_height, eye=-1):
        DrawableModule.draw(self, window_width, window_height, eye)
        glPushMatrix()

        numLines = self.activeConf['numLines']
        
        #color + lines
        glLineWidth(2)
        eval('glColor3f' + self.activeConf['color'])

        #Fill grid frame
        glBegin(GL_LINES)
        for i in range(-numLines,numLines):            
            if(self.activeConf['XY']):
                glVertex3f(-numLines,i,0)           #xplane
                glVertex3f(numLines,i,0)    
                glVertex3f(i,numLines,0)           #yplane
                glVertex3f(i,-numLines,0)    

            if(self.activeConf['XZ']):
                glVertex3f(-numLines,0,i)           #xplane
                glVertex3f(numLines,0,i)    
                glVertex3f(i,0,numLines)           #zplane
                glVertex3f(i,0,-numLines)    

            if(self.activeConf['YZ']):
                glVertex3f(0,numLines,i)           #yplane
                glVertex3f(0,-numLines,i)    
                glVertex3f(0,i,numLines)           #zplane
                glVertex3f(0,i,-numLines)    

        glEnd()

        glPopMatrix()
        
    def start(self, dt=0, duration=-1, configName=None):
        """
        Activate with the parameters passed in the conf
        """
        DrawableModule.start(self, dt, duration, configName)

    def stop(self, dt=0):
        DrawableModule.stop(self, dt)
    
    def cleanup(self):
        DrawableModule.cleanup(self)
