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
#              Nathan Evans nathan.evans@epfl.ch
#              Joan Llobera joan.llobera@epfl.ch
# Web site : http://lnco.epfl.ch/expyvr
#===============================================================================

'''
hudText.py
Created on Jan 2012
@author: bruno 

updated march2013
joan llobera

updated july 2013
Michel Askelrod
'''

from random import randint
from pyglet.gl import *
from os import path
from datetime import datetime
import pywidget, win32api, win32gui
import csv
from abstract.AbstractClasses import DrawableHUDModule


class ModuleMain(DrawableHUDModule):
    """
    A  module to display a question and get response
    """
    defaultInitConf = {
        'name': 'scaleDialog',
        'endRoutine': True,
        'logToCSV': True,
        'forceCursorVisible': True
    }
    
    defaultRunConf = {    
        'text': 'Please move the slider and validate your answer.',
        'posX': 50.0,
        'posY': 50.0,
        'width': 80.0,
        'minimum': 0.0,
        'maximum': 1.0,
        'initial': 'median',
        'step': 0.1,
        'show_value' : False,
        'continuous_sliding' : False,
        'ticks' : [],
        'keys': 'LEFT RIGHT RETURN',
    }
    
    confDescription = [
        ('name', 'str', "Name of the module"),
        ('endRoutine', 'bool', "End the current routine when Ok button pressed"),
        ('logToCSV', 'bool', "Save the logs of the key pressed in a Comma Separated Values text file"),
        ('forceCursorVisible', 'bool', "Makes sure the mouse cursor is visible (even with 'hidecursor' display settings)"),
        ('text', 'str', "The text to be displayed"),
        ('minimum', 'float', "Value on the left of the scale "),  
        ('maximum', 'float', "Value on the right of the scale "),  
        ('initial', 'str', "Initial value", ['minimum', 'median', 'maximum','random']),
        ('step', 'float', "Size of a single step "),  
        ('show_value', 'bool', "Display the current value bellow the cursor"),
        ('continuous_sliding', 'bool', "Allow to move the cursor continously (use small step)"),
        ('ticks', 'code', "Array of strings used as ticks above the scale, e.g. ['low','medium','high']"),        
        ('keys', 'str', "List of keys to [move left, move right, validate] (space-separated list of keys, e.g. 'LEFT RIGHT RETURN')"),
        ('posX', 'float', "Horizontal position in % of the window width "),  
        ('posY', 'float', "Vertical position in % of the window height "),
        ('width', 'float', "Width in % of the window width"),
        ('value', 'info', "Current value of the slider (read only)."),
        ('setValue( x )', 'info', "Change the value of the slider."),
        ('setVisible( flag=True )', 'info', "Make the slider visible (true by default).")
    ]
    
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableHUDModule.__init__(self, controller, initConfig, runConfigs)
        
        self.widgets = {}
        self.window_width = 0
        self.window_height = 0
        self.value = 0
        self.pause = False
        self.nKeyPress = 0
        self.sliderSteps = 0
        self.increasing = False
        self.decreasing = False
        self.currentKeys = []
        self.cont = None
        self.widget = None
        
        for conf in self.runConfs:
            # pywidget label (with HTML text)
            txtformated = self.runConfs[conf]['text'].replace('\n', '<br>')
            txtformated = '<font face="Helvetica,Arial" size=6 color=white>%s</font>'%txtformated
            label = pywidget.Label(width=500, text=txtformated)
            h = label.height
            slider = pywidget.Slider(value=self.runConfs[conf]['minimum'], minimum=self.runConfs[conf]['minimum'], maximum=self.runConfs[conf]['maximum'], step=self.runConfs[conf]['step'], 
                                     label=self.runConfs[conf]['show_value'], ticks=self.runConfs[conf]['ticks'])

            @slider.event
            def on_value_change(value):
                self.value = value
                self.sliderSteps += 1
                                     
            if self.initConf['endRoutine']:
                # ok button
                button = pywidget.Button(text="Ok")
                hlayout = pywidget.HBox(width=500, elements=[pywidget.Widget(), button], proportions=[70,30]) 
                # vertical layout
                widget = pywidget.VBox(height = 210, elements=[label,slider,hlayout], proportions=[50, 40, 20]) 
                
                @button.event
                def on_button_press(button):
                    self.widget._hidden = True
                    
            else:
                widget = pywidget.VBox(height = 150, elements=[label,slider], proportions=[45, 55]) 
                
            self.widgets[conf] = widget
            self.cont = self.runConfs[conf]['continuous_sliding']
            
        self.csvLogger = None
        if self.initConf['logToCSV']:
            now = datetime.today()
            self.csvLogger = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.initConf['name'] + '.csv') , 'w'), lineterminator = '\n')
            self.csvLogger.writerow(['absTime', 'expTime', 'displayTime', 'routine', 'condition', 'min', 'initial', 'max', 'response', 'nKeyPress', 'duration'])

    
    def draw(self, window_width, window_height):
        DrawableHUDModule.draw(self, window_width, window_height)
        
        if self.widget is None:
            return
    
        if self.decreasing:
            self.widget._elements[1].set_cursor( self.value - self.activeConf['step'] )
        if self.increasing:
            self.widget._elements[1].set_cursor( self.value + self.activeConf['step'] )
            
        if not self.cont:
            self.decreasing = False
            self.increasing = False
        
        # resolution changed ? -> recenter and rescale the widget as asked in config
        if self.window_width != window_width or self.window_height != window_height:
            self.window_width = window_width
            self.window_height = window_height
            # adjust widget            
            self.widget.width = self.window_width * self.activeConf['width'] / 100.0 
            self.widget.update_width()
            self.widget.update_height()
            self.widget.x = self.window_width * self.activeConf['posX'] / 100.0 - self.widget.width / 2
            self.widget.y = self.window_height * self.activeConf['posY'] / 100.0 - self.widget.height / 2
            
        # draw the widget
        self.widget.draw()
        
        if self.widget._hidden and self.initConf['endRoutine']:
            self.controller.endCurrentRoutine()
        
    def start(self, dt=0, duration=-1, configName=None):
        """
        Activate the widget with the parameters passed in the conf
        """
        DrawableHUDModule.start(self, dt, duration, configName)
                 
        self.cursorvisible, tmp, coordinates = win32gui.GetCursorInfo()
        # show the cursor if needs to be shown :
        if self.cursorvisible < 1 and self.initConf['forceCursorVisible']:
            win32api.ShowCursor(1)
            
        # choose appropriate widget
        self.widget = self.widgets[configName]
        self.widget._hidden = False  
        self.value = 0
        self.sliderSteps = 0
        self.nKeyPress = 0
        self.window_width = 0
        self.window_height = 0
        
        # compute initial value 
        if self.activeConf['initial'] == 'minimum':
            self.initialValue = self.activeConf['minimum']
        elif self.activeConf['initial'] == 'maximum':
            self.initialValue =  self.activeConf['maximum']
        else:
            n = int((self.activeConf['maximum'] - self.activeConf['minimum'])/self.activeConf['step'])
            if self.activeConf['initial'] == 'random':
                self.initialValue = self.activeConf['minimum'] + float(randint(0,n)) * self.activeConf['step']
            else:
                self.initialValue = self.activeConf['minimum'] + float(n/2) * self.activeConf['step']
                        
        # set initial value to the slider object of the widget
        self.setValue(self.initialValue)
        
        # register the widget for windows events
        self.controller.registerWidget(self.widget)
        self.controller.registerKeyboardAction(self.activeConf['keys'], self.onKeyPress, self.onKeyRelease)

    def stop(self, dt=0):
        # unregister the widget 
        self.controller.unregisterWidget(self.widget)
        self.controller.unregisterKeyboardAction(self.activeConf['keys'], self.onKeyPress, self.onKeyRelease)
        
        # get start times before stopping module
        startTimes = self.getStartingTimes()
        
        if self.csvLogger :
            self.csvLogger.writerow( startTimes + 
                                     [ self.controller._currentRoutine, self.controller._currentCondition, 
                                      self.activeConf['minimum'], self.initialValue, self.activeConf['maximum'], 
                                      self.value, self.nKeyPress, str("%.4f"%(self.controller.gTimeManager.experimentTime() - startTimes[1])) ] )
                        
        # stop module
        DrawableHUDModule.stop(self, dt)
        
        # set the cursor back to its original visibility (i.e. hides it if needed)
        if self.cursorvisible < 1:
            win32api.ShowCursor(0)

    def onKeyPress(self, keypressed=None, runConfigs=None):
        # if self.cont:
        try:
            index = self.activeConf['keys'].split().index(keypressed)
            self.currentKeys.append(keypressed)
            if index == 0:
                self.decreasing = True
                self.nKeyPress += 1
            elif index == 1:
                self.increasing = True
                self.nKeyPress += 1
            else:
                self.widget._hidden = True
        except:
            pass

    def onKeyRelease(self, keypressed=None):
        
        # get only keys which were pressed after start
        if self.currentKeys.count(keypressed):
            self.currentKeys.remove(keypressed)
        try:
            index = self.activeConf['keys'].split().index(keypressed)
            if index == 0:
                self.decreasing = False
            elif index == 1:
                self.increasing = False
        except:
            pass

    def setValue(self, val):
        if (self.activeConf['minimum'] < val + 0.001) and (self.activeConf['maximum'] > val - 0.001) :
            if  self.widget is not None:
                self.widget._elements[1].set_cursor( val )
            self.value = val

    def setVisible(self, flag=True):
        if  self.widget is not None : 
            self.widget._hidden = not flag