'''
Created on Jul 8, 2010

@author: bh, Tobias Leugger
@since: Summer 2010

@license: Distributed under the terms of the GNU General Public License (GPL).
'''
from os import path
import csv
from datetime import datetime

from abstract.AbstractClasses import BasicModule



class ModuleMain(BasicModule):
    """
    A simple module to listen to keyboard inputs
    """
    defaultInitConf = {
        'name': 'keyboard',
        'logToCSV': True
    }
    
    defaultRunConf = {    
        'keys': 'ENTER',
        'unpause': True,
        'endRoutine': True,
    }
    
    confDescription = [
        ('name', 'str', "Module listening to keyboard events and reacting to some key press."),
        ('logToCSV', 'bool', "Save the logs of the key pressed in a Comma Separated Values text file"),
        ('keys', 'str', "List of keys to listen to (space-separated list of keys, e.g. 'A _1 NUM_1 ENTER LEFT')"),
        ('unpause', 'bool', "Unpause the simulation at key press"),
        ('endRoutine', 'bool', "End the current routine at key release"),
        ('currentKeys', 'info', "List of keys currently pressed")
    ]
   
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        BasicModule.__init__(self, controller, initConfig, runConfigs)
        self.buttonpresstime = {}
        self.logline = {}
        self.currentKeys = []
        
        self.csvLogger = None
        if self.initConf['logToCSV']:
            now = datetime.today()
            self.csvLogger = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.initConf['name'] + '.csv') , 'w'), lineterminator = '\n')
            self.csvLogger.writerow(['absTime', 'expTime', 'displayTime', 'routine', 'condition', 'key', 'reactionExpTime', 'reactionDisplayTime', 'pressDuration'])
            
    def start(self, dt=0, duration=-1, configName=None):
        """
        Activate the engine with the parameters passed in the conf
        """
        BasicModule.start(self, dt, duration, configName)  
        self.controller.registerKeyboardAction(self.activeConf['keys'], self.onKeyPress, self.onKeyRelease)
                
        self.buttonpresstime = {}
        self.logline = {}
        self.currentKeys = []
            
    def stop(self, dt=0):
        # get start times before stopping module
        startTimes = self.getStartingTimes()
        
        # unregister keyboard listenner
        self.controller.unregisterKeyboardAction(self.activeConf['keys'], self.onKeyPress, self.onKeyRelease)   
        self.currentKeys = []
        
        if self.csvLogger :
            # if no key was ever pressed, write a default entry line
            if len(self.logline) == 0:
                self.csvLogger.writerow( startTimes + [ self.controller._currentRoutine, self.controller._currentCondition, '', -1, -1, -1] )
            else:
                for k in self.logline.keys():
                    # if a log line was started, but not finished in onKeyRelease
                    if len(self.logline[k]) > 0:
                        self.logline[k].append(-1)
                        self.csvLogger.writerow(self.logline[k])
            
        # stop module
        BasicModule.stop(self, dt)
        
    def onKeyPress(self, keypressed=None):
        # get times
        startTimes = self.getStartingTimes()
        
        # get key
        self.currentKeys.append(keypressed)
        self.log("Key %s pressed"%keypressed)
        
        # create entry for this key
        self.buttonpresstime[keypressed] = self.controller.gTimeManager.experimentTime()
        self.logline[keypressed] = []
        
        # act on key
        if self.activeConf['unpause']:
            responsetime = self.controller.gTimeManager.unpause()
        else:
            responsetime = self.buttonpresstime[keypressed] - startTimes[1]
        # log    
        if self.csvLogger:            
            displayresponsetime =  self.buttonpresstime[keypressed] - startTimes[2]
            self.logline[keypressed] = startTimes + [ self.controller._currentRoutine, self.controller._currentCondition ]\
                                     + [keypressed, str("%.4f"%responsetime), str("%.4f"%displayresponsetime)]
        
    def onKeyRelease(self, keypressed=None):
        
        # get only keys which were pressed after start
        if self.currentKeys.count(keypressed):
            self.currentKeys.remove(keypressed)
            self.log("Key %s released"%keypressed)
            
            # get times
            keypressduration = self.controller.gTimeManager.experimentTime() - self.buttonpresstime[keypressed]
        
            # log
            if self.csvLogger and len(self.logline[keypressed]) > 0:
                self.logline[keypressed].append( str("%.4f"%keypressduration) )
                self.csvLogger.writerow(self.logline[keypressed])
                # keep but empty the log line for this key
                self.logline[keypressed] = []
                
            if self.activeConf['endRoutine']:
                self.controller.endCurrentRoutine()
        else:
            self.log("Ignored key %s release"%keypressed)
