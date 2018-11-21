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
'''
import os
from pyglet.gl import *
from pyglet import image

from abstract.AbstractClasses import DrawableHUDModule
from controller import getPathFromString


class ModuleMain(DrawableHUDModule):
    """
    A simple module to display Head-Up Display Images
    """
    defaultInitConf = {
        'name': 'hudImage'
    }
    
    defaultRunConf = {
        'filename': 'image_file_name.png',
        'scale': 100.0,
        'posX': 50.0,
        'posY': 50.0,
        'angle': 0.0,
        'alpha': 1.0,
        'pause_on_start': False
    }
    
    confDescription = [
        ('name', 'str', "Module displaying a 2D image on screen (Head-Up-Display image)"),
        ('filename', 'str', "Full path and filename of the image to display"),
        ('scale', 'float', "Scale factor in % of the window height *"),
        ('posX', 'float', "Horizontal position in % of the window width *"),  
        ('posY', 'float', "Vertical position in % of the window height *"),  
        ('angle', 'float', "Angle of rotation in degree *"),  
        ('alpha', 'float', "Opacity factor [0 1] = (1.0-transparency) *"),  
        ('pause_on_start', 'bool', "Pause the simulation when starting"),
        ('setIndex(int)', 'info', "Change the index of the image to display.")
    ]
    

    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableHUDModule.__init__(self, controller, initConfig, runConfigs)
        
        self.pictures = {}
        self.lists = {}
        self.alpha = 1.0
        self.pause = False
        self.drawn = False
        
        # load all the images we're going to display
        for conf in self.runConfs.values():
            imageName = conf['filename']
            if imageName in self.pictures:
                # We've already loaded that image
                continue
            pic = self.pictures[imageName] = image.load( getPathFromString(imageName) )
            texture = pic.get_texture()
        
            # Compile a display list for a quad with texture coordinates
            t = texture.tex_coords
            self.lists[imageName] = glGenLists(1)
            glNewList(self.lists[imageName], GL_COMPILE)
            glBindTexture(texture.target, texture.id)
            glScalef( float(pic.width) / float(pic.height), 1.0, 1.0)
            glBegin(GL_QUADS)
            glTexCoord2f(t[0], t[1])
            glVertex3f(-5.0, -5.0, 0.0)
            glTexCoord2f(t[3], t[4])
            glVertex3f(5.0, -5.0, 0.0)
            glTexCoord2f(t[6], t[7])
            glVertex3f(5.0, 5.0, 0.0)
            glTexCoord2f(t[9], t[10])
            glVertex3f(-5.0, 5.0, 0.0)
            glEnd()
            glEndList()
        
        self.scale = 100.0
        self.posX = 50
        self.posY = 50
        self.angle = 0.0
        self.alpha = 1.0

    def draw(self, window_width, window_height):
        DrawableHUDModule.draw(self, window_width, window_height)
        
        # center image
        glTranslatef(window_width * self.posX / 100.0, window_height * self.posY / 100.0, 0.0)
        # scale polygon 10x10 by self.scale % of window_height
        glScalef(self.scale / 1000.0 * window_height, self.scale / 1000.0 * window_height, 1.0)
        # apply transformations
        glRotatef(self.angle, 0,0,1)
        glColor4f(1.0, 1.0, 1.0, self.alpha)
        
        # Turn texturing on and draw
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT)
        glEnable(GL_TEXTURE_2D)
        # transparency based on Source Alpha Value
        glBlendEquation(GL_FUNC_ADD)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glCallList(self.lists[self.activeConf['filename']]) 
        glPopAttrib()

        # pause the time manager only after displaying the first frame
        if self.pause:
            self.controller.gTimeManager.pause()
            self.pause = False
        self.drawn = True
        
    def start(self, dt=0, duration=-1, configName=None):
        """
        Activate the text HUD engine with the parameters passed in the conf
        """
        DrawableHUDModule.start(self, dt, duration, configName)
        self.scale = self.activeConf['scale']
        self.posX = self.activeConf['posX']
        self.posY = self.activeConf['posY']
        self.angle = self.activeConf['angle']
        self.alpha = self.activeConf['alpha']

        if self.activeConf['pause_on_start']:
            self.pause = True
            
    def cleanup(self):
        DrawableHUDModule.cleanup(self)
        for list in self.lists.values():
            glDeleteLists(list, 1)
        self.lists = {}
        self.pictures = {}
