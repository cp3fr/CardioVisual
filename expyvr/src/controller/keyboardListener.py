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
keyboardListener.py
Created on Nov 23, 2010
@author: tobias, bruno
'''

from pyglet.window import key

class KeyboardListener():
    def __init__(self, controller):
        self._controller = controller
        # list of keys to listen associated with the list of methods to call
        self._buttonFunctionMap = {}         

    def distributeKeyPress(self, k):
        # special case PAUSE key ; can always unpause in case of bad script
        if k == key.PAUSE:
            self._controller.gTimeManager.togglePause()
        # if exists, call the function associated with that key
        elif k in self._buttonFunctionMap:
            # browse the list of elements in the list of functions
            for fn in self._buttonFunctionMap[k]:
                if fn[0] is not None:
                    # call function
                    fn[0](key.symbol_string(k)) 
                    
    def distributeKeyRelease(self, k):
        # if exists, call the function associated with that key
        if k in self._buttonFunctionMap:
            # browse the list of elements in the list of functions
            for fn in self._buttonFunctionMap[k]:
                if fn[1] is not None:
                    # call all functions
                    fn[1](key.symbol_string(k)) 
      
    def listenTo(self, stringlistofkeys, functionPress, functionRelease):
        # insert the new items into the dictionary
        for k in self._getValidButtons(stringlistofkeys):
            # if the key is already in the list
            if k in self._buttonFunctionMap:
                # add the function to the list of functions in the map
                self._buttonFunctionMap[k].append( (functionPress, functionRelease) )
            else:
                # update the map with this new entry
                self._buttonFunctionMap.update( {k: [(functionPress, functionRelease)]} )
        
    def stopListeningTo(self, stringlistofkeys, functionPress = None, functionRelease = None):
        # Remove the elements to stop to listen
        for k in self._getValidButtons(stringlistofkeys):
            # if the key is in the map
            if k in self._buttonFunctionMap:
                # browse the list of elements in the list of functions
                for fn in self._buttonFunctionMap[k]:
                    # if the function matches or if none was given
                    if (functionPress,functionRelease) == fn  or ( functionPress is None and functionRelease is None ):
                        self._buttonFunctionMap[k].remove(fn)
                    # if the list is now empty, delete the entry
                    if len(self._buttonFunctionMap[k]) < 1:
                        del self._buttonFunctionMap[k]
        
    def _getValidButtons(self, stringlistofkeys):
        # create an upper-case list of strings without the white-spaces
        keyslist = stringlistofkeys.upper().split()
        # only return the valid keys
        return [getattr(key, k) for k in keyslist if hasattr(key, k)]


