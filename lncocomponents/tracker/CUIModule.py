'''
Created on Feb 2, 2011

@author: bh
@since: Winter 2011

@license: Distributed under the terms of the GNU General Public License (GPL).
'''

from os import path
import csv
from datetime import datetime
import pyglet
from pyglet.gl import *

from abstract.AbstractClasses import DrawableHUDSourceModule
from input import base
from input import directinput


class ModuleMain(DrawableHUDSourceModule):
    """
    A simple module to listen to CUI board inputs
    http://www.create.ucsb.edu/~dano/CUI/
    """
    defaultInitConf = {
        'name': 'CUIboard',
        'logToCSV': True
    }
    
    confDescription = [
       ('name', 'str', "CUI board Input"),
       ('logToCSV', 'bool', "Save the logs of the key pressed in a Comma Separated Values text file"),
       ('cui', 'info', "DirectX object with these attributes:\n x, y, z, rx, ry, rz")
    ]

    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableHUDSourceModule.__init__(self, controller, initConfig, runConfigs)
                   
        self.cui = None 
        for dev in directinput.get_devices():
            if dev.name.find('CUI') > -1:
                self.cui = CUI(dev)

        if self.cui is None:
            raise RuntimeError("Could not find any CUI board connected")   
            
        # start logger
        self.csvLogger = None
        if self.initConf['logToCSV']:
            now = datetime.today()
            self.csvLogger = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.initConf['name'] +  '.csv') , 'w'), lineterminator = '\n')
        
    def start(self, dt=0, duration=-1, configName=None):
        """
        Activate the engine with the parameters passed in the conf
        """
        DrawableHUDSourceModule.start(self, dt, duration, configName)  
        self.cui.open()
        pyglet.clock.schedule(self.update)
          
    def stop(self, dt=0):
        DrawableHUDSourceModule.stop(self, dt)
        pyglet.clock.unschedule(self.update)
        self.cui.close()
        
    def update(self, dt):
        """
        The update is called regularly to update data
        """
        if not self.started:
            return
            
        self.cui.device.dispatch_events()

        if self.initConf['logToCSV']:
            line = [ self.controller.gTimeManager.experimentTime() ]
            line.extend( [ self.cui.x, self.cui.y, self.cui.z, self.cui.rx, self.cui.ry, self.cui.rz ] )
            self.csvLogger.writerow(line)
            
    def draw(self, window_width, window_height):
        DrawableHUDSourceModule.draw(self, window_width, window_height)
              
        glTranslatef( window_width / 2, window_height / 12, 0)
    
        # CUI x, y, z are axis of accelerometer
        glColor3f(1, 1, 0)
        glTranslatef( 0, window_height / 10, 0)
        glRectd(0, 0, self.cui.x * window_width / 2, window_height / 12)
        glTranslatef( 0, window_height / 10, 0)
        glRectd(0, 0, self.cui.y * window_width / 2, window_height / 12)
        glTranslatef( 0, window_height / 10, 0)
        glRectd(0, 0, self.cui.z * window_width / 2, window_height / 12)
    
        # rx is BVP
        glColor3f(1, 0, 0)
        glTranslatef( 0, window_height / 10, 0)
        glRectd(0, 0, self.cui.rx * window_width / 2, window_height / 12)
        # ry is SCL
        glColor3f(1, 0, 1)
        glTranslatef( 0, window_height / 10, 0)
        glRectd(0, 0, self.cui.ry * window_width / 2, window_height / 12)
        # ry is pressure
        glColor3f(0, 1, 1)
        glTranslatef( 0, window_height / 10, 0)
        glRectd(0, 0, self.cui.rz * window_width / 2, window_height / 12)

    def getData(self):
        """
        For abstract interface (reactor is a source module). Keeping getPositions() for old calls to positions
        """
        DrawableHUDSourceModule.getData(self)
        return [ self.cui.x, self.cui.y, self.cui.z, self.cui.rx, self.cui.ry, self.cui.rz ]

    def getUpdateInterval(self):
        """
        For abstract interface (reactor is a source module). 
        """
        return DrawableHUDSourceModule.getUpdateInterval(self)


class CUI(object):

    def __init__(self, device):
        self.device = device

        self.x = 0
        self.y = 0
        self.z = 0
        self.rx = 0
        self.ry = 0
        self.rz = 0

        self.x_control = None
        self.y_control = None
        self.z_control = None
        self.rx_control = None
        self.ry_control = None
        self.rz_control = None

        def add_axis(control):
            name = control.name
            scale = 2.0 / (control.max - control.min)
            bias = -1.0 - control.min * scale
            if control.inverted:
                scale = -scale
                bias = -bias
            setattr(self, name + '_control', control)

            @control.event
            def on_change(value):
                setattr(self, name, value * scale + bias)

        for control in device.get_controls():
            if isinstance(control, base.AbsoluteAxis):
                if control.name in ('x', 'y', 'z', 'rx', 'ry', 'rz', 
                                    'hat_x', 'hat_y'):
                    add_axis(control)

    def open(self, window=None, exclusive=False):
        '''Open the joystick device.  See `Device.open`.
        '''
        self.device.open(window, exclusive)

    def close(self):
        '''Close the joystick device.  See `Device.close`.
        '''
        self.device.close()
