'''
Created on Jul 8, 2010

@author: bh
@since: Winter 2012

@license: Distributed under the terms of the GNU General Public License (GPL).
'''
from os import path
import csv
import win32api, win32con, win32gui
from datetime import datetime

from abstract.AbstractClasses import BasicModule



class ModuleMain(BasicModule):
    """
    A simple module to listen to keyboard inputs
    """
    defaultInitConf = {
        'name': 'mouse',
        'logToCSV': True
    }
    
    defaultRunConf = {    
        'buttons': 'LEFT',
        'track_motion': False,
        'cursorVisible': True,
        'unpause': False,
        'endRoutine': True,
        'startPosition': '50, 50'
    }
    
    confDescription = [
        ('name', 'str', "Module listening to the mouse events and reacting to some button press."),
        ('logToCSV', 'bool', "Save the logs of the key pressed in a Comma Separated Values text file"),
        ('buttons', 'str', "List of buttons to listen to (space-separated list of LEFT RIGHT MIDDLE keywords)"),
        ('track_motion', 'bool', "Track every mouse movements (even without a button pressed)"),
        ('startPosition', 'str', "Put the mouse cursor at this position when starting\n(coordinates in % of screen dimensions, with a coma between X and Y)"),
        ('cursorVisible', 'bool', "shows or hides mouse cursor (disregarding 'hidecursor' display settings)"),
        ('unpause', 'bool', "Unpause the simulation at button press"),
        ('endRoutine', 'bool', "End the current routine at button release"),
        ('currentButtons', 'info', "List of buttons currently pressed"),
        ('currentPosition', 'info', "Coordinates of mouse cursor (if track_motion enabled)")
    ]
   
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        BasicModule.__init__(self, controller, initConfig, runConfigs)
        self.buttonpresstime = {}
        self.logline = {}
        self.motionloglines = []
        self.currentButtons = []
        self.currentPosition = []
        
        self.csvLogger = None
        if self.initConf['logToCSV']:
            now = datetime.today()
            self.csvLogger = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.initConf['name'] + '.csv') , 'w'), lineterminator = '\n')
            self.csvLogger.writerow(['absTime', 'expTime', 'displayTime', 'routine', 'condition', 'button', 'x', 'y', 'reactionExpTime', 'reactionDisplayTime', 'pressDuration'])
            
    def start(self, dt=0, duration=-1, configName=None):
        """
        Activate the engine with the parameters passed in the conf
        """
        BasicModule.start(self, dt, duration, configName)  
                
        self.showCursor = self.activeConf['cursorVisible']       
                
        self.cursorvisible, tmp, coordinates = win32gui.GetCursorInfo()
        print('cursor visible: ',self.cursorvisible,'showCursor: ',self.showCursor)
        
        # show the cursor if needs to be shown :
        
        if self.showCursor:
            win32api.ShowCursor(1)
        else:
            win32api.ShowCursor(0)
            
        hCurs1 = win32api.LoadCursor(0, win32con.IDC_CROSS)
        win32api.SetCursor(hCurs1)
   
        # get the screen width and height for coordinates %
        screenWidth = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        screenHeight = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        # move the cursor to the start position
        x, y = self.activeConf['startPosition'].split(',')
        win32api.SetCursorPos( (int(x) * screenWidth / 100, int(y) * screenHeight / 100) )
        
        # register listeners
        self.controller.registerMouseAction(self.activeConf['buttons'], self.onButtonPress, self.onButtonRelease)
        if self.activeConf['track_motion']:
            self.controller.registerMouseMotion(self.onMotion)
                
        self.buttonpresstime = {}
        self.logline = {}
        self.motionloglines = []
        self.currentButtons = []
        self.currentPosition = []
        
    def setPosition(self, x, y):
        screenWidth = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        screenHeight = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        win32api.SetCursorPos( (int(x) * screenWidth / 100, int(y) * screenHeight / 100) )
        
            
    def stop(self, dt=0):
        # get start times before stopping module
        startTimes = self.getStartingTimes()
        
        # unregister keyboard listenner
        self.controller.unregisterMouseAction(self.activeConf['buttons'], self.onButtonPress, self.onButtonRelease)   
        self.currentButtons = []
        if self.activeConf['track_motion']:
            self.controller.unregisterMouseMotion(self.onMotion)
        
        if self.csvLogger :
            # if no key was ever pressed, write a default entry line
            if len(self.logline) == 0:
                self.csvLogger.writerow( startTimes + [ self.controller._currentRoutine, self.controller._currentCondition, '', -1, -1, -1, -1, -1] )
            else:
                for k in self.logline.keys():
                    # if a log line was started, but not finished in onKeyRelease
                    if len(self.logline[k]) > 0:
                        self.logline[k].append(-1)
                        self.csvLogger.writerow(self.logline[k])
            # write also the log lines recorded during motion
            if len(self.motionloglines) > 0:
                self.csvLogger.writerows(self.motionloglines)
            
        # # set the cursor back to its original visibility (i.e. hides it if needed)
        # if self.cursorvisible:
            # win32api.ShowCursor(1)
        # else:
        #win32api.ShowCursor(0)
            
        # self.cursorvisible, tmp, coordinates = win32gui.GetCursorInfo()
        # print('cursor visible: ',self.cursorvisible,'showCursor: ',self.showCursor)
        
            
        # hCurs1 = win32api.LoadCursor(0, win32con.IDC_CROSS)
        # win32api.SetCursor(hCurs1)
            
        # stop module
        BasicModule.stop(self, dt)
        self.currentPosition = []
        
    def onButtonPress(self, x, y, buttonpressed=None):
     
        # get times
        startTimes = self.getStartingTimes()
        
        # get key
        self.currentButtons.append(buttonpressed)
        self.log("%s button pressed (%d, %d)"%(buttonpressed, x,y))
        
        # create entry for this key
        self.buttonpresstime[buttonpressed] = self.controller.gTimeManager.experimentTime()
        self.logline[buttonpressed] = []
        
        # act on key
        if self.activeConf['unpause']:
            responsetime = self.controller.gTimeManager.unpause()
        else:
            responsetime = self.buttonpresstime[buttonpressed] - startTimes[1]
        # log    
        if self.csvLogger:            
            displayresponsetime =  self.buttonpresstime[buttonpressed] - startTimes[2]
            self.logline[buttonpressed] = startTimes + [ self.controller._currentRoutine, self.controller._currentCondition ]\
                                     + [buttonpressed, x, y, str("%.4f"%responsetime), str("%.4f"%displayresponsetime)]
        
    def onButtonRelease(self, x, y, buttonpressed=None):
    
        # get only keys which were pressed after start
        if self.currentButtons.count(buttonpressed):
            self.currentButtons.remove(buttonpressed)
            self.log("%s button released (%d, %d)"%(buttonpressed, x,y))
            
            # get times
            keypressduration = self.controller.gTimeManager.experimentTime() - self.buttonpresstime[buttonpressed]
        
            # log
            if self.csvLogger and len(self.logline[buttonpressed]) > 0:
                # add the computed duration
                self.logline[buttonpressed].append( str("%.4f"%keypressduration) )
                self.csvLogger.writerow(self.logline[buttonpressed])
                # write also the log lines recorded during motion
                if len(self.motionloglines) > 0:
                    self.csvLogger.writerows(self.motionloglines)
                    self.motionloglines = []
                # keep but empty the log line for this key
                self.logline[buttonpressed] = []
                
            if self.activeConf['endRoutine']:
                self.controller.endCurrentRoutine()
        else:
            self.log("Ignored %s button release"%buttonpressed)

    def onMotion(self, x, y, buttonspressed=""):
    
        self.currentPosition = [x, y]
        # log
        if self.csvLogger:
            times = self.getStartingTimes()
            relativetime = self.controller.gTimeManager.experimentTime() - times[1]
            displayrelativetime =  self.controller.gTimeManager.experimentTime() - times[2]
            logline = times + [ self.controller._currentRoutine, self.controller._currentCondition, buttonspressed, x, y, str("%.4f"%relativetime), str("%.4f"%displayrelativetime), -1]
            if buttonspressed == "":
                self.motionloglines = []
                self.csvLogger.writerow( logline )
            else:
                self.motionloglines.append( logline )
