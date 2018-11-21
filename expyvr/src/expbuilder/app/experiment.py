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
experiment.py
@attention: Adapted from parts of the PsychoPy library
@copyright: 2009, Jonathan Peirce, Tobias Leugger
@author: Tobias, Bruno
@since: Spring 2010
'''

from lxml import etree
from copy import copy, deepcopy
from operator import attrgetter
import random, os

import expbuilder, loops, components, helpers
from expbuilder import preferences
from settings import CameraSettings, WindowSettings, LoggerSettings
from param import Param
from errors import showInfo, showWarning, storeTracebackAndShowError


class Experiment:
    """
    An experiment contains a single Flow and at least one
    Routine. The Flow controls how Routines are organised
    e.g. the nature of repeats and branching of an experiment.
    """
    def __init__(self):
        # this can be checked by the builder that this is an experiment and a compatible version
        self.version = expbuilder.__version__ # imported from components
        self._reset()
        
    def _reset(self):
        """
        Resets the experiment to be empty
        """
        self.flow = Flow(exp=self) # every exp has exactly one flow
        self.routines = []
        self.components = []
        self.cameraSettings = CameraSettings(exp=self)
        self.windowSettings = {}
        self.loggerSettings = LoggerSettings(exp=self)
        setting, name = self.getNewWindowSetting()
        self.windowSettings[name] = setting
        self.activeRoutine = None # the routine that is currently edited
                
    def addRoutine(self, routineName, routine=None):
        """
        Add a Routine to the current list of them.

        Can take a Routine object directly or will create
        an empty one if none is given.
        """
        if routine == None:
            self.routines.appendRoutine(routineName, exp=self) # create a deafult routine with this name
        else:
            self.routines.append(routine)
            
    def getRoutine(self, routineName):
        for routine in self.routines:
            if routine.getName() == routineName:
                return routine
        return None
            
    def removeRoutine(self, routineName):
        for routine in self.routines:
            if routine.getName() == routineName:
                break
        self.routines.remove(routine)
        self.activeRoutine = None
        
    def getComponent(self, componentName):
        for component in self.components:
            if component.getName() == componentName:
                return component
        return None        
    
    def hasComponent(self, componentName):
        for component in self.components:
            if component.getName() == componentName:
                return True
        return False
    
    def removeComponent(self, component):
        """
        Removes a component from the experiment and from all the
        routines that are using it.
        """
        if component in self.components:
            self.components.remove(component)
            for routine in self.routines:
                for condition in routine._conditions:
                    for timeline in condition._componentTimelines:
                        if timeline.component == component:
                            condition.removeComponentTimeline(timeline)
            
    def getNewWindowSetting(self, num=None):
        """
        Returns a new window setting  with a default name. Does not actually add 
        it to the experiment, this has to be done separately
        """
        # Set the name
        if num == None:
            num = len(self.windowSettings) + 1
        name = 'win ' + str(num)
        windowSetting = WindowSettings(exp=self)
        return windowSetting, name
        
    def removeWindowSetting(self, name):
        """
        Deletes the given window setting if it exists
        """
        if name in self.windowSettings:
            del(self.windowSettings[name])

    def getUsedName(self, name):
        """
        Check over all routines, components, loops and isis if the name is 
        already used and return None for unused or the object that used 
        the name otherwise
        """
        # look for routines and loop names
        for flowElement in self.flow:
            if flowElement.getType() in ['LoopInitiator','LoopTerminator']:
                flowElement = flowElement.loop # we want the loop itself
            if str(flowElement.getName()) == name:
                return flowElement
        for routine in self.routines:
            if routine.getName() == name:
                return routine
        for component in self.components:
            if component.getName() == name:
                return component
        return None # we didn't find an existing name :-)
    
    def saveToXML(self, filename):
        # create the dom object
        self.xmlRoot = etree.Element("ExpyVR")
        self.xmlRoot.set('version', self.version)
        self.xmlRoot.set('encoding', 'utf-8')
        self.xmlRoot.set('type', 'experiment')

        # set settings and routines
        self.xmlRoot.append(self._generateSettingsXML())
        self.xmlRoot.append(self._generateCompontensXML())
        self.xmlRoot.append(self._generateRoutinesXML())
                    
        # save the flow
        flowNode = etree.SubElement(self.xmlRoot, 'AbstractExperimentFlow')
        for element in self.flow: # a list of elements(routines and loopInit/Terms)
            elementNode = etree.SubElement(flowNode, element.getType())
            if element.getType() == 'LoopInitiator':
                loop = element.loop
                name = loop.getName()      
                elementNode.set('type',loop.getType())
                elementNode.set('name', name)
                for paramName, param in loop.params.iteritems():
                    self._setXMLparam(parent=elementNode,param=param,name=paramName)
            elif element.getType() == 'LoopTerminator':
                elementNode.set('name', element.loop.getName())
            elif element.getType() == 'Routine':
                elementNode.set('routineName', element.getName())
            elif element.getType() == 'Isi':
                elementNode.set('name', element.getName())
                for paramName, param in element.params.iteritems():
                    self._setXMLparam(parent=elementNode, param=param, name=paramName)
                
        # write to disk
        f = open(filename, 'wb')
        f.write(etree.tostring(self.xmlRoot, encoding=unicode, pretty_print=True))
        f.close()
        
    def generateAllInstances(self, instancesFolder, experimentFilename, generateAllFor=[], num_instances = 0):
        try:
            gen = _InstanceGenerator(self, instancesFolder, experimentFilename, generateAllFor, num_instances)
            gen.generate()
        except:
            storeTracebackAndShowError("An error occurred while generating the instances.")
        else:
            showInfo("%d instances have been successfully generated in the folder\n%s."%(gen.totalInstancesGenerated, gen.instanceFilename))
        
    def generateInstance(self, instanceFilename, experimentFilename):
        try:
            gen = _InstanceGenerator(self, instanceFilename, experimentFilename)
            gen.generate()
        except:
            storeTracebackAndShowError("An error occured while generating the instance.")
                
    def generateRoutineInstance(self, routineName, conditionName, instanceFilename, experimentFilename):
        try:
            gen = _InstanceGenerator(self, instanceFilename, experimentFilename)
            xmlNodes = []
            routineNode = etree.Element('Routine')
            routineNode.set('routineName', routineName)
            routineNode.set('condition', conditionName)
            xmlNodes.append(('Routine', routineNode))
            gen.totalInstancesGenerated = 1
            gen._writeInstanceFile(xmlNodes)
        except:
            storeTracebackAndShowError("An error occured while generating the instance.")
            
    def _generateSettingsXML(self):
        # Store settings
        settingsNode = etree.Element('Settings')
        
        # Store path settings of all extra components
        pathNode = etree.SubElement(settingsNode, 'Python')
        prefs = preferences.Preferences()
        for comppath in prefs.builder['componentsPath'].split(';'):
            pathchild = etree.SubElement(pathNode, "ComponentPath")
            pathchild.set('directory', str(comppath))
            
        # Store logger settings
        loggerNode = etree.SubElement(settingsNode, 'Logger')
        for name in helpers.getCompleteOrder(self.loggerSettings.params, self.loggerSettings.order):
            param = self.loggerSettings.params[name]
            self._setXMLparam(parent=loggerNode, param=param, name=name)
        
        # Store camera settings
        displayNode = etree.SubElement(settingsNode, 'Display')
        cameraNode = etree.SubElement(displayNode, 'Camera')
        for name in helpers.getCompleteOrder(self.cameraSettings.params, self.cameraSettings.order):
            param = self.cameraSettings.params[name]
            self._setXMLparam(parent=cameraNode, param=param, name=name)
        
        # Store windows node
        windowsNode = etree.SubElement(displayNode, 'Windows')
        for windowName in sorted(self.windowSettings.keys()):
            windowNode = etree.SubElement(windowsNode, 'Window')
            windowNode.set('name', windowName)
            
            order = helpers.getCompleteOrder(self.windowSettings[windowName].params,
                                             self.windowSettings[windowName].order)
            for name in order:
                param = self.windowSettings[windowName].params[name]
                self._setXMLparam(parent=windowNode, param=param, name=name)
        
        return settingsNode
    
    def _generateCompontensXML(self):
        componentsNode = etree.Element('Components')
        for component in self.components:
            # Set the basic info
            componentNode = etree.SubElement(componentsNode, 'Component')
            componentNode.set('type', component.getType())
            componentNode.set('importPath', component._importPath)
            componentNode.set('name', component.getName())
            componentNode.set('enabled', 'True' if component.enabled() else 'False')
            
            # Add the init config
            initConfigNode = etree.SubElement(componentNode, 'InitConfig')
            for name, param in component.params.iteritems():
                self._setXMLparam(parent=initConfigNode, param=param, name=name)
                
            # Add all the configs
            configsNode = etree.SubElement(componentNode, 'Configs')
            for setName in sorted(component.configs.keys()):
                configNode = etree.SubElement(configsNode, 'Config')
                configNode.set('name', setName)
                for name, param in component.configs[setName].params.iteritems():
                    if name != 'name' and not param.likeStandard:
                        self._setXMLparam(parent=configNode, param=param, name=name)
        return componentsNode
        
    def _generateRoutinesXML(self):
        routinesNode = etree.Element('Routines')
        for routine in self.routines:
            routineNode = etree.SubElement(routinesNode, 'Routine')
            routineNode.set('name', routine.getName())
            
            # Add all the conditions
            conditionsNode = etree.SubElement(routineNode, 'Conditions')
            for condition in routine._conditions:
                conditionNode = etree.SubElement(conditionsNode, 'Condition')
                conditionNode.set('name', condition.getName())
                
                # Add the componentTimelines and the flow of this condition (activations and display times of all components)
                conditionCompNodes = etree.SubElement(conditionNode, 'UsedComponents')
                routineFlowNode = etree.SubElement(conditionNode, 'RoutineFlow')
                occurenceNodes = []
                for timeline in condition._componentTimelines:
                    # Store info about order of condition components
                    timelineNode = etree.SubElement(conditionCompNodes, 'UsedComponent')
                    timelineNode.set('componentName', timeline.component.getName())
                    timelineNode.set('configName', condition.getConfig(timeline))
                    timelineNode.set('isGrouped', str(timeline.numConditionsInGroup > 0))
                    
                    # Activations and display times can be treated the same way
                    allOccurences = copy(timeline._activations) # Make a local shallow copy
                    allOccurences.extend(timeline._displayTimes)
                    for occurence in allOccurences:
                        occurenceNode = etree.Element('Occurence')
                        occurenceNode.set('type', occurence.type)
                        occurenceNode.set('componentName', timeline.component.getName())
                        occurenceNode.set('startTime', str(occurence.params['startTime'].val))
                        occurenceNode.set('duration', str(occurence.params['duration'].val))
                        occurenceNodes.append(occurenceNode)
                routineFlowNode[:] = sorted(occurenceNodes, key = lambda node: node.get('startTime'))
        return routinesNode
        
    def _setXMLparam(self, parent, param, name):
        """
        Add a new child to a given xml node.
        name can include spaces and parens, which will be removed to create child name
        """
        if hasattr(param, 'getType'):
            thisType = param.getType()
        else:
            thisType = 'Param'
        thisChild = etree.SubElement(parent, thisType) # creates and appends to parent
        thisChild.set('name', name)
        if hasattr(param, 'val'):
            thisChild.set('val', str(param.val))
        if hasattr(param, 'valType'):
            thisChild.set('valType', str(param.valType))
        return thisChild
    
    def _getXMLparam(self, params, paramNode):
        """params is the dict of params of the builder component (e.g. stimulus) into which
        the parameters will be inserted (so the object to store the params should be created first)
        paramNode is the parameter node fetched from the xml file
        """
        name = paramNode.get('name')
        if 'val' in paramNode.keys() and params.has_key(name):
            params[name].setVal(paramNode.get('val'))
            if params[name].hasStandard:
                params[name].likeStandard = False

           
    def importComponentsFromXML(self, filename, excludelist = []):
        """
        Open an xml experiment file, read the components, and add them to the current experiment.
        """
        # open the file using a parser that ignores prettyprint blank text
        parser = etree.XMLParser(remove_blank_text=True)
        f = open(filename)
        root = etree.XML(f.read(), parser)
        f.close()
        
        version = root.get('version')
        if version != self.version:
            showWarning("ExpyVR is version %s, the experiment you're loading is version %s. This might cause some problems" % (self.version, version))
        type = root.get('type')
        
        
        # Fetch experiment components
        componentsNode = root.find('Components')
        for componentNode in componentsNode:              
            # ensure no duplicated names
            newname = componentNode.get('name')
            # pass if in the exclude list
            if excludelist.count(newname) != 0:
                continue 
            # create a bis name if already same name exists
            while self.hasComponent(newname):
                newname += "_bis"
            # create new component
            component = components.getNewComponent(self, componentNode.get('type'), newname)
            # Toggle if not enabled
            if componentNode.attrib.has_key('enabled') and not eval(componentNode.attrib['enabled']):
                component.toggleEnabled()
                
            # Populate the component with its various params
            for paramNode in componentNode.find('InitConfig'):
                self._getXMLparam(component.params, paramNode)
            # update name field
            component.params.get('name').setVal(newname)
            
            # Insert all the configs
            configs = {}
            for configNode in componentNode.find('Configs'):
                configName = configNode.get('name')
                configs[configName] = component.getNewConfig(configName)
                for paramNode in configNode:
                    self._getXMLparam(configs[configName].params, paramNode)
            component.setConfigs(configs)
            
            # Add the component to the experiment
            self.components.append(component)
            
    def loadFromXML(self, filename):
        """
        Loads an xml file and parses the experiment from it
        """
        # open the file using a parser that ignores prettyprint blank text
        parser = etree.XMLParser(remove_blank_text=True)
        f = open(filename)
        root = etree.XML(f.read(), parser)
        f.close()
        
        version = root.get('version')
        if version != self.version:
            showWarning("ExpyVR is version %s, the experiment you're loading is version %s. This might cause some problems" % (self.version, version))
        type = root.get('type')
        
        # Parse document nodes
        # first make sure we're empty
        self._reset()
        # fetch exp settings
        settingsNode = root.find('Settings')
        loggerNode = settingsNode.find('Logger')
        cameraNode = settingsNode.find('Display/Camera')
        windowsNode = settingsNode.findall('Display/Windows/Window')
        
        if cameraNode is not None:
            for node in cameraNode:
                self._getXMLparam(self.cameraSettings.params, node)
        
        for node in loggerNode:
            self._getXMLparam(self.loggerSettings.params, node)
        
        self.windowSettings = {}
        for windowNode in windowsNode:
            window = WindowSettings(exp=self)
            windowName = windowNode.get('name')
            for node in windowNode:
                self._getXMLparam(window.params, node)
            self.windowSettings[windowName] = window
        
        # Fetch experiment components
        componentsNode = root.find('Components')
        for componentNode in componentsNode:              
            component = components.getNewComponent(self, componentNode.get('type'), componentNode.get('name'))
            # Toggle if not enabled
            if componentNode.attrib.has_key('enabled') and not eval(componentNode.attrib['enabled']):
                component.toggleEnabled()
                
            # Populate the component with its various params
            for paramNode in componentNode.find('InitConfig'):
                self._getXMLparam(component.params, paramNode)
            
            # Insert all the configs
            configs = {}
            for configNode in componentNode.find('Configs'):
                configName = configNode.get('name')
                configs[configName] = component.getNewConfig(configName)
                for paramNode in configNode:
                    self._getXMLparam(configs[configName].params, paramNode)
            component.setConfigs(configs)
            
            # Add the component to the experiment
            self.components.append(component)
            
        # Fetch routines
        routinesNode = root.find('Routines')
        for routineNode in routinesNode: # get each routine node from the list of routines
            # then create and add the routine
            routine = Routine(name=routineNode.get('name'), exp=self)
            self.routines.append(routine)
        
        # Fetch flow settings (do this first so we know all the loop vars)
        flowLoops = {}
        for elementNode in root.find('AbstractExperimentFlow'):
            if elementNode.tag == "LoopInitiator":
                loopType = elementNode.get('type')
                loopName = elementNode.get('name')
                loop = None
                exec('loop=loops.%s(exp=self,name="%s")' %(loopType,loopName))
                flowLoops[loopName]=loop
                for paramNode in elementNode:
                    self._getXMLparam(paramNode=paramNode,params=loop.params)
                self.flow.append(LoopInitiator(loop=flowLoops[loopName]))
            elif elementNode.tag == "LoopTerminator":
                self.flow.append(LoopTerminator(loop=flowLoops[elementNode.get('name')]))
            elif elementNode.tag == "Routine":
                routineName = elementNode.get('routineName')
                self.flow.append(self.getRoutine(routineName))
            elif elementNode.tag == "Isi":
                isi = Isi(exp=self, name=elementNode.get('name'))
                for paramNode in elementNode:
                    self._getXMLparam(paramNode=paramNode, params=isi.params)
                self.flow.append(isi)
        # Update all the loop vars in all the routines
        self.flow.updateLoopVars()
        
        # Now we can parse the condition loop vars and timelines
        for routine in self.routines:
            # Populate all the conditions of this routine
            for conditionNode in root.findall('Routines/Routine[@name="' + routine.getName() + '"]/Conditions/Condition'):
                # Get the condition
                conditionName = conditionNode.get('name')
                condition = routine.getConditionByName(conditionName)
                if condition == None:
                    showWarning("The condition '%s' has a name that cannot be mapped to any loops. " % conditionName + 
                                "The loaded experiment will not contain this condition.")
                    continue
                
                # Add all the components used in this condition
                for timelineNode in conditionNode.findall('UsedComponents/UsedComponent'):
                    componentName = timelineNode.get('componentName')
                    component = self.getComponent(componentName)
                    componentTimeline = component.getNewComponentTimeline()
                    addToGroup = False 
                    if timelineNode.get('isGrouped') == 'True':
                        addToGroup = True
                    condition.addComponentTimeline(componentTimeline, addToGroup)
                    condition.setConfig(componentTimeline, timelineNode.get('configName'))
                
                # Add all activations and display times
                for componentTimeline in condition._componentTimelines:
                    activationsToAdd = []
                    displayTimesToAdd = []
                    for occurence in conditionNode.findall('RoutineFlow/Occurence[@componentName="' + componentTimeline.component.getName() + '"]'):
                        duration = occurence.get('duration')
                        startTime = occurence.get('startTime')
                        if occurence.get('type') == 'activation':
                            activationsToAdd.append(componentTimeline.getNewActivation(startTime, duration))
                        else: # it's a "display"
                            displayTimesToAdd.append(componentTimeline.getNewDisplayTime(startTime, duration))
                    componentTimeline.updateActivations(activationsToAdd)
                    componentTimeline.updateDisplayTimes(displayTimesToAdd)
        
        # Open some routine
        if len(self.routines) > 0:
            self.activeRoutine = self.routines[0]



class _InstanceGenerator:
    
    LIMITING_FACTOR = 5
    """
    The InstanceGenerator is used to generate instances of an experiment. This
    means it goes through all the loops in the flow, applies the randomisation
    and generates linearised flows that are stored to XML.
    It can also generate all possible instances of an experiment regarding some
    ShuffleLoops and FactorialLoops.
    """
    def __init__(self, experiment, instanceFilename, experimentFilename, generateAllFor=[], num_instances = 0):
        self.experiment = experiment
        self.instanceFilename = instanceFilename
        self.experimentFilename = experimentFilename
        self.generateAllFor = generateAllFor
        self.num_instances = num_instances
        
        self.curInstanceNum = 1
        self.totalInstancesGenerated = 0
        
        self.message = ""
    
    def generate(self):
        # First find out how often loop that are shuffled are repeated
        loopRepeatCount = self._followFlow()
        
        # Generate all combinations for all loops that are shuffled individually
        allCombinations = {}
        for loopName in self.generateAllFor:
            loop = self.experiment.flow.getLoopFromName(loopName)
            allRandomisations = self._makeLoopVarRandomisations(loop.getSet())
            allCombinations[loopName] = self._combineMultipleLoopOccurences(allRandomisations, loopRepeatCount[loopName])
            
            # bhbn; limiting combinatory explosion (attempt)
            if len(allCombinations[loopName]) > self.num_instances * self.LIMITING_FACTOR:
                random.shuffle(allCombinations[loopName])
                allCombinations[loopName] = allCombinations[loopName][0:self.num_instances * self.LIMITING_FACTOR]
        
        # Now combine the possibilities of the different loops together
        finalCombinations = self._combineDifferentLoops(allCombinations)
        
        # Shuffle the combinations
        random.shuffle(finalCombinations)
        
        # cut the number of combinations to the max required
        if self.num_instances > 0:
            finalCombinations = finalCombinations[0:self.num_instances]
            
        # Set how many instances we're going to generate (used for the filename)
        self.totalInstancesGenerated = len(finalCombinations)
        
        # Finally, generate all the XMLs
        for combination in finalCombinations:
            self._followFlow(generate=True, fixedLoopVars=combination, interleave_shuffle = True)
        
        # Show warning message if there is any
        if self.message:
            showWarning(self.message)

    def _followFlow(self, generate=False, fixedLoopVars={}, interleave_shuffle = False):
        """
        Follows the experiment flow as if the experiment was actually running.
        If generate is True, it will store an instance XML using the specified
        fixedLoopVars or using random ones for the loops that no loop vars are
        given.
        @return: A dictionary which maps from the names of all the loops that
        are shuffled to number of times that this loop is repeated
        """
        loopRepeatCount = {}
        
        xmlNodes = []
        loopVars = {}
        
        loopStarts = {}
        loopsPassed = {}
        i = 0
        
        # Go through the flow and follow the loops as required
        while i < len(self.experiment.flow):
            element = self.experiment.flow[i]
            if element.getType() == 'LoopInitiator':
                name = element.loop.getName()
                if element.loop.generateAll:
                    if name not in loopRepeatCount:
                        # encounter the loop the first time
                        loopRepeatCount[name] = 0
                    loopRepeatCount[name] += 1
                if generate:
                    # Get the loop variables used in this pass of the loop
                    if name in fixedLoopVars:
                        # If the loop vars are specfied in the fixed ones, use that
                        loopVars[name] = fixedLoopVars[name][loopRepeatCount[name] - 1]
                    elif element.loop.hasLoopVar:
                        # Otherwise get the set from the loop directly
                        loopVars[name] = element.loop.getSet()
                
                # Store the start of this loop to be able to go back to the start
                loopStarts[name] = i
                loopsPassed[name] = 0
            elif element.getType() == 'LoopTerminator':
                name = element.loop.getName()
                loopsPassed[name] += 1
                if loopsPassed[name] == element.loop.getNumReps():
                    # If we have followed this loops as often as specified, stop following it
                    if name in loopVars:
                        del(loopVars[name])
                    del(loopStarts[name])
                    del(loopsPassed[name])
                else:
                    # We still have to follow this loop, go back to the start
                    i = loopStarts[name]
            
            if generate:
                # If we're generating the XML, make the nodes for ISIs and routines
                if element.getType() == 'Isi':
                    xmlNodes.append(('Isi', element.getXML()))
                elif element.getType() == 'Routine':
                    # Get the current loop vars
                    currentLoopVars = {}
                    for loopName, loopSet in loopVars.iteritems():
                        currentLoopVars[loopName] = loopSet[loopsPassed[loopName]]
                        
                    # Construct the routine node
                    conditionName = element.getConditionByLoopVars(currentLoopVars).getName()
                    routineNode = etree.Element('Routine')
                    routineNode.set('routineName', element.getName())
                    routineNode.set('condition', conditionName)
                    xmlNodes.append(('Routine', routineNode))
            # Continue to the next element int the flow
            i += 1
        
        if generate:
            # If we're generating the xml, write it now
            self._writeInstanceFile(xmlNodes)
            
        return loopRepeatCount

    def _writeInstanceFile(self, nodes):
        """
        Writes an instance file with the given experiment flow nodes
        """
        # Create the root
        xmlRoot = etree.Element("ExpyVR")
        xmlRoot.set('version', self.experiment.version)
        xmlRoot.set('encoding', 'utf-8')
        xmlRoot.set('type', 'instance')
        
        # Get the filename to write to
        instanceFilename = self._getNextFilename()
        
        # Write where the experiment file is located relatively to the instance
        expRelPath = os.path.relpath(self.experimentFilename, os.path.dirname(instanceFilename))
        expNode = etree.SubElement(xmlRoot, 'Experiment')
        expNode.set('fileName', expRelPath)
        
        # Create the flow element
        flowNode = etree.SubElement(xmlRoot, 'ExperimentFlow')
        for elem in nodes:
            flowNode.append(elem[1])
        
        # Write to disk
        f = open(instanceFilename, 'wb')
        f.write(etree.tostring(xmlRoot, encoding=unicode, pretty_print=True))
        f.close()
        
    def _getNextFilename(self):
        """
        Returns the filename that should be used for the next instance
        """
        if self.totalInstancesGenerated == 1:
            # If we only generate one instance, we should have gotten the filename
            # directly in the constructor
            return self.instanceFilename
        
        filename = os.path.basename(self.experimentFilename).split('.')[0] + "-"
        filename += str(self.curInstanceNum).zfill(len(str(self.totalInstancesGenerated)))
        self.curInstanceNum += 1
        filename = os.path.join(self.instanceFilename, filename + ".inst.xml")
        if os.path.exists(filename):
            # warn only once
            if not len(self.message):
                self.message += "Some instance files already existed in %s.\n New instance files have been added by number.\n" % self.instanceFilename
            # Don't override existing files
            return self._getNextFilename() 
        return filename

    def _makeLoopVarRandomisations(self, list):
        """
        Recursive method to generate all possible randomisations (shuffled) of
        the given list of strings
        """
        if len(list) == 1:
            return [list]
        
        randomisations = []
        for name in list:
            newList = copy(list)
            newList.remove(name)
            innerRands = self._makeLoopVarRandomisations(newList)
            for innerRand in innerRands:
                innerRand.append(name)
            randomisations.extend(innerRands)
        return randomisations
    
    def _combineMultipleLoopOccurences(self, loopVarRands, num, generatedCombinations=[[]]):
        """
        Recursive method that generates all possible randomisations if the loop
        represented by the loopVarRands is repeated num number of times.
        The generatedCombinations is used internally for the recursive calls.
        """
        newGeneratedCombinations = []
        for comb in generatedCombinations:
            for rand in loopVarRands:
                cp = deepcopy(comb)
                cp.append(rand)
                newGeneratedCombinations.append(cp)
                # bhbn; limiting combinatory explosion (attempt)
                if len(newGeneratedCombinations) > self.num_instances  * self.LIMITING_FACTOR:
                    break
                
        # bhbn; limiting combinatory explosion (attempt)
        if len(newGeneratedCombinations) > self.num_instances  * self.LIMITING_FACTOR:
            random.shuffle(newGeneratedCombinations)
            newGeneratedCombinations = newGeneratedCombinations[0:self.num_instances * self.LIMITING_FACTOR]
            
        # recursion stop condition    
        if num <= 1:
            return newGeneratedCombinations
        # recursion
        return self._combineMultipleLoopOccurences(loopVarRands, num - 1, newGeneratedCombinations)
    
    def _combineDifferentLoops(self, individualLoopCombinations):
        """
        Generate all combinations of how the loop variables from different loops
        can be shuffled.
        """
        final = [{}]
        for loopName in self.generateAllFor:
            newFinal = []
            for comb in individualLoopCombinations[loopName]:
                for elem in final:
                    cp = deepcopy(elem)
                    cp[loopName] = deepcopy(comb)
                    newFinal.append(cp)
            final = newFinal

        return final


    
class Flow(list):
    """
    The flow of the experiment is a list of L{Routine}s, L{LoopInitiator}s,
    L{LoopTerminator}s and L{Isi}s, that will define the order in which events occur
    """
    def __init__(self, exp):
        list.__init__(self)
        self.exp = exp
        
    def addOrMoveLoop(self, loop, startPos, endPos):
        """
        Adds initiator and terminator objects for the loop
        into the Flow list or moves the loop to the new position
        if it's already in the list
        """
        # Check if we already have this loop
        oldStartPos, oldEndPos = self.getLoopPosition(loop)
        startPos = int(startPos)
        endPos = int(endPos)
        if oldStartPos == None:
            # We don't have this loop yet, simply insert it
            self.insert(endPos, LoopTerminator(loop))
            self.insert(startPos, LoopInitiator(loop))
        else:
            # We already have this loop, remove the old one and re-insert at the new position
            terminator = self.pop(oldEndPos)
            initiator = self.pop(oldStartPos)
            # Because we just removed two elements from the flow, we have to play around
            # with the indices a bit
            if oldEndPos < startPos:
                startPos -= 2
            elif oldStartPos < startPos:
                startPos -= 1
            if oldEndPos < endPos:
                endPos -= 2
            elif oldStartPos < endPos:
                endPos -= 1
            self.insert(endPos, terminator)
            self.insert(startPos, initiator)
        # Loop vars might have changed
        self.updateLoopVars()
                
    def addOrMoveElement(self, element, position):
        """
        Moves the given element (a routine or an isi) to the given position 
        or inserts it if it isn't in the flow yet
        """
        position = int(position)
        if self.count(element) == 0:
            # the element is not in the flow yet, insert it
            self.insert(position, element)
        else:
            # the element is already in the flow, we might have to move it
            oldPosition = self.index(element)
            if oldPosition == position:
                # position stayed the same, do nothing
                return
            # remove it and re-insert it at the new place
            self.remove(element)
            if oldPosition > position:
                self.insert(position, element)
            else:
                self.insert(position - 1, element)
        self.updateLoopVars()
                
    def getLoopPosition(self, loop):
        """
        Return a tuple of two integers representing the start 
        and the end of the given loop. If the loop is not found
        None, None is returned
        """
        start, end = None, None
        for element in self:
            if element.getType() in ['LoopInitiator','LoopTerminator'] and element.loop == loop: 
                if element.getType() == 'LoopInitiator':
                    start = self.index(element)
                else:
                    end = self.index(element)
        return start, end
        
    def getLoopFromName(self, name):
        """
        Returns the loop with the given name
        """
        for element in self:
            if element.getType() in ['LoopInitiator','LoopTerminator'] and element.loop.getName() == name: 
                return element.loop;
        return None
        
    def removeComponent(self, component):
        """
        Removes a Loop, Routine or Isi from the flow
        """
        if component.getType() in ['LoopInitiator', 'LoopTerminator']:
            # Set the loop as component and continue to do the next
            component = component.loop
        if isinstance(component, loops._BaseLoop):
            # We need to remove the termination points that correspond to the loop
            for comp in list(self):
                if comp.getType() in ['LoopInitiator','LoopTerminator'] and comp.loop == component: 
                    self.remove(comp)
        elif component.getType() in ['Routine', 'Isi']:
            self.remove(component)
        self.updateLoopVars()
            
    def updateLoopVars(self):
        """
        Updates all the routines in the flow with the new loop variables 
        of the loops that they are inside of
        """
        currentLoops = []
        for element in self:
            # Go through all the elements and tell the routines about the loops they're in
            if element.getType() == 'Routine':
                element.updateSurroundingLoops(currentLoops)
            elif element.getType() == 'LoopInitiator' and element.loop.hasLoopVar:
                currentLoops.append(element.loop)
            elif element.getType() == 'LoopTerminator' and element.loop.hasLoopVar:
                currentLoops.remove(element.loop)



class Routine():
    """
    A Routine determines a single sequence of events, such
    as the presentation of trial. Multiple Routines might be
    used to comprise an Experiment (e.g. one for presenting
    instructions, one for trials, one for debriefing subjects).

    In practice a Routine is simply a python list of Components,
    each of which knows when it starts and stops.
    """
    def __init__(self, name, exp):
        self.order = ['name']
        self.params = {'name': Param(name, valType='str', hint="Name of the routine")}
        self.exp = exp
        self._surroundingLoops = []
        self._conditions = []
        self._groupedComponentTimelines = {}
            
    def updateSurroundingLoops(self, newLoops):
        """
        Updates the surrounding loops with the passed ones and updates the 
        conditions accordingly. The passes loops should be ordered by their
        start position in the flow.
        """
        # Set the new loops
        self._surroundingLoops = copy(newLoops)
        
        # Update all the existing conditions
        newConditions = []
        for cond in self._conditions:
            if cond.updateInvolvedLoops(self._surroundingLoops):
                # This conditions still exists, add it
                newConditions.append(cond)
        
        # Generate all the indices we should have conditions for
        indices = [[]]
        for loop in self._surroundingLoops:
            newIndices = []
            for index in indices:
                for i in range(len(loop.getLoopVarValues())):
                    cp = copy(index)
                    cp.append(i)
                    newIndices.append(cp)
            indices = newIndices
        
        # Create all the conditions that we don't have yet
        self._conditions = []
        for index in indices:
            cond = next((cond for cond in newConditions if cond._loopVarIndices == index), None)
            if cond == None:
                cond = ExperimentalCondition(self, self._surroundingLoops, index)
            self._conditions.append(cond)
        
        # Sort the conditions by name
        self._conditions.sort(key=attrgetter('_name'))
            
    def addToGroup(self, componentTimeline):
        """
        Checks if the component of the given componentTimeline already has a
        group. If yes the componentTimeline of the group is updated and returned.
        Otherwise the componentTimeline is taken as the one for the new group.
        """
        compName = componentTimeline.component.getName()
        if compName not in self._groupedComponentTimelines:
            self._groupedComponentTimelines[compName] = componentTimeline
        self._groupedComponentTimelines[compName].numConditionsInGroup += 1
        return self._groupedComponentTimelines[compName]
    
    def removeFromGroup(self, timeline):
        """
        Removes one from the number of conditions in the group of the
        componentTimeline passed. If the group is now empty it is removed and
        the same componentTimeline is returned. If there is still a group, a
        new componentTimeline is created and returned
        """
        timeline.numConditionsInGroup -= 1
        if timeline.numConditionsInGroup <= 0:
            del self._groupedComponentTimelines[timeline.component.getName()]
            return timeline
        return timeline.getDuplicate()
    
    def getGroupedTimeline(self, component):
        """
        If there is a group for the given component the corresponding
        timeline is returned, otherwise None
        """
        if component.getName() in self._groupedComponentTimelines:
            return self._groupedComponentTimelines[component.getName()]
        return None
    
    def getConditionsInGroup(self, timeline):
        """
        Returns a list of the names of all conditions that have the given
        timeline.
        """
        group = self.getGroupedTimeline(timeline.component)
        conds = []
        if group == timeline:
            for condition in self._conditions:
                if timeline == condition.containsComponent(timeline.component):
                    conds.append(condition.getName())
        return conds
    
    def getConditionByLoopVars(self, loopNamesToLoopVars):
        try:
            loopVars = []
            for loop in self._surroundingLoops:
                loopVars.append(loopNamesToLoopVars[loop.getName()])
                    
            cond = next((cond for cond in self._conditions if cond._loopVarValues == loopVars))
        except:
            raise Exception("No loop exists for loop vars %s in routine '%s'" % (str(loopNamesToLoopVars), self.getName()))
        return cond
        
    def getConditionByName(self, conditionName):
        return next((cond for cond in self._conditions if cond._name == conditionName), None)

    def getType(self):
        return 'Routine'
    
    def getName(self):
        return self.params['name'].val



class ExperimentalCondition:
    def __init__(self, routine, involvedLoops=[], indices=[]):
        self.routine = routine
        self._componentTimelines = []
        self._componentConfigs = {} # keys: component, values: name of config used
        
        self._loops = copy(involvedLoops)       # list of loops surrounding this conditions routine
        self._loopVarIndices = copy(indices)    # list of indices: determines which loop var value this condition has
        self._loopVarValues = []                # list of loop var values: the loop var values this condition has
        self._name = ""
        self._updateNames()
        
    def getName(self):
        return self._name
    
    def updateInvolvedLoops(self, involvedLoops):
        """
        Updates the loops, loop var values and loop var indices of thi condition
        @return: False if this condition can no longer exist, True otherwise
        """
        newIndices = []
        for loop in involvedLoops:
            loopVars = loop.getLoopVarValues()
            if loop in self._loops:
                index = self._loopVarIndices[self._loops.index(loop)]
                if index >= len(loopVars):
                    # This condition doesn't exist anymore
                    return False
            else:
                index = 0
            newIndices.append(index)
        self._loops = copy(involvedLoops)
        self._loopVarIndices = newIndices
        self._updateNames()
        return True
        
    def _updateNames(self):
        """
        Updates the name and the name of the loop vars of this condition
        """
        self._loopVarValues = []
        for i in range(len(self._loops)):
            loopVars = self._loops[i].getLoopVarValues()
            self._loopVarValues.append(loopVars[self._loopVarIndices[i]])
        self._name = '-'.join(self._loopVarValues)
        if self._name == "":
            self._name = "default"
            
    def getMaxTime(self):
        """
        What the last (predetermined) stimulus time to be presented. If 
        there are no components or they have code-based times then will default
        to 10secs
        """      
        maxTime = 0
        for componentTimeline in self._componentTimelines:
            maxTime = max(maxTime, componentTimeline.getEndTime())
        if maxTime == 0: # if there are no components
            maxTime = 10
        return maxTime
    
    def containsComponent(self, component):
        """
        Checkes whether this routine already has a componentTimeline of the
        passed component, if yes returns the componentTimeline otherwise None
        """
        for componentTimeline in self._componentTimelines:
            if componentTimeline.component == component:
                return componentTimeline
        return None;
    
    def addComponentTimeline(self, componentTimeline, addToGroup=False):
        """
        Add the componentTimeline to this condition and to the group if
        specified.
        """
        if addToGroup:
            componentTimeline = self.routine.addToGroup(componentTimeline)
        self._componentTimelines.append(componentTimeline)
        self._componentConfigs[componentTimeline.component] = 'standard'
    
    def removeComponentTimeline(self, componentTimeline):
        """
        Removes the componentTimeline from this condition and from the group
        if it's in a group
        """
        if componentTimeline in self._componentTimelines:
            if componentTimeline.isInGroup():
                self.routine.removeFromGroup(componentTimeline)
            self._componentTimelines.remove(componentTimeline)
            del self._componentConfigs[componentTimeline.component]
            
    def getConfig(self, componentTimeline):
        if componentTimeline in self._componentTimelines:
            return self._componentConfigs[componentTimeline.component]
        return None
    
    def setConfig(self, componentTimeline, configName):
        self._componentConfigs[componentTimeline.component] = configName



class ComponentTimeline:
    """
    Represents a component within a condition
    """   
    def __init__(self, component, startTime=0.0, duration=1.0):
        self.component = component
        self.numConditionsInGroup = 0
        self._activations = []
        self._displayTimes = []
        
        # Add the first activation of this component
        self._activations.append(self.getNewActivation(startTime, duration))
        if self.isDrawable():
            # If it's drawable, add a first display time
            self._displayTimes.append(self.getNewDisplayTime(startTime, duration))
                
    def updateActivations(self, activations):
        """
        Updates the activations of this component with the given ones.
        Sorts the list according to the start time of the activations
        and changes the activation numbers accordingly
        """
        self._activations = sorted(activations, key = lambda activation: activation.params['startTime'].val)
        for i, activation in enumerate(self._activations):
            # update the activation number
            activation.num = i + 1
    
    def getNewActivation(self, startTime=0.0, duration=1.0, num=None):
        if num == None:
            num = len(self._activations) + 1
        newActivation = ComponentOccurence('activation', startTime, duration, num)
        return newActivation
    
    def updateDisplayTimes(self, displayTimes):
        """
        Updates the display times of this component with the given ones.
        Sorts the list according to the start time of the display time
        and changes the display time numbers accordingly
        """
        self._displayTimes = sorted(displayTimes, key = lambda displayTime: displayTime.params['startTime'].val)
        for i, dispTime in enumerate(self._displayTimes):
            # update the display time number
            dispTime.num = i + 1
    
    def getNewDisplayTime(self, startTime=0.0, duration=1.0 , num=None):
        if num == None:
            num = len(self._displayTimes) + 1
        newDispTime = ComponentOccurence('display', startTime, duration, num)
        return newDispTime
    
    def getEndTime(self):
        maxTime = 0
        for activation in self._activations:
            maxTime = max(maxTime, activation.getEndTime())
        if self.isDrawable():
            for displayTime in self._displayTimes:
                maxTime = max(maxTime, displayTime.getEndTime())
        return maxTime
    
    def getComponentName(self):
        """
        Returns the name of the component of this condition component
        """
        return self.component.getName()
    
    def getDuplicate(self):
        """
        Returns another ComponentTimeline that belongs to the same component
        and has the same activations and displayTimes but is not in a group.
        """
        duplicate = ComponentTimeline(self.component)
        duplicate._activations = deepcopy(self._activations)
        duplicate._displayTimes = deepcopy(self._displayTimes)
        return duplicate
    
    def isDrawable(self):
        return self.component._drawable
    
    def isInGroup(self):
        return self.numConditionsInGroup > 0



class ComponentOccurence:
    """
    An occurence (activation or display timing) of a component with 
    start time and duration
    """
    def __init__(self, type, startTime = 0.0, duration = 1.0, num = 0):
        self.num = num
        self.type = type
        if self.type == 'display':
            hintStart = "The time in seconds when the component is displayed"
            hintDuration = "The time in seconds that the component is displayed (-1 for infinity)"
        else: # type == 'activation'
            hintStart = "The time in seconds when the component is activated"
            hintDuration = "The time in seconds that the component is active for (-1 for infinity)"
        
        # add the params
        self.params = {}
        self.params['startTime'] = Param(float(startTime), valType='float', hint=hintStart)
        self.params['duration'] = Param(float(duration), valType='float', hint=hintDuration)
        
        # make startTime come before duration
        self.order = ['startTime', 'duration']
        
    def getEndTime(self):
        dur = self.params['duration'].val
        if dur < 0:
            # If duration is negative (infinite), say it lasts 1 second
            dur = 1
        return self.params['startTime'].val + dur
    
    def getName(self):
        return self.type + ' ' + str(self.num)



class LoopInitiator:
    """
    A simple class for inserting into the flow.
    This is created automatically when the loop is created
    """
    def __init__(self, loop):
        self.loop = loop
        self.exp = loop.exp
        
    def getType(self):
        return 'LoopInitiator'
    
    
    
class LoopTerminator:
    """
    A simple class for inserting into the flow.
    This is created automatically when the loop is created
    """
    def __init__(self, loop):
        self.loop = loop
        self.exp = loop.exp
        
    def getType(self):
        return 'LoopTerminator'
    
    
    
class Isi:
    """
    An Inter Stymulus Interval
    """
    def __init__(self, exp, name, durationMin=0.1, durationMax=0.2):
        """
        @param name: name of the loop e.g. trials
        @type name: string
        @param set: Set of durations for the intervals (comas separated list of durations, in sec)
        @type set: string
        @param randomize: Randomize the order of intervals 
        @type randomize: bool
        """
        self.type = 'Isi'
        self.exp = exp
        self.order = ['name', 'set', 'randomize'] # order of the params
        self.params = {}
        self.params['name'] = Param(name, valType='str', hint="Name of this Inter Stimulus Interval")
        self.params['set'] = Param("0.1, 0.2, 0.3", valType='str', hint="Set of durations for the intervals (comas separated list of durations, in sec)")
        self.params['randomize'] = Param(True, valType='bool', hint="Randomize the order of intervals of the set")

        self.pool = []
        
    def getType(self):
        return self.type
    
    def getName(self):        
        # little trick to reset the pool each time the xml tree is regenerated
        self.pool = []
        return self.params['name'].val
    
    def getXML(self):
        """
        Returns an etree Element (XML node) representing this ISI
        """
        # create the node and set the name
        node = etree.Element('Isi')
        # node.set('name', self.getName())
        node.set('name', self.params['name'].val)
        
        # if the pool of isi is empty, fill it with the set
        if len(self.pool)<1:
            self.pool = self._getListFromInput(self.params['set'].val)
            self.pool.reverse()
            # the case of the empty set : put a zero
            if len(self.pool) < 0 :
                self.pool = [0.0]
            # randomize set if requested
            if self.params['randomize'].val:
                random.shuffle(self.pool)
                
        # pop one value from the pool
        node.set('duration', str(self.pool.pop()))
        return node
        
    
    def _getListFromInput(self, input):
        """
        Splits the input at commas and sanitises the values.
        """
        return input.replace(' ', '').replace('-', '_').split(',')
        