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
hudTextFile.py
Created on Jul 8, 2010
@author: bruno, Tobias 
'''

from pyglet.gl import *

import csv
from abstract.AbstractClasses import DrawableHUDModule
from controller import getPathFromString



class ModuleMain(DrawableHUDModule):
    """
    A simple module to display HUD text
    """
    defaultInitConf = {
        'name': 'hudTextFile',
        'filename': '$EXPDIR$/text.csv',
        'color': (255, 0, 0, 255),
        'size': 26,
        'font': "arial",
        'italic': False,
        'bold': False,
        'halign': "left",
        'withFrame': True,
        'posX': 50.0,
        'posY': 50.0,
        'auto_width': True,
        'width': 50.0
    }
    
    defaultRunConf = {    
        'line': 0,
        'pause_on_start': False
    }
    
    confDescription = [
        ('name', 'str', "Module displaying lines of text from a file (Head-Up-Display text file)"),
        ('filename', 'str', "Full path and name of the .csv file to open: each line will be displayed separately"), 
        ('line', 'int', "The number of the line to read from the file"),
        ('font', 'str', "Name of font", ['verdana', 'arial','arial black','times new roman','courier new','consolas','impact','wingdings']),
        ('size', 'int', "Size of font in pixels"),
        ('color', 'code', "Color of font in rgba [0..255], e.g. (255,0,0,255)"),
        ('italic', 'bool', "Use italic style"),
        ('bold', 'bool', "Use bold style"),
        ('halign', 'str', "The horizontal alignment of the text.", ['left', 'center', 'right']),
        ('withFrame', 'bool', "Show text within a rectangular frame (automatic)."),
        ('posX', 'float', "Horizontal position in % of the window width"),  
        ('posY', 'float', "Vertical position in % of the window height"),  
        ('auto_width', 'bool', "Take as much space as the text requires (ignore the width parameter below)"),
        ('width', 'float', "Horizontal size in % of the window width (adjuted to screen size)"),
        ('pause_on_start', 'bool', "Pause the simulation when starting"),
        ('setLine(int)', 'info', "Change the line of text to display.")
    ]
    
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableHUDModule.__init__(self, controller, initConfig, runConfigs)
        
        self.pause = False
        self.labels = {}
        self.window_width = 0
        self.need_rescale = True
        self.withframe = self.initConf['withFrame']
        self.posX = self.initConf['posX']
        self.posY = self.initConf['posY']
        self.numlines = 0
        
        try:
            fn =  str(self.initConf['filename'])
            f = open( getPathFromString( fn ) )
            csvread = csv.reader(f)
            for r in csvread:
                if len(r) < 1:
                    continue
                string = ''
                for i in r:
                    string += i + '\n'
                string = string[:-1]
                
                self.labels[self.numlines] = pyglet.text.Label(text=string, color=self.initConf['color'],
                                                   font_name=self.initConf['font'], font_size=self.initConf['size'],
                                                   italic=self.initConf['italic'], bold=self.initConf['bold'],
                                                   anchor_x='center', anchor_y='center',
                                                   multiline = True, width = 2048, x=0, y=0)
                self.labels[self.numlines].set_style("align", self.initConf['halign']) 
                self.numlines += 1
                
        except IOError:
            showWarning( 'Could not open file %s.\n\nThe filename given was: %s.'%(getPathFromString(fn), str(fn)) )
        else:
            f.close()

    def draw(self, window_width, window_height):
        DrawableHUDModule.draw(self, window_width, window_height)
        
        # resolution changed ? -> rescale the text
        if self.need_rescale or self.window_width != window_width:
            self.window_width = window_width
            
            self.label.height = self.label.content_height
            # adjust label width
            if not self.initConf['auto_width']:
                self.label.width = int( self.initConf['width'] * self.window_width / 100.0)
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
                 
        # show the line of text requested
        self.setLine( self.activeConf['line'] )

        if self.activeConf['pause_on_start']:
            self.pause = True

    def setLine(self, line):
        # get bounded line number [0 .. self.numlines]
        l = max ( 0, min ( line, self.numlines) )
        # get label prepared for this line
        self.label = self.labels[self.activeConf['line']]
        if self.initConf['auto_width']:
            self.label.width = self.label.content_width + 10
        # scale text on first frame
        self.need_rescale = True
        
        