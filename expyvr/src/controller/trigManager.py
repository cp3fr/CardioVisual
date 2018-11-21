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
trigManager.py
Created on March 15, 2011
@author: nathan
'''


class TrigManager():
    """
    Creates a unique, shared database of trigger code mappings for all components wishing to send triggers.
    
    This way, a unique mapping will be made between 
    """
    def __init__(self, controller, rCodes):
        self._controller = controller
        self._trigMap = {}
        self._curCode = 0
        self._reservedCodes = []        
        
        for i in xrange(len(rCodes)):
            self.reserveCode(rCodes[i])
            
        print "reserved Codes: " + str(self._reservedCodes)
        
    '''
    If certain trigger codes shouldn't be given out (ie: fixed for motors, etc), reserve them here
    '''
    def reserveCode(self,code):
        code = int(code)        #in case passing a string
        if not self._findCode(code):
            self._reservedCodes.append(code)
    
    def _findCode(self,c):
        """Return the index of the first item in reserved codes matching """
        for i in xrange(len(self._reservedCodes)):             
            if self._reservedCodes[i] == c:
                return True      

        return False

    def getCode(self,label):
        if self._trigMap.has_key(label):
#            self._controller.gLogger.logMe('trigManager','getCode',"Trigger label " + str(label) + " already in use. Returning same code.")
            return self._trigMap[label]

        #Skip over reserved
        nextCode = self._curCode
        while (self._findCode(nextCode)):   
            nextCode = nextCode + 1
            print "nextCode: " + str(nextCode)

        self._trigMap[label] = nextCode
        self.reserveCode(nextCode)
        self._curCode = nextCode

        return nextCode
    
            
    def printMapping(self):
        for k in self._trigMap.keys():
            self._controller.gLogger.logMe('trigManager', 'printMap', str(k) + " :: " + str(self._trigMap[k]))
        

    def cleanup(self):
        #del self._trigMap
        pass     
