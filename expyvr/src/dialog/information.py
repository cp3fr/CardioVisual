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
Created on Jan 2012
@author: bruno
'''

from pyglet.gl import *
import pywidget, win32api, win32gui
from abstract.AbstractClasses import DrawableHUDModule



class ModuleMain(DrawableHUDModule):
    """
    A  module to display a question and get response with buttons
    """
    defaultInitConf = {
        'name': 'informationDialog',
        'endRoutine': True,
        'forceCursorVisible': True
    }
    
    defaultRunConf = {    
        'text': 'Any text\nincluding line breaks',
        'posX': 50.0,
        'posY': 50.0,
        'keys': 'ENTER',
    }
    
    confDescription = [
        ('name', 'str', "Name of the module"),
        ('endRoutine', 'bool', "End the current routine when dialog closed"),
        ('forceCursorVisible', 'bool', "Makes sure the mouse cursor is visible (even with 'hidecursor' display settings)"),
        ('text', 'str', "The text to be displayed"),
        ('posX', 'float', "Horizontal position in % of the window width *"),  
        ('posY', 'float', "Vertical position in % of the window height *"),  
        ('keys', 'str', "All keys which will close the dialog (space-separated list of keys, e.g. 'A _1 NUM_1 ENTER LEFT')"),
    ]
    
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableHUDModule.__init__(self, controller, initConfig, runConfigs)
        
        self.widget = None
        self.pause = False
        self.dialogs = {}
        self.window_width = 0
        self.window_height = 0
        
        for conf in self.runConfs:
            # pywidget label (with HTML text)
            txtformated = self.runConfs[conf]['text'].replace('\n', '<br>')
            txtformated = '<font face="Helvetica,Arial" size=3 color=white>%s</font>'%txtformated
            label = pywidget.Label(width=250, text=txtformated)
            h = label.height
            # ok button
            btext = self.runConfs[conf]['keys'].strip()
            button = pywidget.Button( text = 'Ok' if len(btext)<1 else 'Ok (' + btext + ')' )
            # vertical layout
            box = pywidget.VBox(elements=[label,button], proportions=[80, 20]) 
            # give the dialog a height proportional to the number of lines (+margin for title bar and panning)
            dialog = pywidget.Dialog(height=int(h*2.0+100.0), title=self.initConf['name'], content=box)
            self.dialogs[conf] = dialog
            
            @button.event
            def on_button_press(button):
                self.dialog._hidden = True
    
    def draw(self, window_width, window_height):
        DrawableHUDModule.draw(self, window_width, window_height)
        
        if self.dialog is None:
            return
        
        # resolution changed ? -> recenter the widget where asked in config
        if self.window_width != window_width or self.window_height != window_height:
            self.window_width = window_width
            self.window_height = window_height

            self.dialog.x = self.window_width * self.activeConf['posX'] / 100.0 - self.dialog.width / 2
            self.dialog.y = self.window_height * self.activeConf['posY'] / 100.0 - self.dialog.height / 2
            
        # draw the dialog
        self.dialog.draw()
     
        if self.dialog._hidden and self.initConf['endRoutine']:
            self.controller.endCurrentRoutine()
        
    def start(self, dt=0, duration=-1, configName=None):
        """
        Activate the dialog with the parameters passed in the conf
        """
        DrawableHUDModule.start(self, dt, duration, configName)
                 
        self.cursorvisible, tmp, coordinates = win32gui.GetCursorInfo()
        # show the cursor if needs to be shown :
        if self.cursorvisible < 1 and self.initConf['forceCursorVisible']:
            win32api.ShowCursor(1)
            
        # choose appropriate dialog
        self.dialog = self.dialogs[configName]
        self.dialog._hidden = False        
        self.window_width = 0
        self.window_height = 0
                        
        # register the widget for windows events
        self.controller.registerWidget(self.dialog)
        self.controller.registerKeyboardAction(self.activeConf['keys'], self.onKeyPress)

            
    def stop(self, dt=0):
        # unregister the widget 
        self.controller.unregisterWidget(self.dialog)
        self.controller.unregisterKeyboardAction(self.activeConf['keys'], self.onKeyPress)  
        
        # set the cursor back to its original visibility (i.e. hides it if needed)
        if self.cursorvisible < 1:
            win32api.ShowCursor(0)
            
        # stop module
        DrawableHUDModule.stop(self, dt)

    def onKeyPress(self, keypressed=None):
        if self.started:
            self.dialog._hidden = True
