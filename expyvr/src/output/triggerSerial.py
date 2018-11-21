'''
Serial Trigger Module

@author: Javier Bello Ruiz
@since April 2014
'''

import csv
import serial
from datetime import datetime
from pyglet.gl import *
from pyglet.clock import _default_time_function as time
from time import sleep
from os import path

#pylnco modules
from display.tools import *
from abstract.AbstractClasses import BasicModule
from controller import getPathFromString
      
      
class SerialPort(serial.Serial):    
        
    def __init__(self, *args, **kwargs):
        #ensure that a reasonable timeout is set
        timeout = kwargs.get('timeout', 0.1)
        if timeout < 0.01: timeout = 0.1
        kwargs['timeout'] = timeout if timeout > 0.1 else 0.1
        serial.Serial.__init__(self, *args, **kwargs)
        # init 
        self.flushInput()       
            
    def stop(self):    
        self.close()
        
    def writeData(self, string):
        try:
            n = self.write(string)
            
            if n < len(string) :
                print "Did not send the whole message"
                return False
            else:
                print "Trigger sent!"
        except:
            print "Error sending data"
            return False
            
        return True
            
class ModuleMain(BasicModule):
    
    defaultInitConf = {
        'name': 'triggerSerial',
        'port': 'COM1',
        'baudrate': '9600',
        'logToCSV': True
    }
    
    defaultRunConf = {
        'trigCodeName': 'condX',
        'writeAtStart': 0,
        'writeAtStop': 0
    }
    
    confDescription = [
        ('name', 'str', "Module to send triggers through serial port."),
        ('port', 'str', "Computer serial port.", ['COM1', 'COM2', 'COM3', 'COM4','COM5', 'COM6', 'COM7', 'COM8','COM9', 'COM10', 'COM11', 'COM12', 'COM13', 'COM14', 'COM15', 'COM16', 'COM17', 'COM18']),
        ('baudrate', 'str', "Baudrate", ['2400', '4800', '9600', '19200', '38400', '57600', '115200']),
        ('logToCSV', 'bool', "Save data to coma-separated-values file ( <date>_<modulename>.csv )"),
        ('trigCodeName', 'str', "Unique name for this trigger code."),
        ('writeAtStart', 'int', "At the start() of the component, write this code."),
        ('writeAtStop', 'int', "At the stop() of the component, write this code."),
        ('write()', 'info', "Writes a trigger to the port, given an integer code value: self.mytriggermodule.write(1)"),
    ]
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        BasicModule.__init__(self, controller, initConfig, runConfigs)
        
        self.lastTrigTime = 0#last time we sent a trigger
       
        # init serial
        self.com = SerialPort(port=self.initConf['port'], baudrate=int(self.initConf['baudrate']))

        # start logger
        self.csvLogger = None
        if self.initConf['logToCSV']:
            now = datetime.today()
            self.csvLogger = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.initConf['name'] +  '.csv') , 'w'), lineterminator = '\n')
            self.csvLogger.writerow(['expTime', 'routine', 'condition', 'code'])
            
    def start(self, dt= 0, duration= -1, configName= None):
        BasicModule.start(self, dt, duration, configName)
        tCode = self.activeConf['writeAtStart']
        self.log("Trying to send trigger code: " + str(tCode))
        self.write(tCode)

    def stop(self, dt= 0):
        BasicModule.stop(self, dt)
        stopWrite = self.activeConf['writeAtStop']  
        self.log("Writing stop:" + str(stopWrite))
        self.write(stopWrite)
        
    def cleanup(self):
        BasicModule.cleanup(self)
        if self.com is not None:
            self.com.stop()
        
    def write(self, tcode):
        if self.com is not None:
            self.com.writeData(str(tcode))
            self.log("writetrig," + str(tcode))
            self.lastTrigTime = time()
            if self.csvLogger :
                self.csvLogger.writerow([self.controller.gTimeManager.experimentTime(), self.controller._currentRoutine, self.controller._currentCondition, tcode])

