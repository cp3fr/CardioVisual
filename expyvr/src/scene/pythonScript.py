'''
Created on April 29 2011

@author: bh
'''

# generic toolbox for scripts
import os, csv, re, serial, socket, threading, math, random
import numpy as np
from datetime import datetime
from pyglet.gl import *
# scripting expyvr toolbox
from pyglet.clock import _default_time_function as time
from abstract.AbstractClasses import BasicModule
from controller import getPathFromString

try:
    import avatar.avatarlib as avatarlib
except:
    pass

class ModuleMain(BasicModule):
    """
    A simple module to encapsulate Python scripts
    """
    defaultInitConf = {
        'name': 'script',
        'initCode': 'self.r=0',
        'cleanupCode': '',
    }
    
    defaultRunConf = {
        'updateCode': 'self.r=self.r+10*dt',
    }
    
    confDescription = [
        ('name', 'str', "Module executing a Python script"),
        ('initCode', 'str', "Code (or filename) to initialize the module"),
        ('cleanupCode', 'str', "Code (or filename) to end module properly"),
        ('updateCode', 'str', "Code (or filename) to update data (executed as is). Variable 'dt' is the update delta time."),
        ('starting', 'info', "True when the update function is called for the first time when starting a routine."),    
        ('getStartingTimes()', 'info', "Returns tupple of times when the routine was started [absTime, ExpTime, dispTime].")   
    ]

    def __init__(self, controller, initConfig=None, runConfigs=None):
        BasicModule.__init__(self, controller, initConfig, runConfigs)
        
        # execute the code of initialization
        try:
            f = open(getPathFromString(self.initConf['initCode']))
        except IOError:
            exec( self.initConf['initCode'] )
        else:
            exec( f.read() )
            f.close()
            
        self.updatecode = {}
        self.starting = False
        
        for confName, conf in self.runConfs.items():
            # compile the code to be executed by python interpreter at each update
            code = ''
            try:
                f = open(getPathFromString(conf['updateCode']))
            except IOError:
                code = conf['updateCode']
            else:
                code = f.read() 
                f.close()
            if len(code) > 0:
                code += '\n'
                self.updatecode[confName] = compile( code, '<string>', 'exec' )
            else:
                self.updatecode[confName] = None
        
        
    def update(self, dt):
        if self.started:
            exec( self.updatecode[self.activeConfName] )
        
    def start(self, dt=0, duration=-1, configName=None):
        """
        Activate the update with script passed in the conf
        """
        BasicModule.start(self, dt, duration, configName)
        if self.updatecode[self.activeConfName] is not None:
            self.starting = True
            self.update(0)
            self.starting = False
            pyglet.clock.schedule(self.update)

    def stop(self, dt=0):
        BasicModule.stop(self, dt)
        pyglet.clock.unschedule(self.update)
                
    def cleanup(self):
        BasicModule.cleanup(self)
        # execute the code of cleanup
        if len(self.initConf['cleanupCode']) > 0 :
            try:
                f = open(getPathFromString(self.initConf['cleanupCode']))
            except IOError:
                exec( self.initConf['cleanupCode'] )
            else:
                exec( f.read() )
                f.close()
                