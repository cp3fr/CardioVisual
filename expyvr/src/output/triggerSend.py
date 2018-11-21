'''
Trigger Sender Module

Handles sending trigger codes to external devices (such as parallel port)
If no trigger manager has been created, a new one is made.

@author: nathan
@since April 2011
'''

from os import path
import csv
from datetime import datetime
from pyglet.gl import *
from abstract.AbstractClasses import BasicModule
from pyglet.clock import _default_time_function as time

# Port/trigger modules
import controller.trigManager as tManager
from output.parallelPort import *


class ModuleMain(BasicModule):    
    defaultInitConf = {
        'name': 'triggerSend',
        'port': 'parallel',
        'address': '0x378',
        'autoAssignCode': True,
        'ignoredCodes': '0'  ,
        'logToCSV': True
    }
    
    defaultRunConf = {
        'trigCodeName': 'condX',
        'writeAtStart': 0,
        'writeAtStop': 0
    }
        
    confDescription = [
       ('name', 'str', "Module sending triggers through parallel port"),
       ('port', 'str', "To what external port do we write trigger value?",['parallel']),
       ('address', 'str', "Address of port"),
       ('autoAssignCode', 'bool', "Use trigger code mapping to auto assign a unique trigger code to this instance. Note: if unselected, manually enter code for writeAtStart."),
       ('trigCodeName', 'str', "Unique name for this trigger code (to be mapped into an available numerical code)"),
       ('writeAtStart', 'int', "At the start() of the component, write this code. Note: if autoAssignCode is selected, this code is ignored in favor of system generated code"),
       ('writeAtStop', 'int', "At the stop() of the component, write this code (regardless of what triggerCode"),
       ('ignoredCodes', 'str', "List of trigger codes which should not be considered in the pool (space separated ints)"),
       ('logToCSV', 'bool', "Save the logs of the buttons pressed in a Comma Separated Values text file"),   
       ('write()', 'info', "Writes a trigger to the port, given an integer code value: self.mytriggermodule.write(1)"),
       ('read()', 'info', "Reads values (integers) from the parallel port, useful for debugging"),
   ]
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        BasicModule.__init__(self, controller, initConfig, runConfigs)
        self.trigManager = None
        self.lastTrigTime = 0           #last time we sent a trigger
        
        # start logger
        self.csvLogger = None
        if self.initConf['logToCSV']:
            now = datetime.today()
            self.csvLogger = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.initConf['name'] +  '.csv') , 'w'), lineterminator = '\n')
            self.csvLogger.writerow(['expTime', 'routine', 'condition', 'code'])

        
        if(self.initConf['autoAssignCode']):
            #Load trigger manager
            if not self.controller.gModuleList.has_key('trigManager'):
                iCodes = self.initConf['ignoredCodes'].split()
                self.trigManager = tManager.TrigManager(self.controller,iCodes)
                self.controller.addToModuleList('trigManager', self.trigManager)
            else:
                self.trigManager = self.controller.gModuleList['trigManager']
        
        self.address = self.initConf['address']
        
        if(self.initConf['port'] == 'parallel'):
            # Try to connect to parallel port
            try:
                self.pp = ParallelPort(self.address)
            except RuntimeError as e:
                self.log("Warning: %s"%str(e))
                self.pp = None
                pass
                #raise Warning("Could not connect to Parallel Port")
        else:
            raise Warning("Warning: " + self.initConf['port'] + " port not yet implemented")
                                                   
    def start(self, dt=0, duration=-1, configName=None):
        """
        Send a trigger
        """
        BasicModule.start(self, dt, duration, configName)     
        
        if(self.initConf['autoAssignCode']):
            tCode = self.trigManager.getCode(self.activeConf['trigCodeName'])
        else:
            tCode = self.activeConf['writeAtStart']
   
        self.log("Trying to send trigger code: " + str(tCode))
        
        if(self.initConf['port'] == 'parallel'):
            self.write(tCode)
        else:
            self.log("Writing to port: " + str(self.initConf['port'] + " not implemented"))
        
    def stop(self, dt=0):
        BasicModule.stop(self, dt)
        stopWrite = self.activeConf['writeAtStop']
        if(self.initConf['port'] == 'parallel'):            
            self.log("Writing stop:" + str(stopWrite))
            if not self.pp is None:
                self.pp.write(stopWrite,self.address)
        else:
            self.log("Writing to port: " + str(self.initConf['port'] + " not implemented"))

    def cleanup(self):
        BasicModule.cleanup(self)
        
        if not self.pp is None:
            self.pp.write(0,self.address)
        
        if(self.initConf['autoAssignCode']):
            self.log("Final Trigger Mapping: ")
            self.trigManager.printMapping()
        
        
    '''
    For external modules to leech off of established port connection
    '''
    def write(self, tcode):
        if self.pp is not None:
            # avoid re-sending same status
            if tcode != self.pp.read(self.address):
                self.pp.write(tcode, self.address)
                self.log("writetrig," + str(tcode))
                self.lastTrigTime = time()
                
                if self.csvLogger :
                    self.csvLogger.writerow( [ self.controller.gTimeManager.experimentTime(), self.controller._currentRoutine, self.controller._currentCondition, tcode])
    def read(self):
        if self.pp is not None:
            print self.pp.read(self.address)
            
    def writeTrig(self, tcodename = ''):
        # default action without code given ; Zero
        if not len(tcodename) > 0:
            self.write(self.activeConf['writeAtStop'])
            return
        # if automatic assignment, ask trigManager for a code
        if(self.initConf['autoAssignCode']):
            self.write(self.trigManager.getCode(tcodename))
        # not automatic assignment but known code ; send it!
        elif self.activeConf['trigCodeName'] == tcodename:
            self.write(self.activeConf['writeAtStart'])
        # not a valid code at all :(
        else:
            self.log("The trigger code %s is not the current trigCodeName and the 'autoAssignCode' is not selected; NOT sending trigger."%tcodename)
        
        
        
            