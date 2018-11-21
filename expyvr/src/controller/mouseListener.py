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
mouseListener.py
Created on Jan 6, 2012
@author: bruno
'''

from pyglet.window import mouse
from pyglet.event import EVENT_UNHANDLED

class MouseListener():
    def __init__(self, controller):
        self._controller = controller
        # list of buttons to listen associated with the list of methods to call
        self._buttonFunctionMap = {}         
        # list of methods to call when mouse moves
        self._motionFunctionList = []         
        # list of widgets registered
        self._widgets = []         

    def distributeButtonPress(self, x, y, button):
        # distribute the event to every widget registered
        for w in self._widgets:
            if w.on_mouse_press(x, y, button, 0) != EVENT_UNHANDLED:
                return 
            
        # if exists, call the function associated with that button
        if button in self._buttonFunctionMap:
            # browse the list of elements in the list of functions
            for fn in self._buttonFunctionMap[button]:
                if fn[0] is not None:
                    # call function
                    fn[0](x, y, mouse.buttons_string(button))
                    
    def distributeButtonRelease(self, x, y, button):
        # distribute the event to every widget registered
        for w in self._widgets:
            if w.on_mouse_release(x, y, button, 0) != EVENT_UNHANDLED:
                return 
            
        # if exists, call the function associated with that button
        if button in self._buttonFunctionMap:
            # browse the list of elements in the list of functions
            for fn in self._buttonFunctionMap[button]:
                if fn[1] is not None:
                    # call all functions
                    fn[1](x, y, mouse.buttons_string(button)) 
      
    def listenTo(self, stringlistofbuttons, functionPress, functionRelease):
        # insert the new items into the dictionary
        for k in self._getValidButtons(stringlistofbuttons):
            # if the key is already in the list
            if k in self._buttonFunctionMap:
                # add the function to the list of functions in the map
                self._buttonFunctionMap[k].append((functionPress, functionRelease))
            else:
                # update the map with this new entry
                self._buttonFunctionMap.update({k: [(functionPress, functionRelease)]})
        
    def stopListeningTo(self, stringlistofbuttons, functionPress=None, functionRelease=None):
        # Remove the elements to stop to listen
        for k in self._getValidButtons(stringlistofbuttons):
            # if the key is in the map
            if k in self._buttonFunctionMap:
                # browse the list of elements in the list of functions
                for fn in self._buttonFunctionMap[k]:
                    # if the function matches or if none was given
                    if (functionPress, functionRelease) == fn  or (functionPress is None and functionRelease is None):
                        self._buttonFunctionMap[k].remove(fn)
                    # if the list is now empty, delete the entry
                    if len(self._buttonFunctionMap[k]) < 1:
                        del self._buttonFunctionMap[k]
        
    def _getValidButtons(self, stringlistofbuttons):
        # create an upper-case list of strings without the white-spaces
        buttonslist = stringlistofbuttons.upper().split()
        # only return the valid buttons
        return [getattr(mouse, k) for k in buttonslist if hasattr(mouse, k)]

    def listenToMotion(self, functionMove):
        # add the function to the list of functions
        self._motionFunctionList.append(functionMove) 
        
    def stopListeningToMotion(self, functionMove):
        # remove the function to the list of functions
        self._motionFunctionList.remove(functionMove) 

    def distributeMotion(self, x, y, dx, dy, buttons):
        ret = EVENT_UNHANDLED
        # distribute the event to every widget registered
        for w in self._widgets:
            if buttons > 0: # drag
                ret = w.on_mouse_drag(x, y, dx, dy, buttons, 0)
            else:
                ret = w.on_mouse_motion(x, y, dx, dy)
                
        if ret != EVENT_UNHANDLED:
            return True
        
        # browse the list of elements in the list of functions
        for fn in self._motionFunctionList:
            if fn is not None:
                # call function
                fn(x, y, mouse.buttons_string(buttons))       
                
        return False
    
    def registerWidget(self, widget):
        # add the widget to the list of widgets
        self._widgets.append(widget)
        
    def unregisterWidget(self, widget):
        # remove the widget from the list of widgets
        self._widgets.remove(widget)
