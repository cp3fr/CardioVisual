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
timeManager.py
Created on Nov 23, 2010
@author: tobias, bruno
'''
from time import time as unix_time
from pyglet.clock import _default_time_function as time

class TimeManager():
    """
    The TimeManager class handles the timing of the experiment. 
    It implements pausing by storing the total time the experiment was paused so
    that the logger and other modules can use the actual time that the experiment
    is running for. It has to be used as the time function for the pyglet.clock to
    correctly pause all scheduled actions.
    All modules that need to use time that is experiment-centric have to use the
    instance of this class that is created in the controller.
    """
    def __init__(self, controller):
        self._controller = controller
        self._paused = False
        self._pauseStart = 0.0
        self._totalPauseTime = 0.0
        self._time0 = 0.0
        self._time_of_start = 0.0
        self._referenceWindow = None
        
    def start(self):
        self._time0 = time()
        self._time_of_start = unix_time()
        
    def absoluteTime(self):
        """
        Simply returns the current time from pyglet.clock._default_time_function()
        """
        return time()
    
    def experimentTime(self):
        """
        Returns the duration that the experiment was running (unpaused).
        Returns -1 if the TimeManager hasn't been started
        """
        if self._time0 == 0.0:
            return -1
        return self.clockTime() - self._time0
    
    def clockTime(self):
        """
        Returns the absolute time minus the time we spent pausing.
        During pauses, always returns the same time.
        This function should only be used by pyglet.clock 
        """
        if self._paused:
            return self._pauseStart - self._totalPauseTime
        return time() - self._totalPauseTime
    
    def displayTime(self):
        """
        Returns the experiment time when the display swap buffer occured
        Returns -1 if the TimeManager hasn't been started
        """
        if self._time0 == 0.0:
            return -1
        
        if self._referenceWindow is None:
            # find the first window valid from all renderers
            for r in self._controller.gDisplay.renderers:
                self._referenceWindow = r.getWindow()
                if self._referenceWindow is not None:
                    break
            
        if self._referenceWindow is not None:
            return self._referenceWindow.getFlipTime() - self._totalPauseTime - self._time0
        else:
            return self.clockTime()
            
    def displayPeriod(self):
        """
        Return the period of update of the display, i.e. dt between last two frames
        """
        if self._referenceWindow is None:
            # find the first window valid from all renderers
            for r in self._controller.gDisplay.renderers:
                self._referenceWindow = r.getWindow()
                if self._referenceWindow is not None:
                    break
            
        if self._referenceWindow is not None:
            return self._referenceWindow.getFlipPeriod()
        else:
            return -1
    
    def pause(self):
        if not self._paused:
            self._paused = True
            self._pauseStart = time()
            self._log("Experiment paused")
    
    def unpause(self):
        if self._paused:
            self._paused = False
            pauseTime = time() - self._pauseStart
            self._totalPauseTime += pauseTime
            self._log("Experiment resumed after %f seconds" % pauseTime)
            return pauseTime
        else:
            return 0
            
    def togglePause(self):
        if self._paused:
            self.unpause()
        else:
            self.pause()
            
    def _log(self, logData):
        self._controller.gLogger.logMe('timeManager', 'mainTimeManager', logData)
        

