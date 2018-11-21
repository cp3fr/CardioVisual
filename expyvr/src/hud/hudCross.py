# -*- coding: utf-8 -*-
#===============================================================================
# Copyright (c) 2009-2011 EPFL (Ecole Polytechnique federale de Lausanne) 
# Laboratory of Cognitive Neuroscience (LNCO) 
# 
# ExpyVR is free software ; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation ; either version 2 of the License, or (at your option) any later version.
# 
# ExpyVR is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY ; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with ExpyVR ; if not, write to the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA.
# 
# Authors : Tobias Leugger leugger.tobias@web.de
#          Bruno Herbelin bruno.herbelin@epfl.ch
#          Nathan Evans   nathan.evans@epfl.ch
# Web site : http://lnco.epfl.ch/expyvr
#===============================================================================

'''
Created on Jul 8, 2010

@author: bh
@since: Summer 2010

@license: Distributed under the terms of the GNU General Public License (GPL).
'''

from pyglet.gl import *

#pylnco modules
from abstract.AbstractClasses import DrawableHUDModule



class ModuleMain(DrawableHUDModule):
    """
    A simple module to display a fixation cross
    """
    defaultInitConf = {
        'name': 'fixationcross'
    }
    
    defaultRunConf = {
        'shape': '+',
        'size': 3,
        'pensize': 8,
        'color': (255, 255, 255, 255),
        'posX': 50.0,
        'posY': 50.0,
        'pause_on_start': False
    }
    
    confDescription = [
        ('name', 'str', "Module displaying a fixation cross"),
        ('shape', 'str', "Shape of the cross", ['+', 'X', '.']),
        ('size', 'int', "Size of the cross, in percent of the screen height"),
        ('pensize', 'int', "Width of the pen drawing the cross, in pixels"),
        ('color', 'code', "Color of the cross in rgba [0..255], e.g. (255,0,0,255)"),
        ('posX', 'float', "Horizontal position in % of the window width *"),  
        ('posY', 'float', "Vertical position in % of the window height *"),  
        ('pause_on_start', 'bool', "Pause the simulation when starting"),
    ]

    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableHUDModule.__init__(self, controller, initConfig, runConfigs)
        
        self.pause = False           
    
    def draw(self, window_width, window_height):
        DrawableHUDModule.draw(self, window_width, window_height)
        
        # center cross
        glTranslatef(window_width * self.posX / 100.0, window_height * self.posY / 100.0, 0.0)
        
        glEnable(GL_POINT_SMOOTH)
        # scale cross 10x10 by self.scale % of window_height
        glScalef(self.scale / 1000.0 * window_height, self.scale / 1000.0 * window_height, 1.0)
        self.cross.draw()

        # pause the time manager only after displaying the first frame
        if self.pause:
            self.controller.gTimeManager.pause()
            self.pause = False
            
    def start(self, dt=0, duration=-1, configName=None):
        """
        Activate the engine with the parameters passed in the conf
        """
        DrawableHUDModule.start(self, dt, duration, configName)
        self.cross = Cross(self.activeConf)
        self.scale = self.activeConf['size']
        self.posX = self.activeConf['posX']
        self.posY = self.activeConf['posY']
        
        if self.activeConf['pause_on_start']:
            self.pause = True

    def stop(self, dt=0):
        DrawableHUDModule.stop(self, dt)
        self.cross.erase()

            

class Cross(object):
    def __init__(self, config):

        # Compile a display list
        self.list = glGenLists(1)
        glNewList(self.list, GL_COMPILE)

        # glColor4iv does NOT work :(
        color = config['color']
        glColor4f( float(color[0])/255.0, float(color[1])/255.0,
                   float(color[2])/255.0, float(color[3])/255.0 )

        glLineWidth(config['pensize'])
        glPointSize(config['pensize'])
        glDisable(GL_DEPTH_TEST)
        
        if config['shape'] == 'o':
            glBegin(GL_POINTS)
            glVertex3f(0.0, 0.0, 0.0)
            glEnd()
        elif config['shape'] == 'X':
            s = 5.0
            glBegin(GL_LINES)
            glVertex3f(-s, -s, 0.0)
            glVertex3f(s, s, 0.0)
            glVertex3f(-s, s, 0.0)
            glVertex3f(s, -s, 0.0)
            glEnd()
        else: # it's a "+"
            s = 5.0
            glBegin(GL_LINES)
            glVertex3f(0.0, -s, 0.0)
            glVertex3f(0.0, s, 0.0)
            glVertex3f(-s, 0.0, 0.0)
            glVertex3f(s, 0.0, 0.0)
            glEnd()

        glEndList()

    def draw(self):
        glCallList(self.list)   
        
    def erase(self):
        glDeleteLists(self.list, 1)


