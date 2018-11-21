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
maincontrol.py
ExpyVR Main Controller 
Centralized controller for all experimental modules in the ExpyVR toolkit

Created on Nov 23, 2010
@author: Nathan

'''

"""
Imports
"""
import os, imp, pyglet, sys
import numpy as np
import random
from pyglet import clock                        #scheduler
from lxml import etree                          #xml parsing
from collections import deque

#Main Modules
from abstract.AbstractClasses import BasicModule
from logger import mainlogger
from display import maindisplay, renderer
from display.mode import *

from excepts import *                           #local exception handlers
from timeManager import TimeManager
from keyboardListener import KeyboardListener
from mouseListener import MouseListener
from abstract.AbstractClasses import DrawableHUDModule, DrawableHUDSourceModule
from controller import getPathFromString


class MainControl:
    def __init__(self):
        #publics
        self.gTimeManager = TimeManager(self)           # global time manager
        clock.get_default().time = self.gTimeManager.clockTime
        self.gModuleList = {}                           # global dict of all instantiated modules in exp {"comp_name" -> instance} 
        self.gLogger = None                             # global logger object
        self.gDisplay = None                            # global display object
        self.gKeyboardListener = KeyboardListener(self) # global keyboard listener that will handle all keys press
        self.gMouseListener = MouseListener(self)       # global mouse listener that will handle all button press
        
        #privates
        self._experiment = None                 # parsed experiment 
        self._condParamList = []                # list of cond-specific params for each event
        self._defaultParamList = []             # default parameters (in case no cond-specificity)
        self._isTerminated = False              # whether this experiment was terminated properly
        self._currentRoutine = None             # stores the name of the current routine
        self._currentCondition = None           # stores the name of the current condition
        self._accumulatedTime = 0 

    def loadExperiment(self, filename):
        """
        Load an XML description of an experiment -- parse + setup all data structures 
        """
        self._experiment = Experiment()
        self._loadExpInstance(filename)

    def startExperiment(self, closeWindowsOnExit = False):
        """
        Schedule and start an already-loaded experiment 
        """
        # starts the logger
        self.gLogger.start()
        # setup the close window tag ; it is used when testing to close the window when the experiment ends
        self.closeWindowsOnExit = closeWindowsOnExit
        # will actually start with the experiment in 1 second; this gives time to the window to show and stabilize
        clock.schedule_once(self._startNextEvent, 1.0, start=True)
        try:    
            pyglet.app.run()
        except BaseException, e:
            self._log("Error type %s caught during execution."%str(e.__class__))
            # make sure we always write out the log to file
            self.cleanupExperiment()
            raise
         
    def cleanupExperiment(self):
        """
        Calls the cleanup method of all instantiated modules, 
        terminates the logging properly and makes sure nothing
        is scheduled anymore.
        """
        if self._isTerminated:
            # Don't do this more than once
            return
        self._log("Cleaning up all instantiated modules")
        # Tell all the modules to clean up
        #@todo: make more elegant than hack. there are some modules we add which aren't our own; they don't
        # have cleanup functions
        for module in self.gModuleList.itervalues():
            if str(module.__module__) != 'ctypes':  
                module.cleanup()
        # Stop the logger properly
        if self.gLogger:
            self.gLogger.stop()
        # Unschedule everything to make sure nothing was forgotten
        self._emptyScheduler()
        # close all windows if required
        if self.closeWindowsOnExit:
            self.gDisplay.closeAll()
        # done
        self._isTerminated = True
        
    def endCurrentRoutine(self, dt=0):
        """
        Ends the current routine by emptying the toDrawList and telling all 
        components to stop. Then start the next item in the flow.
        Used to advance the experiment if one of the components in a routine has
        an infinite duration.
        """
        self._log("Explicit end of current routine called")
        
        # Empty the toDrawList
        self.gDisplay.toDrawList = []
        self.gDisplay.toDrawHUDList = []
        
        # Make sure the scheduler is empty
        # TODO: is this too risky to do?
        self._emptyScheduler()
        
        # Stop all components that aren't stopped yet
        for comp in self.gModuleList.itervalues():
            # TODO: are there any modules that are not BasicModules?
            if isinstance(comp, BasicModule) and comp.started:
                comp.stop()
        
        # reschedule background processes
        self.gDisplay.setWindowsVisible()
        self.gLogger.start(verbose=False)
        
        # Start the next thing
        clock.schedule_once(self._startNextEvent, 0.0, start=False)
        
        # reset accumulative time (we cannot know better than time of NOW)
        self._accumulatedTime = self.gTimeManager.experimentTime() 
        
    def _emptyScheduler(self):
        """
        Emptys the scheduled items lists of the clock
        """
        clock.get_default()._schedule_items = []
        clock.get_default()._schedule_interval_items = []
    
    def _startNextEvent(self, dt=0, start = False):
        """
        Starts the next item in the flow (routine or isi)
        """
        # reset if request
        if start:
            self.gTimeManager.start()
        
        # Update the current condition and routine
        self._currentCondition = None
        self._currentRoutine = None
        
        # Check if experiment is finished
        if len(self._experiment.instFlow) == 0:
            self._log("Experiment finished")
            self.cleanupExperiment()
            return
        
        # Load next FlowObject
        fObj = self._experiment.instFlow.popleft()
        self._log("Starting Flow Item: " + fObj.type)
        
        if fObj.type == 'Routine':
            # Start routine with condition parameters 
            # Control timing of routine components by sorting CompInstance start tuples
            rName = fObj.attribs['routineName']
            self._log("Scheduling Routine: " + rName)
            self._startRoutine(rName, fObj.attribs['condition'])
        
        elif fObj.type == 'Isi':
            isiduration =  float(fObj.attribs['duration'])
            # "Sleep" by calling _startNextEvent after the Isi duration
            self._log("ISI for %.3fs"%isiduration)
            clock.schedule_once(self._startNextEvent, isiduration)
            # compute when the theoretical next start time should be
            self._accumulatedTime += isiduration
            # Force black screen?
        else:
            self._log("PROBLEM: Unhandled Experimental Flow Tag: " + fObj.type)
                    
    def _startRoutine(self, rName, condName):
        # Set current routine and condition name
        self._currentCondition = condName
        self._currentRoutine = rName
        
        retard = self.gTimeManager.experimentTime() - self._accumulatedTime
        
        drawOrders = self._experiment.drawOrders[rName][condName]   # {'comp name' -> drawIndex}
        configsUsed = self._experiment.configsUsed[rName][condName] # {'comp name' -> configName}
        routineEnd = 0                                              # Endtime for whole routine
        hasInfiniteComponent = False                                # Whether there is some component with infinite duration
        
        # Schedule each start/stop for each component
        for cTuple in self._experiment.routineFlows[rName][condName]:   # [('compName',type,start,dur) ('compName2',type,start2,dur2)]
            # Unpack the tuple
            compName, type, startTime, duration = cTuple
            
            # Ignore ZERO (| | < epsilon) durations
            if abs(duration) < 0.000001:
                continue
            
            compObj = self.gModuleList[compName]
            endTime = startTime + duration
            configName = configsUsed[compName]
            drawIndex = drawOrders[compName]
            
            if endTime > routineEnd:
                routineEnd = endTime
            if duration < 0:
                hasInfiniteComponent = True 
            
            desc = "'%s:%s' in condition '%s' from %s to %s" \
                    % (compObj.__module__, compObj.getName(), condName, str(startTime), 
                    (str(endTime) if endTime > 0 else "infinite"))
            if type == 'activation':
                if startTime > 0:
                    self._log("Scheduling activation of " + desc)
                    clock.schedule_once(compObj.start, startTime, duration=duration, configName=configName)   # Schedule start w/ params
                else:
                    self._log("Immediately activating " + desc)
                    compObj.start(duration=duration, configName=configName)
                if duration > 0:
                    # Schedule stop, if duration is not infinite (negative)
                    clock.schedule_once(compObj.stop, endTime - retard)
            elif type == 'display':
                if startTime > 0:  # Future
                    self._log("Scheduling display of " + desc)
                    clock.schedule_once(self._startDrawComp, startTime, compObj, drawIndex) # Add to dispQ
                else:               # Now
                    self._log("Immediately displaying " + desc)
                    self._startDrawComp(0, compObj, drawIndex)
                if duration > 0:
                    # Schedule stop, if duration is not infinite (negative)
                    # clock.schedule_once(self._stopDrawComp, endTime - retard, compObj, drawIndex)
                    clock.schedule_once(self._stopDrawComp, endTime - retard + self.gTimeManager.displayPeriod() / 2.0, compObj, drawIndex)
            else:
                self._log("Unknown Occurence Type: " + type)
                raise
        
        if not hasInfiniteComponent:
            # Schedule next routine/isi if we know the duration of the routine
            clock.schedule_once(self._startNextEvent, routineEnd - retard)
            # compute when the theoretical next start time should be
            self._accumulatedTime += routineEnd
        
    def _startDrawComp(self, dt, compObj, drawIndex):
        """
        Adds the given component to the list of elements to be drawn
        """
        if isinstance(compObj, DrawableHUDModule) or isinstance(compObj, DrawableHUDSourceModule):
            self.gDisplay.toDrawHUDList.append((drawIndex, compObj))
            self.gDisplay.toDrawHUDList.sort(key=lambda obj: obj[0])
        else:
            self.gDisplay.toDrawList.append((drawIndex, compObj))
            self.gDisplay.toDrawList.sort(key=lambda obj: obj[0])
        
    def _stopDrawComp(self, dt, compObj, drawIndex):
        """
        Removes the given component from the list of elements to be drawn
        """
        if (drawIndex, compObj) in self.gDisplay.toDrawList:
            self.gDisplay.toDrawList.remove((drawIndex, compObj))
        elif (drawIndex, compObj) in self.gDisplay.toDrawHUDList:
            self.gDisplay.toDrawHUDList.remove((drawIndex, compObj))

    def _loadExpInstance(self, filename):
        """
        Loads an XML experimental instance file and parses the specific experiment flow
        """
        #get directory root
        filepath = os.path.dirname(filename)             
        # where the file is is where the instance is
        os.environ['INSTDIR'] = os.path.realpath(filepath)
        #open the file using a parser that ignores prettyprint blank text
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse(filename, parser)
        expNode = tree.find('Experiment')
        # TODO: check that version is right
        self._loadExpOverview(os.path.join(filepath, expNode.attrib['fileName']))
        
        #load condition-based routine flow
        self._loadExpFlow(tree)

    def _loadExpFlow(self, treeRoot):
        expFNode = treeRoot.find('ExperimentFlow')
        
        # Add Routines/Isi as FlowObjects to an event queue
        for flowTag in expFNode.getiterator():
            if flowTag.tag != 'ExperimentFlow': # Skip parent
                self._experiment.instFlow.append(FlowObject(flowTag.tag, flowTag.attrib)) 

    def _loadExpOverview(self, filename):
        """
        Loads an XML experimental settings file and parses the settings, components and routines
        """
        
        # where the file is is where the experiment is
        os.environ['EXPDIR'] = os.path.realpath(os.path.dirname(filename))       
        
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse(filename, parser)
        
        self._loadSettings(tree)        # Load Settings

        #instantiate logger 
        self.gLogger = mainlogger.Logger(self,
                                         self._experiment.settings['backFreq'],
                                         self._experiment.settings['savePath'],
                                         self._experiment.settings['expName'],
                                         self._experiment.settings['logType'])
                                         
        self._loadComponents(tree)      # Load Components     
        self._loadRoutines(tree)        # Load Routines

        #instantiate display + windows
        self.gDisplay = maindisplay.Display(self)
        
        for wname in self._experiment.winList.keys():
            wparams = self._experiment.winList[wname]
            r = None
            args = ""
            # build up the argument string from list of parameters
            for a in wparams:
                args += "%s=%s,"%(a, str(wparams[a]))
            args += "name='%s'"%wname
            ##
            ## Generic construction of the renderer corresponding to the mode (given as string)
            ##
            exec('r = %s.Renderer(%s)'%(wparams['mode'], args))
            r.setController(self)
            self.gDisplay.addRenderer(r)

        self.gDisplay.setWindowsVisible()
        
        # Set the camera position
        self.gDisplay.set_camera_position(self._experiment.getCameraPosition())
        self.gDisplay.set_camera_angles(self._experiment.getCameraAngles())

        self._log("Read and parsed experiment")
        self._log("Instantiated logger + Display")

    def _loadSettings(self, treeRoot):
        #Logger Parameters
        setNode = treeRoot.find('Settings')
        
        # Python parameters 
        pathNode = setNode.find('Python')
        for comppath in pathNode.getiterator('ComponentPath'):
            if comppath.attrib.has_key('directory'):
                compdir = os.path.abspath(getPathFromString(comppath.attrib['directory']))
                if os.path.isdir(compdir):
                    # modify PYTHONPATH to include the components path given
                    sys.path.append(compdir)
                compdir = os.path.join( compdir, 'lib')
                if os.path.isdir(compdir):
                    # modify PYTHONPATH to include the lib path given
                    sys.path.append(compdir)
        
        # Logger parameters
        logNode = setNode.find('Logger')
        for param in logNode.getiterator('Param'):
            try: 
                if param.attrib['name'] == 'expname':           #experiment name
                    self._experiment.settings['expName'] = param.attrib['val']
                elif param.attrib['name'] == 'logtype':         #logging type
                    self._experiment.settings['logType'] = param.attrib['val']
                elif param.attrib['name'] == 'logfreq':         #backup frequency
                    self._experiment.settings['backFreq'] = param.attrib['val']
                elif param.attrib['name'] == 'savepath':        #log save path
                    self._experiment.settings['savePath'] = param.attrib['val']
                else:
                    un = ParseError(param.attrib['name'])
                    raise un
            except ParseError:
                print "Unhandled Settings parameter for Logger <Param 'name'=" , un.value , '>'
        
        # Display Parameters
        dispNode = setNode.find('Display')
        
        # Camera Parameters
        cameraNode = dispNode.find('Camera')
        if cameraNode is not None:
            for param in cameraNode.getiterator('Param'):
                name = param.attrib['name']
                if name in self._experiment.cameraSettings:
                    try:
                        val = float(param.attrib['val'])
                        self._experiment.cameraSettings[name] = val
                    except ValueError:
                        print("Settings parameter for Camera <Param 'name'=%s> must be a float, '%s' given" % name, param.attrib['val'])
                else:
                    print("Unhandled Settings parameter for Camera <Param 'name'=" , name , '>')
        
        # Window parameters
        winNode = dispNode.find('Windows')
        for win in winNode.getiterator('Window'):
            wname = win.attrib['name']
            self._experiment.addWindow(wname)
            
            for param in win.getiterator('Param'):            
                pdict = self._experiment.winList[wname]
                try: 
                    if param.attrib['name'] == 'size':                 #window size tuple                        
                        pdict['size'] = eval(param.attrib['val'])
                    elif param.attrib['name'] == 'mode':               #window display mode
                        pdict['mode'] = param.attrib['val']
                    elif param.attrib['name'] == 'fov':                #window field of view
                        pdict['fov'] = float(param.attrib['val'])
                    elif param.attrib['name'] == 'fullscreen':         #window fullscreen or not
                        pdict['fullscreen'] = eval(param.attrib['val'])
                    elif param.attrib['name'] == 'hidecursor':         # cursor visible or not
                        pdict['hidecursor'] = eval(param.attrib['val'])
                    elif param.attrib['name'] == 'mousecameracontrol': # allow mouse control of camera
                        pdict['mousecameracontrol'] = eval(param.attrib['val'])
                    elif param.attrib['name'] == 'screenid':           #id of screen
                        pdict['screenid'] = eval(param.attrib['val'])
                    elif param.attrib['name'] == 'flipScreen':         #flip screen or not
                        pdict['flipScreen'] = eval(param.attrib['val'])
                    elif param.attrib['name'] == 'mirror_3D':         # 3D mirror not
                        pdict['mirror_3D'] = eval(param.attrib['val'])
                    elif param.attrib['name'] == 'color':              #window bg color
                        pdict['color'] = eval(param.attrib['val'])
                    elif param.attrib['name'] == 'focallength':                
                        pdict['focallength'] = float(param.attrib['val'])
                    elif param.attrib['name'] == 'eyeseparation':
                        pdict['eyeseparation'] = float(param.attrib['val'])
                    else:
                        raise ParseError(param.attrib['name'])
                except ParseError as un:
                    print "Unhandled Settings parameter for Display <Param 'name'=" , un.value , '>'
                    raise
    
    def _loadComponents(self, treeRoot):
        for compNode in treeRoot.findall('Components/Component'):
            # discard the component if disabled
            if not compNode.attrib.has_key('enabled') or eval(compNode.attrib['enabled']):
                # Create an empty comp obj, import/instantiate the module
                cName = compNode.attrib['name']
                iPath = compNode.attrib['importPath']
                comp = Component(cName, compNode.attrib['type'], iPath)
                # Go through the InitConfig
                for param in compNode.findall('InitConfig/Param'):
                    self._addParam(comp.initParams, param)
                
                # Go through other Configs
                for config in compNode.findall('Configs/Config'):
                    condName = config.attrib['name']
                    comp.params[condName] = {}  # Prepare param dict for this config
                    
                    # Get the params
                    for param in config.findall('Param'):
                        self._addParam(comp.params[condName], param)    # Type check and add 
    
                # Instantiate the module
                self._importModule(comp)
                # Add it to the experiment
                self._experiment.components[cName] = comp

    def _loadRoutines(self, treeRoot, condName=''):
        for routine in treeRoot.findall('Routines/Routine'):        #over routines
            rName = routine.attrib['name']
            
            # Create empty dicts for storing draw orders and config
            self._experiment.drawOrders[rName] = {}
            self._experiment.configsUsed[rName] = {}
            self._experiment.routineFlows[rName] = {}
            
            for condition in routine.findall('Conditions/Condition'):
                condName = condition.attrib['name']
                
                # Create empty dicts for storing draw orders and configs and list for flows
                self._experiment.drawOrders[rName][condName] = {}
                self._experiment.configsUsed[rName][condName] = {}
                self._experiment.routineFlows[rName][condName] = []
                
                # Go through the used components
                compDrawIndex = 0
                for compNode in condition.findall('UsedComponents/UsedComponent'):
                    # Set the draw index and the config used in this condition
                    compName = compNode.attrib['componentName']
                    # only add created components
                    if self._experiment.components.has_key(compName):
                        self._experiment.drawOrders[rName][condName][compName] = compDrawIndex
                        self._experiment.configsUsed[rName][condName][compName] = compNode.attrib['configName']
                        compDrawIndex += 1
            
                #<RoutineFlow> -- add Occurence tuples to routineFlows list      
                for occNode in condition.findall('RoutineFlow/Occurence'): 
                    # only add created components
                    if self._experiment.components.has_key(occNode.attrib["componentName"]):
                        self._experiment.routineFlows[rName][condName].append(
                            (occNode.attrib["componentName"],
                            occNode.attrib["type"],
                            float(occNode.attrib["startTime"]),
                            float(occNode.attrib["duration"])))   

    def _addParam(self, paramDict, paramXml):
        pName = paramXml.attrib['name']
        pVal = paramXml.attrib['val']
        pType = paramXml.attrib['valType']
        
        if pType == 'int':
            pVal = int(pVal)
        elif pType == 'float':
            pVal = float(pVal)
        elif pType == 'str':
            pVal = str(pVal)            #shouldn't have to - already a str
        elif pType == 'bool':
            pVal = eval(pVal)
        elif pType == 'code':
            pVal = eval(pVal)
        else:
            self._log("Unknown Parameter Type: " + pType)
            raise
        paramDict[pName] = pVal # add it to the dict

    def _importModule(self, comp):
        """
        Imports python module from the component "importPath" and dynamically imports the libraries 
        
        Note: We require that all modules follow a naming convention so the GUI can remain ignorant
              importPath = src/ dir-relative path to python module
              main class to instantiate = ModuleMain()
        """
        # Dynamically Import
        fp = None
        try:
#            mymodule = __import__(iPath, fromlist=['ModuleMain'])           #dynamic import       
            mymodule = imp.new_module('dummy')
            mymodule.__path__ = None
            for modulename in comp.importPath.split('.'):
                fp, pathname, description = imp.find_module(modulename, mymodule.__path__)
                mymodule = imp.load_module(modulename, fp, pathname, description)
            curComp = mymodule.ModuleMain(self, initConfig=comp.initParams, runConfigs=comp.params)
            print "MainController: Successfully imported: " + comp.importPath
        except Exception:
            print "MainController: Failed to import: " + comp.importPath      #don't have logger yet
            curComp = None
            raise
        finally:
            # Since we may exit via an exception, close fp explicitly.
            if fp:
                fp.close()
                
        self.gModuleList[comp.name] = curComp   # add to module list
        
    def _log(self, logData):
        """
        Wrapper for logging inside the controller
        """
        self.gLogger.logMe('mainControl', 'mainControl', logData)
        
    '''
    Methods for building things yourself i.e.: not reading in Experiment / Instance XML files
    '''
    def setLogger(self, log):
        self.gLogger = log
    
    def setDisplay(self, disp):
        self.gDisplay = disp
    
    def addToModuleList(self, modName, modRef):
        self.gModuleList[modName] = modRef
        
    def removeFromModuleList(self, modName):
        del self.gModuleList[modName]
        
    def registerKeyboardAction(self, keysString, functionToCallWhenPress, functionToCallWhenRelease = None):
        if len(keysString.strip()) > 0:
            self.gKeyboardListener.listenTo( keysString.strip(), functionToCallWhenPress, functionToCallWhenRelease )
        
    def unregisterKeyboardAction(self, keysString, functionToCallWhenPress = None, functionToCallWhenRelease = None):
        if len(keysString.strip()) > 0:
            self.gKeyboardListener.stopListeningTo( keysString.strip(), functionToCallWhenPress, functionToCallWhenRelease )

    def registerMouseAction(self, buttonsString, functionToCallWhenPress, functionToCallWhenRelease = None):
        if len(buttonsString.strip()) > 0:
            self.gMouseListener.listenTo( buttonsString.strip(), functionToCallWhenPress, functionToCallWhenRelease )
        
    def unregisterMouseAction(self, buttonsString, functionToCallWhenPress = None, functionToCallWhenRelease = None):
        if len(buttonsString.strip()) > 0:
            self.gMouseListener.stopListeningTo( buttonsString.strip(), functionToCallWhenPress, functionToCallWhenRelease )

    def registerMouseMotion(self, functionToCallWhenMove):
        self.gMouseListener.listenToMotion( functionToCallWhenMove )
        
    def unregisterMouseMotion(self, functionToCallWhenMove ):
        self.gMouseListener.stopListeningToMotion( functionToCallWhenMove )
        
    def registerWidget(self, widget):
        self.gMouseListener.registerWidget(widget)
        
    def unregisterWidget(self, widget):
        self.gMouseListener.unregisterWidget(widget)

class Experiment:
    '''
        Parsed experiment class
                
        SETTINGS
        
        Logger
        PARAM        DESCRIPTION                VALUES                        DEFAULT
        ---------    ----------------           ---------------               ------
        expName  =    description/exp name                                     "expyvr exp"        
        logType  =    how to log                {console,console-file,file}    "console"
        logFreq  =    log backup frequency      (in sec)                       60
        savePath =    path to save logging      /path/to/logdata               cwd
        
        Display (Window):
        PARAM        DESCRIPTION                VALUES                        DEFAULT
        ---------    ----------------           ---------------               ------
        name     =    window name                
        mode     =    window output device     {mono,stereo,hmd,minicave}      mono
        size     =    window size              (x,y)                          (800,600)
        
    '''
    def __init__(self):        
        self.settings = {'expName':'expyvr exp', 'logType':'console', 'logFreq':60, 'savePath':os.getcwd()}
        self.cameraSettings = {}    # Starting position and angles of the camera
        for param in ['posX', 'posY', 'posZ', 'angleX', 'angleY', 'angleZ']:
            self.cameraSettings[param] = 0
        self.winList = {}           # Display (window) parameter list -- dict:  "winname -> {params}
        
        self.components = {}        # components: 'compName' -> comp obj
        self.routineFlows = {}      # routine flows: 'routine name' -> {'condition name' -> [('compName',type,start,dur) ('compName2',type,start2,dur2)]}
        self.drawOrders = {}        # Draw orders of components: 'routine name' -> {'condition name' -> {'comp name' -> drawIndex}}
        self.configsUsed = {}       # Configs used in different conditions: 'routine name' -> {'condition name' -> {'comp name' -> configName}}
                
        self.instFlow = deque([])   #queue for cur instance experimental flow
        
        
    def addWindow(self, winname):
        self.winList[winname] = {'mode':'mono', 'size':'(800,600)'}
    
    def getCameraPosition(self):
        return np.array([self.cameraSettings['posX'],
                        self.cameraSettings['posY'],
                        self.cameraSettings['posZ']])
    
    def getCameraAngles(self):
        return np.array([self.cameraSettings['angleX'],
                        self.cameraSettings['angleY'],
                        self.cameraSettings['angleZ']])
        



class Component:
    '''
    A simple object representing a component (module) in the experiment
    '''
    def __init__(self, name, type, iPath):
        self.name = name
        self.importPath = iPath
        self.type = type
        self.initParams = {} # the params for the initialisation of the component
        self.params = {}    #dictionary of condition-spec params  "condName" -> {paramdict}


class FlowObject:
    '''
    Abstract class for experimental instance Routine and ISI tags
    '''
    def __init__(self, type, attribs):
        self.type = type                    #Routine or Isi
        self.attribs = attribs              #dictionary of {attribute:val} pairs
