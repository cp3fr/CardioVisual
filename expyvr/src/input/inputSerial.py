'''
Created on Jan 29, 2011

@author: bh
@since: winter 2010

@license: Distributed under the terms of the GNU General Public License (GPL).
'''

from os import path
import csv
import threading
import serial
from pyglet.clock import _default_time_function as current_time
from datetime import datetime
from time import sleep
from pyglet.gl import *

#pylnco modules
from display.tools import *
from abstract.AbstractClasses import DrawableHUDSourceModule
from controller import getPathFromString

      
class SerialTimeout(serial.Serial):
    """
    Serial port enforcing a time out
    """
    def __init__(self, *args, **kwargs):
        #ensure that a reasonable timeout is set
        timeout = kwargs.get('timeout', 0.1)
        kwargs['timeout'] = timeout if timeout > 0.1 else 0.1
        serial.Serial.__init__(self, *args, **kwargs)
        # init 
        self.flushInput()

class SerialPacketReader():
    """
    separate thread to continuously read serial port (not dependent on expyvr update)
    so that the module 'measure' is always the latest recieved data.
    """
    def __init__(self, parent):
        self.module = parent
        self.com = SerialTimeout(port=parent.initConf['port'], baudrate=int(parent.initConf['baudrate']))
        self.reading = False        

    def read_forever(self):
        self.reading = True
        # self.com.open()
        # read until self.read is false
        while self.reading:
            #read data from serial
            self.buf = self.com.readline()
            # handle the packet
            if self.module is not None and self.module.started:
                self.module.handle(self.buf)
            
    def stop(self):
        self.reading = False      
        # self.com.close()
        
            
class ModuleMain(DrawableHUDSourceModule):
    """
    A simple module to read data from serial port.
    Warning ; it consider data are provoded as text, values separated by comas, and ending with a '\n'
    """
    defaultInitConf = {
        'name': 'serial',
        'port': 'COM1',
        'baudrate': '9600',
        'initCode': '',
        'logToCSV': True
    }
    
    defaultRunConf = {
        'updateCode': "for d in data: print d",
    }
    
    confDescription = [
        ('name', 'str', "Module reading the flow of data coming from a serial port."),
        ('port', 'str', "Computer serial port", ['COM1', 'COM2', 'COM3', 'COM4','COM5', 'COM6', 'COM7', 'COM8','COM9', 'COM10', 'COM11', 'COM12', 'COM13', 'COM14']),
        ('baudrate', 'str', "Baudrate", ['2400', '4800', '9600', '19200', '38400', '57600','115200' ]),
        ('initCode', 'str', "Code (or filename) to initialize the module"),
        ('logToCSV', 'bool', "Save data to coma-separated-values file ( <date>_<modulename>.csv )"),
        ('updateCode', 'str', "Code (or filename) to be executed at each update.\n'data' is a stack of strings of data read from serial line since last update,\n'time' is the stack of times when each data was read (s)."),
        ('getData()', 'info', "Returns last received data (string)")
        ]
    
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableHUDSourceModule.__init__(self, controller, initConfig, runConfigs)
                
        self.label = None
        self.data = {}
        self.keys = []
        self.lastKey = 0
        self.frequency = 0.0
        self.lastdata = ''
        self.starting = False
        
        # init 
        self.logActive = self.initConf['logToCSV']
        if self.logActive:
            now = datetime.today()
            self.csvLogger = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.initConf['name'] +  '.csv') , 'w'), lineterminator = '\n')
            line = [ 'expe_time', 'Routine', 'Condition', 'read_time', 'data' ]
            self.csvLogger.writerow(line)
        
        # init sensor
        self.sensor = SerialPacketReader(self) 
        self.sensor_thread = threading.Thread(target=self.sensor.read_forever)
        self.lock = threading.Lock()

        # execute the code of initialization
        try:
            f = open(getPathFromString(self.initConf['initCode']))
        except IOError:
            exec( self.initConf['initCode'] )
        else:
            exec( f.read() )
            f.close()
            
        # compile the code to be executed by python interpreter at each update
        self.updateCode = {}
        for confName, conf in self.runConfs.items():
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
                self.updateCode[confName] = compile( code, '<string>', 'exec' )
            else:
                self.updateCode[confName] = None
                
        # start the thread
        self.sensor_thread.start()
            
    def draw(self, window_width, window_height, eye=-1):
        DrawableHUDSourceModule.draw(self, window_width, window_height)

        if self.label is None:
            self.label = pyglet.text.Label(text='',
                                       color=(0, 200, 200, 255),
                                       font_name='Lucida Console',
                                       font_size=12,
                                       anchor_x='left', anchor_y='center',
                                       width=600, multiline=False,
                                       x=100, y=120)
            
        if self.getUpdateInterval() > 9 :
            self.label.text = "{0} data : {1} ".format( self.initConf['name'], str(self.getData()) )
        else:
            self.label.text = "{0} data : {1} ({2: =7.1f} Hz)".format( self.initConf['name'], str(self.getData()), self.getUpdateInterval() )
        self.label.draw() 
        
    def handle(self, serialPacket):
    
        if self.lock.acquire():
            # generate key from time (microsecond precision)
            key = long(current_time() * 1000000.0)
            # store data
            self.keys.append(key)
            self.data[key] = serialPacket.strip()
            
            # compute average frequency
            if self.frequency == 0:
                self.frequency = 1000000.0 / float(key - self.lastKey)
            else:
                self.frequency = 500000.0 / float(key - self.lastKey) + 0.5 * self.frequency
                
            # remember last key handled
            self.lastKey = key
            
            self.lock.release()
            # Necessary to give the main thread time to acquire lock
            sleep(0)

    def start(self, dt= 0, duration= -1, configName= None):
        DrawableHUDSourceModule.start(self, dt, duration, configName)
        pyglet.clock.schedule(self.update)  
        self.lastkey = long(current_time() * 1000000.0)
        
        if self.updateCode[self.activeConfName] is not None:
            self.starting = True
            self.update(0)
            self.starting = False
        
    def stop(self, dt= 0):
        DrawableHUDSourceModule.stop(self, dt)
        pyglet.clock.unschedule(self.update)

    def update(self, dt):
        """
        The update is called regularly
        """
        # access to the thread data (lock protected)
        if self.lock.acquire():
            # make a local copy
            time = []
            data = []
            
            for t in self.keys: 
                data.append(self.data[t])
                time.append( float(t) / 1000000.0)
            # clear buffer
            self.keys = []
            self.data = {}
            # release lock
            self.lock.release()
            
        # logging of local data
        if self.logActive:
            for i in range(len(data)):
                # log time & condition
                line = [ str("%.4f"%self.controller.gTimeManager.experimentTime()), self.controller._currentRoutine, self.controller._currentCondition ]
                # log data
                line.extend([ str("%.9f"%time[i]), data[i]])
                self.csvLogger.writerow(line)
                
        # Run update code on the local data
        if self.updateCode[self.activeConfName] is not None:
            exec( self.updateCode[self.activeConfName] )
            
        self.lastdata = '' if len(data)<1 else data[-1]
        
    def cleanup(self):
        DrawableHUDSourceModule.cleanup(self)
        # request stop and wait for the thread to terminate
        self.sensor.stop()
        self.sensor_thread.join(1.0)

    def getData(self):
        """
        For abstract interface (source module). 
        """
        DrawableHUDSourceModule.getData(self)
        return self.lastdata

    def getUpdateInterval(self):
        """
        For abstract interface (source module). 
        """
        DrawableHUDSourceModule.getUpdateInterval(self)
        return self.frequency

