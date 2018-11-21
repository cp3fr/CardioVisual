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
hudText.py
Created on Jul 8, 2010
@author: bruno, Tobias 
'''

from pyglet.gl import *

from abstract.AbstractClasses import DrawableHUDModule



class ModuleMain(DrawableHUDModule):
    """
    A simple module to display HUD text
    """
    defaultInitConf = {
        'name': 'hudText'
    }
    
    defaultRunConf = {    
        'text': 'Any text\nincluding line breaks',
        'color': (255, 0, 0, 255),
        'size': 26,
        'font': "arial",
        'halign': "left",
        'italic': False,
        'bold': False,
        'withFrame': True,
        'posX': 50.0,
        'posY': 50.0,
        'auto_width': True,
        'width': 50.0,
        'pause_on_start': False
    }
    
    confDescription = [
        ('name', 'str', "Module displaying text on screen (Head-Up-Display text)"),
        ('text', 'str', "The text to be displayed"),
        ('font', 'str', "Name of font", ['verdana', 'arial','arial black','times new roman','courier new','consolas','impact','wingdings']),
        ('size', 'int', "Size of font in pixels"),
        ('color', 'code', "Color of font in rgba [0..255], e.g. (255,0,0,255)"),
        ('italic', 'bool', "Use italic style"),
        ('bold', 'bool', "Use bold style"),
        ('halign', 'str', "The horizontal alignment of the text.", ['left', 'center', 'right']),
        ('withFrame', 'bool', "Show text within a rectangular frame (automatic)."),
        ('posX', 'float', "Horizontal position in % of the window width *"),  
        ('posY', 'float', "Vertical position in % of the window height *"),  
        ('auto_width', 'bool', "Take as much space as the text requires (ignore the width parameter below)"),
        ('width', 'float', "Horizontal size in % of the window width (adjuted to screen size)"),
        ('pause_on_start', 'bool', "Pause the simulation when starting"),
        ('setText(conf)', 'info', "Choose the text configuration to show (give config name as parameter)")
    ]
    
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableHUDModule.__init__(self, controller, initConfig, runConfigs)
        
        self.pause = False
        self.labels = {}
        self.window_width = 0
        self.need_rescale = True
        
        # load all the images we're going to display
        for c in self.runConfs:  
            conf = self.runConfs[c]
            self.labels[c] = pyglet.text.Label(text=conf['text'], color=conf['color'],
                                                       font_name=conf['font'], font_size=conf['size'],
                                                       italic=conf['italic'], bold=conf['bold'],
                                                       anchor_x='center', anchor_y='center', 
                                                       multiline = True, width = 2048, x=0, y=0)
            self.labels[c].set_style("align", conf['halign']) 
    
    def draw(self, window_width, window_height):
        DrawableHUDModule.draw(self, window_width, window_height)
        
        # resolution changed ? -> rescale the text
        if self.need_rescale or self.window_width != window_width:
            self.window_width = window_width
            # adjust label width
            if not self.activeConf['auto_width']:
                self.label.width = int( self.activeConf['width'] * self.window_width / 100.0)
            self.need_rescale = False
            
        # center text
        glTranslatef(window_width * self.posX / 100.0, window_height * self.posY / 100.0, 0.0)
        
        if self.withframe:
            glColor4f(1,1,1,0.1)
            glRecti( -self.label.width//2 -20, -self.label.content_height//2 -20, self.label.width//2 +20, self.label.content_height//2 +20)

        self.label.draw()
        
        # pause the time manager only after displaying the first frame
        if self.pause:
            self.controller.gTimeManager.pause()
            self.pause = False
        
    def start(self, dt=0, duration=-1, configName=None):
        """
        Activate the text HUD engine with the parameters passed in the conf
        """
        DrawableHUDModule.start(self, dt, duration, configName)
                 
        self.setText(configName)
        self.withframe = self.activeConf['withFrame']
        self.posX = self.activeConf['posX']
        self.posY = self.activeConf['posY']

        if self.activeConf['pause_on_start']:
            self.pause = True

    def setText(self, configName):
    
        if self.labels.keys().count(configName) > 0:
            self.label = self.labels[configName]
            if self.activeConf['auto_width']:
                self.label.width = self.label.content_width + 10
            # scale text on first frame
            self.need_rescale = True
        

