'''
Created on Jan 16, 2011

@author: bh
@since: Winter 2011

@license: Distributed under the terms of the GNU General Public License (GPL).
'''

from os import path
import csv
from datetime import datetime
import pyglet

from abstract.AbstractClasses import BasicModule
from input import directinput


class ModuleMain(BasicModule):
    """
    A simple module to listen to joystick inputs
    """
    defaultInitConf = {
        'name': 'joystick',
        'id': '0',
        'logToCSV': True
    }
    
    defaultRunConf = {    
        'unpause': False,
        'endRoutine': False,
    }
    
    confDescription = [
        ('name', 'str', "Module listening to joysticks event and reacting to button press."),
        ('id', 'str', "DirectX identifier of the joystick", ['0', '1', '2', '3']),
        ('logToCSV', 'bool', "Save the logs of the buttons pressed in a Comma Separated Values text file"),
        ('unpause', 'bool', "Unpause the simulation at button press"),
        ('endRoutine', 'bool', "End the current routine at button press"),
        ('joystick', 'info', "DirectX object with these attributes:\n x, y, z, rx, ry, rz, hat_x, hat_y\nE.g. joystick.x is main horizontal axis"),
        ('currentButtons', 'info', "List of buttons currently pressed (integer ids)")
    ]

    def __init__(self, controller, initConfig=None, runConfigs=None):
        BasicModule.__init__(self, controller, initConfig, runConfigs)
            
        try:
            self.joystick = directinput.get_joysticks()[int(self.initConf['id'])]
        except:
            raise RuntimeError("Could not find joystick %s" % self.initConf['id'])   
        
        # start logger
        self.csvLogger = None
        if self.initConf['logToCSV']:
            now = datetime.today()
            self.csvLogger = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.initConf['name'] +  '.csv') , 'w'), lineterminator = '\n')
            self.csvLogger.writerow(['absTime', 'expTime', 'displayTime', 'routine', 'condition', 'button', 'reactionExpTime', 'reactionDisplayTime', 'pressDuration'])

        # init
        self.buttonpresstime = {}
        self.logline = {}
        self.currentButtons = []
        
        # connect button press event to appropriate method
        for b in self.joystick.button_controls:
            @b.event
            def on_press():
                self.onButtonPress()
            @b.event
            def on_release():
                self.onButtonRelease()
            
    def start(self, dt=0, duration=-1, configName=None):
        """
        Activate the engine with the parameters passed in the conf
        """
        BasicModule.start(self, dt, duration, configName)  
        # reset
        self.buttonpresstime = {}
        self.logline = {}
        self.currentButtons = []
        
        # open the device and start the reading of events
        self.joystick.open()
        pyglet.clock.schedule(self.update)
          
    def stop(self, dt=0):
        # get start times before stopping module
        startTimes = self.getStartingTimes()
        
        # unregister joystick listenner
        pyglet.clock.unschedule(self.update)
        self.joystick.close()
        self.currentButtons = []
            
        if self.csvLogger :
            # if no button was ever pressed, write a default entry line
            if len(self.logline) == 0:
                self.csvLogger.writerow( startTimes + [ self.controller._currentRoutine, self.controller._currentCondition,'', -1, -1, -1])
            else:
                for b in self.logline.keys():                    
                    # if a log line was started, but not finished in onKeyRelease
                    if len(self.logline[b]) > 0:
                        self.logline[b].append(-1)
                        self.csvLogger.writerow(self.logline[b])
            
        # stop module
        BasicModule.stop(self, dt)
        
    def update(self, dt):
        """
        The update is called regularly to update angle data
        """
        self.joystick.device.dispatch_events()
    
    def onButtonPress(self):
        # get times
        startTimes = self.getStartingTimes()
        
        # get button
        buttonsdown = [ i for i in range(len(self.joystick.buttons)) if self.joystick.buttons[i] ]
        buttonschanged = [i for i in buttonsdown if i not in self.currentButtons]
        self.currentButtons = buttonsdown
                    
        for b in buttonschanged:
            self.log("Button %s pressed"%str(b))
            # create entry for this button
            self.buttonpresstime[b] = self.controller.gTimeManager.experimentTime()
            self.logline[b] = []
            
            # act on key
            if self.activeConf['unpause']:
                responsetime = self.controller.gTimeManager.unpause()
            else:
                responsetime = self.buttonpresstime[b] - startTimes[1]
            # log    
            if self.csvLogger:            
                displayresponsetime =  self.buttonpresstime[b] - startTimes[2]
                self.logline[b] = startTimes + [ self.controller._currentRoutine, self.controller._currentCondition ] \
                                + [b, str("%.4f"%responsetime), str("%.4f"%displayresponsetime)]
          
    def onButtonRelease(self):
        
        # get button
        buttonsdown = [ i for i in range(len(self.joystick.buttons)) if self.joystick.buttons[i] ]
        buttonschanged = [i for i in self.currentButtons if i not in buttonsdown]
        self.currentButtons = buttonsdown
        
        # get only keys which were pressed after start
        if len(buttonschanged) > 0:
            for b in buttonschanged:
                self.log("Button %s released"%str(b))
                # get times
                if self.buttonpresstime.has_key(0):
                    keypressduration = self.controller.gTimeManager.experimentTime() - self.buttonpresstime[b]
                else:
                    keypressduration = -1
                # log
                if self.csvLogger and len(self.logline[b]) > 0:
                    self.logline[b].append( str("%.4f"%keypressduration) )
                    self.csvLogger.writerow(self.logline[b])
                    # keep but empty the log line for this button
                    self.logline[b] = []

            if self.activeConf['endRoutine']:
                self.controller.endCurrentRoutine()
        else:
            self.log("Ignored button %s release"%str(self.currentButtons))