"""
@author: Tobias Leugger
@since: Spring 2010

@attention: Adapted from parts of the PsychoPy library
@copyright: 2009, Jonathan Peirce, Tobias Leugger
@license: Distributed under the terms of the GNU General Public License (GPL).
"""
from copy import deepcopy
from expbuilder.app.param import Param, getParamFromDesc
from expbuilder.app.experiment import ComponentTimeline
from abstract.AbstractClasses import DrawableModule
from abstract.AbstractClasses import DrawableSourceModule


# TODO: (normal) check all values of params

class Component():
    def __init__(self, exp, type, importPath, moduleMain, name=''):
        self.exp = exp # so we can access the experiment if necessary
        self._componentType = type
        self._importPath = importPath
        self._moduleMain = moduleMain
        self._enabled = True
        
        # Check if this is a drawable component
        self._drawable = False
        if issubclass(self._moduleMain, DrawableModule) or issubclass(self._moduleMain, DrawableSourceModule):
            self._drawable = True
        
        self.params = {}
        self.order = []
        self.configs = {}
        
        # Get the init conf from the module main
        initConf = self._moduleMain.defaultInitConf
        for paramDesc in self._moduleMain.confDescription:
            if paramDesc[0] in initConf:
                self.order.append(paramDesc[0])
                self.params[paramDesc[0]] = getParamFromDesc(paramDesc, initConf[paramDesc[0]])
                                                  
        # Prepare the standard experimental config
        self.configs['standard'] = self.getNewConfig('standard')
            
    def __deepcopy__(self, memo):
        # recursion test
        not_there = []
        existing = memo.get(self, not_there)
        if existing is not not_there:
            return existing
        dup = Component(self.exp, self._componentType, self._importPath, self._moduleMain)

        dup.order = deepcopy(self.order)
        dup.configs = deepcopy(self.configs)
        for param in self.params:
            dup.params[param] = deepcopy(self.params[param])
#        dup.params['name'].val += '_bis'
        return dup
                    
    def enabled(self):
        return self._enabled
    
    def toggleEnabled(self):
        self._enabled = not self._enabled
            
    def getNewConfig(self, name):
        """
        Returns a condition config with the given name of this component.
        Sets all the params of the condition config.
        """
        paramSet = ComponentConfig(name)            
        runConf = self._moduleMain.defaultRunConf
        for paramDesc in self._moduleMain.confDescription:
            if paramDesc[0] in runConf:
                paramSet.order.append(paramDesc[0])
                paramSet.addParam(paramDesc[0], getParamFromDesc(paramDesc, runConf[paramDesc[0]]))
        return paramSet
        
    def setConfigs(self, configs):
        """
        Updates the configs of this component with the given ones.
        """
        self.configs = configs
        
    def getType(self):
        return self._componentType
    
    def getName(self):
        return self.params['name'].val
                
    def getNewComponentTimeline(self):
        return ComponentTimeline(self)
    
    

class ComponentConfig:
    def __init__(self, name):
        self.params = {}
        self.order = ['name']
        self.params = {'name': Param(name, valType='str', hint="Name of this config")}
                
    def addParam(self, paramName, param):
        self.params[paramName] = param
        if self.getName() != 'standard':
            param.hasStandard = True
            param.likeStandard = True
        
    def getName(self):
        return self.params['name'].val

    def __deepcopy__(self, memo):
        # recursion test
        not_there = []
        existing = memo.get(self, not_there)
        if existing is not not_there:
            return existing
        dup = ComponentConfig(deepcopy(self.getName()))
        dup.order = deepcopy(self.order)
        for param in self.params:
            dup.params[param] = deepcopy(self.params[param])
            dup.params[param].hasStandard = self.params[param].hasStandard
            dup.params[param].likeStandard = self.params[param].likeStandard
        return dup
       