#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Ocean Server OS5000 sensor driver, 
using the Enhanced Serial Port class of pyserial (http://pyserial.sf.net)  (C)2002 cliechti@gmx.net

You need to install the Scilab CP210x VCP driver first
http://www.silabs.com/products/mcu/Pages/USBtoUARTBridgeVCPDrivers.aspx

bruno.herbelin@epfl.ch
"""

import numpy as np
from serial import Serial
import re

class OS5000(Serial):
    def __init__(self, *args, **kwargs):
        #ensure that a reasonable timeout is set
        timeout = kwargs.get('timeout',0.1)
        if timeout < 0.01: timeout = 0.1
        kwargs['timeout'] = timeout
        Serial.__init__(self, *args, **kwargs)
        self.buf = ''
        self.sync()
        self.shift = np.zeros(3)
        self.values = np.zeros(3)
        
    def readline(self, maxsize=None, timeout=1):
        """maxsize is ignored, timeout in seconds is the max time that is way for a complete line"""
        tries = 0
        while 1:
            self.buf += self.read(24)
            pos = self.buf.find('\n')
            if pos >= 0:
                line, self.buf = self.buf[:pos+1], self.buf[pos+1:]
                return line
            tries += 1
            if tries * self.timeout > timeout:
                break
        line, self.buf = self.buf, ''
        return line

    def sync(self, timeout=1):
        tries = 0
        self.buf = ''
        self.flushInput()
        while self.buf != '$':
            self.buf = self.read(1)
            tries += 1
            if tries * self.timeout > timeout:
                break
        self.buf = ''
        
    def readData(self, timeout=1):
        #self.sync()
        try:
            # read sensor data and extract values
            line = self.readline(timeout=timeout)
            if len(line) > 0:
                vals = re.split('[CPRA]', line)
                v = np.array([ float(vals[1]), float(vals[2]), float(vals[3]) ])
            else:
                v = np.zeros(3)
            # add 360 each time the sensor made a 360 turn (per axis), substract when opposite
            self.shift -= np.greater( v -self.values, np.array([180.0, 180.0, 180.0])) * 360.0
            self.shift += np.less( v -self.values, np.array([-180.0, -180.0, -180.0])) * 360.0
            # remember value 
            self.values = v
            return (self.values + self.shift).copy()
        except:
            self.sync()

