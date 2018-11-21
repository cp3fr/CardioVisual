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

"""
@author: Tobias Leugger, Nathan Evans
@since: Nov 2010

Abstract classes for modules representing a component of ExpyVR.
Every module should have a ModuleMain class expanding from one
of the classes defined here.
"""

class BasicModule:
    """
    BasicModule class: All modules (components) should extend from this
    class, overwrite the methods defined here but still calling them at
    the beginning of the method.
    The default configs should also be overwritten.
    """
    
    """
    Complete config that is used during initialisation. There has
    to be at least the key 'name' 
    """
    defaultInitConf = {
        'name': 'abstractModule',             # any string
    }
    
    """
    Complete run config that is used to configure the module during runtime.
    """
    defaultRunConf = {}
    
    """
    Description of both init and run config params.
    The order will be the order in which they are displayed in the GUI.
    Every element is a 3-tuple or 4-tuple of name of the param, type and  
    a description for the user. An optional 4th part is a list of allowed
    values if the param should be a choice box
    """
    confDescription = [
        ('name', 'str', "Name of this component")
    ]
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        """
        Call this from the __init__ of every child class.
        Makes sure self.initConf and self.runConfs are set with the
        complete dicts. self.runConfs is a dict of configs (dicts) that 
        always at least has an element 'standard'. The default configs 
        are used to complete the passed configs if they are incomplete.
        """
        # make sure we have a complete initConfig
        self.initConf = dict.copy(self.__class__.defaultInitConf)
        if initConfig:
            self.initConf.update(initConfig)
        
        # complete all the run configs
        self.runConfs = {}
        # set the standard config to the default one
        self.runConfs['standard'] = dict.copy(self.__class__.defaultRunConf)
        if runConfigs:
            if 'standard' in runConfigs:
                # if the passed configs contained a standard one, update it
                self.runConfs['standard'].update(runConfigs['standard'])
                del runConfigs['standard']
            for configName, config in runConfigs.items():
                # complete all the other configs with the standard config
                self.runConfs[configName] = dict.copy(self.runConfs['standard'])
                self.runConfs[configName].update(config)
                
        # and copy the standard conf to the active conf, the active conf is
        # the one that should be used to retrieve conf values
        self.activeConf = dict.copy(self.runConfs['standard'])
        self.activeConfName = 'standard'
        
        self.controller = controller
        
        # Stores whether the component is currently started
        self.started = False
        
    def start(self, dt=0, duration=-1, configName=None):
        """
        Overwrite this in every child class and call it before doing anything else.
        Sets the self.activeConf to the runConf with the specified name. If configName
        is not given, the standard config is used.
        """
        self.started = True
        if configName:
            # check if we know the passed config
            try:
                self.activeConf = dict.copy(self.runConfs[configName])
                self.activeConfName = configName
            except KeyError:
                raise KeyError('Config "%s" is not known.' % configName)
        else:
            # if no configName is given, use the standard
            self.activeConf = dict.copy(self.runConfs['standard'])
            self.activeConfName = 'standard'
        self.controller.gLogger.logMeStart(self.__module__, self.getName(), self.activeConfName)
        
    def stop(self, dt=0):
        """
        Overwrite this in every child class and call it before doing anything else.
        """
        self.started = False
        self.controller.gLogger.logMeStop(self.__module__, self.getName(), self.activeConfName)
        
    def cleanup(self):
        """
        Overwrite this in child class if the module needs to do some cleaning up
        (e.g. closing connections, file handlers, ...) before it can be destroyed.
        """
        pass
    
    def log(self, logData):
        """
        Wrapper method for logging to the logger of the controller.
        """
        self.controller.gLogger.logMe(self.__module__, self.getName(), logData)
    
    def getName(self):
        """
        Returns the name of this component
        """
        return self.initConf['name']
        
    def getStartingTimes(self):
        """
        Returns the times when the module started [absoluteTime, experimentTime, displayTime]
        """
        return self.controller.gLogger.getStartingTimes(self.getName())
        
        
class DrawableModule(BasicModule):
    """
    Class extending from BasicModule, representing a module that is drawable
    """ 
    def draw(self, window_width, window_height, eye=-1):
        """
        Method to be overwritten by child class
        """
        pass
        
class DrawableHUDModule(DrawableModule):
    """
    Class extending from DrawableModule, representing a module that draws Head UP (in front and orthographic)
    """ 
    def draw(self, window_width, window_height):
        """
        Method to be overwritten by child class
        """
        pass
    
class SourceModule(BasicModule):
    """ 
    Abstract classes for modules representing a sampled source of information.
    This is geared toward tracker classes which sample data at a given frequency
    from external devices or interfaces.
    """
    
    def getData(self):
        """
        Overwrite in child class to return the most-up-to-date data (whatever format)
        """
        return None

    def getUpdateInterval(self):
        """
        Overwrite in child class to return the sampling frequency at which data is being 
        sampled. (i.e. 1 / sampling_rate)
        """
        return None
    
    
class DrawableSourceModule(SourceModule):
    """
    A draw() method is required so that the sensor position(s) can be drawn
    """
    def draw(self, window_width, window_height, eye=-1):
        """
        Method to be overwritten by child class
        """
        pass
        
class DrawableHUDSourceModule(DrawableSourceModule):
    """
    A draw() method is required so that the sensor position(s) can be drawn Head UP (in front and orthographic)
    """
    def draw(self, window_width, window_height):
        """
        Method to be overwritten by child class
        """
        pass