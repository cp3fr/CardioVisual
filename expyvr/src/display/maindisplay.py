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
ExpyVR display handler 
Display / scene handler 

@author: Bruno Herbelin, Danilo Jimenez Rezende, Nathan Evans, Joan Llobera
'''


#Numpy and scipy
import numpy as np

#For gl
from pyglet.gl import *

class Display():
    def __init__(self, controller):
        self._controller = controller
        self.toDrawList = []         #list of tuples containing the draw order and the objects that should be drawn 
        self.toDrawHUDList = []         #list of tuples containing the draw order and the objects that should be drawn 
        self.renderers = []
        
    # w is width, h is height, eye is for stereo; -1 not stereo, 0 left eye, 1 right eye
    def drawAll(self, w, h, eye = -1):
        for obj in self.toDrawList:
            glMatrixMode(GL_MODELVIEW)        
            glPushMatrix()
            obj[1].draw(w, h, eye)
            glPopMatrix()
            
    # w is width, h is height, eye is for stereo; -1 not stereo, 0 left eye, 1 right eye
    def drawAllHUD(self, w, h):
        for obj in self.toDrawHUDList:
            glMatrixMode(GL_MODELVIEW)        
            glPushMatrix()
            obj[1].draw(w, h)
            glPopMatrix()
            
    def addRenderer(self, renderer):
        renderer.setOnFrameMethods(self.drawAll, self.drawAllHUD)
        self.renderers.append(renderer)
        self._log("Renderer " + renderer.name + " setup for " + renderer.description)
    
    def removeRenderer(self, renderer):
        """
        Windows should call this if they are closed so that the experiment
        can be terminated properly if no more windows are open.
        """
        if renderer.visible:
            renderer.close()
        self.renderers.remove(renderer)
        self._log("Removed window " + renderer.name)
        if len(self.renderers) == 0:
            self._log("No more open windows, terminating experiment")
            self._controller.cleanupExperiment()
            
    def setWindowsVisible(self, visible=True): 
        for r in self.renderers:
            r.setVisible(visible) 

    def closeAll(self):
        while len(self.renderers) > 0:
            self.renderers[0].close()
            self.renderers.remove(self.renderers[0])
                    
    def _log(self, logData):
        """
        Wrapper for logging inside the display
        """
        self._controller.gLogger.logMe('mainDisplay', 'mainDisplay', logData)

    def set_camera_position(self, Q):
        """
        Give a numpy vector to change position of camera
        """
        for r in self.renderers:
            r.cam.set_position(Q)
        
    def set_camera_angles(self, angs):
        """
        Give a numpy vector of Euler Angles (in degrees) to change orientation of camera
        """
        for r in self.renderers:
            r.cam.set_angles(angs)

    def set_camera_rotation(self, R):
        """
        Give a numpy Rotation matrix to change orientation of camera
        """
        for r in self.renderers:
            r.cam.set_position(R)
    
    def set_camera_correction(self,T):
        """
        correct the distance between the eyes and the head center (the vector to give is FROM eyes TO head center, typically [0.0,0.0,0.15])
        """
        for r in self.renderers:
            r.cam.set_correction(T)
