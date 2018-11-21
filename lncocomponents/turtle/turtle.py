'''
Created on Sept 01, 2018

@author: cpf
@since: september 2018

@license: Distributed under the terms of the GNU General Public License (GPL).
'''

from os import path
from time import sleep
import csv, re, glob
import threading, socket
import numpy as np
import math as mt
from planar import Affine
from planar import Vec2

from datetime import datetime
from pyglet.gl import *
from pyglet import image
from pyglet.clock import _default_time_function as time

#pylnco modules
from controller import getPathFromString
from display.tools import *
from abstract.AbstractClasses import DrawableModule
from abstract.AbstractClasses import DrawableHUDModule
from abstract.AbstractClasses import DrawableHUDSourceModule

#module classes
from CircularBuffer import CircularBuffer
from Randomization import Randomization
from EventScheduling import EventScheduling
from TurtleController import TurtleController
    
# main module
class ModuleMain(DrawableModule):
    
    
    defaultInitConf = {
        'name': 'turtle',
        'logToCSV': False,
    }

    defaultRunConf = {
        'ControlInput':          "3",
        'StartPosition':         "[ [50.0, 10.0] ]",
        'GoalPosition':          "[ [25.0, 79.2825], [50.0, 90.0], [75.0, 79.2825] ]",
        'DeviationAngle':        "[ 0.0, 20.0, 40.0, 60.0, 0.0, -20.0, -40.0, -60.0 ]",
        'BeepDistanceFromStart': "[ 1.0 ]",
        'InterBeepInterval':     "[ 0.6, 0.8 ]",
        'TurtleImage':           "$EXPYVRROOT$/lncocomponents/turtle/turtle.png",
    }
    
    confDescription = [
        ('name', 'str', "..."),
        ('logToCSV', 'bool', "..."),
        ('ControlInput', 'code', "1=eye 2=head 3=mouse"),
        ('StartPosition', 'code', "..."),
        ('GoalPosition', 'code', "..."),
        ('DeviationAngle', 'code', "..."),
        ('BeepDistanceFromStart', 'code', "..."),
        ('InterBeepInterval', 'code', "..."),
        ('TurtleImage', 'str', "..."),
    ]
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableModule.__init__(self, controller, initConfig, runConfigs)

        # make a randomizatin object and randomize the order of trials: read randomization parameter list for the experimental trials (specify the number of values per row, and the path)
        # dict = {
        # "startPosition":         [ [50.0, 10.0] ], 
        # "goalPosition":          [ [25.0, 79.2825], [50.0, 90.0], [75.0, 79.2825] ],
        # "deviationAngle":        [0.0, 15.0, 30.0, 45.0, 60.0, 0.0, -15.0, -30.0, -45.0, -60.0],
        # "beepDistanceFromStart": [1.0],
        # "interBeepInterval":     [0.4, 0.8, 1.2]
        # }
        
        dict = {
        "startPosition":         self.activeConf["StartPosition"], 
        "goalPosition":          self.activeConf["GoalPosition"],
        "deviationAngle":        self.activeConf["DeviationAngle"],
        "beepDistanceFromStart": self.activeConf["BeepDistanceFromStart"],
        "interBeepInterval":     self.activeConf["InterBeepInterval"],
        }
        
        self.rand = Randomization(dict, shuffle=True)
        # print("number of trials",self.rand.getNumTrials())
        
        # for i in range(self.rand.getNumTrials()):
            # print('trial: ',i,'trialDict: ',self.rand.get(i))
        
        #set trial number, used to iterate over the randomization list
        self.numTrial = -1;
        
        self.interBeepInterval = 0.0
        
        #create a turtle kinematics object, taking care of updating turtle position on the screenturtle kinematics module arguments, tuned by hand, indicating the size of buffer across which we take the average (filtering) in order to smooth the turtle movements and maximum distance criterion whithin which input commands are accepted 
        self.buffSize = 40 
        self.maxDistCommandTurtle = 0.1
        self.maxDistCommandStart = 0.020
        
        
        # create an event scheduling event and set maximum distance from start for trial initiation
        self.E = EventScheduling();
        self.E.setDistance(self.maxDistCommandStart)

        # init some variables
        self.screenSize = []
        self.commandPos = []
        
        #set fixation cross positions
        self.startCrossPos = [50,50]
        self.goalCrossPos = [50,50]
        
        #prepare output logging
        self.logActive = self.initConf['logToCSV']
        if self.logActive:
            now = datetime.today()
            self.csvLogger = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.initConf['name'] +  '.csv') , 'w'), lineterminator = '\n')
            hdr = ['expTime', 'tStart', 'tAction', 'currTime', 'numTrial', 'inputType', 'devAngle','startPosX','startPosY', 'goalPosX', 'goalPosY', 'beepDistStart', 'interBeepInterval', 'turtlePosX', 'turtlePosY', 'turtleAngle', 'commandPosX', 'commandPosY', 'eyePosX', 'eyePosY', 'headPosX','headPosY', 'mousePosX','mousePosY', 'screenSizeX', 'screenSizeY', 'buffSize', 'maxDistCommandTurtle', 'maxDistCommandStart']
            self.csvLogger.writerow(hdr)
            
        # init graphics
        self.pictures = {}
        self.lists = {}
        
        # load all the images we're going to display
        for conf in self.runConfs.values():
            for pict in ['TurtleImage']:
                imageName = conf[pict]
                if imageName in self.pictures or len(imageName) == 0 :
                    # We've already loaded that image
                    continue
                pic = self.pictures[imageName] = image.load( getPathFromString(imageName))
                texture = pic.get_texture()
                # Compile a display list for a quad with texture coordinates
                t = texture.tex_coords
                self.lists[imageName] = glGenLists(1)
                glNewList(self.lists[imageName], GL_COMPILE)
                glShadeModel(GL_FLAT)
                glEnable(GL_BLEND)
                glBlendEquation(GL_FUNC_ADD)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)# transparency based on Source Alpha Value
                glBindTexture(texture.target, texture.id)
                glScalef( float(pic.width), float(pic.height), 1.0)
                glBegin(GL_QUADS)
                glTexCoord2f(t[0], t[1])
                glVertex3f(-0.5, -0.50, 0.0)
                glTexCoord2f(t[3], t[4])
                glVertex3f(0.50, -0.50, 0.0)
                glTexCoord2f(t[6], t[7])
                glVertex3f(0.50, 0.50, 0.0)
                glTexCoord2f(t[9], t[10])
                glVertex3f(-0.50, 0.50, 0.0)
                glEnd()
                glEndList()
        
        #set the update time for the thread
        self.updateTime = 0.01 # 100Hz
        

    # present visual stimuli
    def draw(self, window_width, window_height, eye=-1):
        DrawableModule.draw(self, window_width, window_height, eye)

        # update screen size info
        self.screenSize = [float(window_width), float(window_height)]
    
        # #draw a line
        # glLineWidth(20); 
        # glColor3f(1.0, 1.0, 1.0);
        # glBegin(GL_LINES);
        # glVertex3f(0.2, -18, -50);
        # glVertex3f(0.2, 18, -50);
        # glEnd();
        
        # Turn blending
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glEnable(GL_BLEND)
        glEnable(GL_TEXTURE_2D)
        # Blending Function For transparency Based On Source Alpha Value
        glBlendEquation(GL_FUNC_ADD)
        glBlendFunc(GL_SRC_ALPHA, GL_SRC_ALPHA)
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, 1, 0, 1, 100, -100)
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)
        
        #=============#
        # draw turtle #
        #=============#
        if self.E.showTurtle():
            image = self.imagelist[0]
            glPushMatrix()
            glLoadIdentity()
            #draw turtle at current position
            if len(self.T.getPos()) == 2:
                glTranslatef(self.T.getPos()[0], self.T.getPos()[1], -50.0)
            #first scale then rotate
            glScalef(1.0/ self.screenSize[0], 1.0/ self.screenSize[1], 1.0)
            #draw turtle with current rotation
            if isinstance(self.T.getRot(),float):
                glRotatef(self.T.getRot(), 0.0, 0.0, 1.0)
                #glRotatef(0.0, 0.0, 0.0, 1.0)
            #fixed values
            
            glColor4f(1.0, 1.0, 1.0, 1.0)
            glCallList(self.lists[self.activeConf[image]]) 
            glPopMatrix()
            
        
              
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopAttrib()
        
        
    # start module
    def start(self, dt=0, duration=-1, configName=None):
        DrawableModule.start(self, dt, duration, configName)
        
        #starting time of the routine
        self.tStart = time()
        self.tAction = time()
        self.tFinish = time()
        
        #raise the trial counter
        self.numTrial += 1;
        
        #set the event to init wait
        self.E.setEvent(0)
       
        #control input for current trial (1=eye 2=head 3=mouse)
        self.inputSelection = self.activeConf["ControlInput"]
        
        #get dictionairy for the current trial
        trialDict = self.rand.get(self.numTrial)
        self.startPos = trialDict['startPosition'] 
        self.goalPos = trialDict['goalPosition']
        self.angDev = trialDict['deviationAngle']
        self.beepDistStart = trialDict['beepDistanceFromStart']
        self.interBeepInterval = trialDict['interBeepInterval']
        
        #some event timing variables
        self.commandPos = []

        #variables receiving current input from eyetracker and mouse modules
        self.eyePos = []
        self.headPos = []
        self.mousePos = []
        self.startCrossPos = self.startPos
        self.goalCrossPos = self.goalPos
        
        #make a list of objects to display
        self.imagelist = []  
        self.imagelist.append('TurtleImage')

        #reset the turtle kinematics module to start parameters
        if self.inputSelection == 1:
            self.T = TurtleController("directionControllerNearRange",self.startPos, self.goalPos, self.angDev, self.buffSize, self.maxDistCommandTurtle)
        else:
            self.T = TurtleController("positionController",self.startPos, self.goalPos, self.angDev, self.buffSize, self.maxDistCommandTurtle)
            #self.T = TurtleController("positionController",self.startPos, self.goalPos, self.angDev, self.buffSize, self.maxDistCommandTurtle)
            
        # start update
        pyglet.clock.schedule_interval(self.update, self.updateTime)
        

    # stop module
    def stop(self, dt=0):
        DrawableModule.stop(self, dt)
        # unschedule updates
        pyglet.clock.unschedule(self.update)
              
              
    # cleanup module
    def cleanup(self): 
        DrawableModule.cleanup(self)
        print "closing down"  
        
    # update module
    def update(self, dt):

        #selection of input command according to active configuration
        #eye
        if self.inputSelection == 1:
            if len(self.eyePos)==2:
                self.commandPos = self.eyePos
        #head
        elif self.inputSelection == 2:
            if len(self.headPos)==2:
                self.commandPos = self.headPos
        #mouse 
        else:
           if len(self.mousePos)==2:
               #need scaling to get into 0-1 range
               self.commandPos = [self.mousePos[0]/self.screenSize[0], self.mousePos[1]/self.screenSize[1]]
            
        #add input to turtle module if valid input received
        if len(self.commandPos) == 2:
            self.T.set(self.commandPos)
        
        #update turtle module
        self.T.update()
        
        #print(self.commandPos)
        #==============#
        # Event Timing #
        #==============#
       
        #initial wait
        if self.E.getEvent() == 0:    
            #check distance between command and start position
            if self.E.evalDuration(2.0): #time in sec
                self.E.setEvent(1)
        #go to start
        elif self.E.getEvent() == 1:
            #check distance between command and start position
            if self.E.evalDistance(self.T.getDistCommandStart()):
                self.tAction = time()
                self.T.unfreeze()
                self.E.setEvent(2)
        #action
        elif self.E.getEvent() == 2:
            #check distance between turtle (distorted) and goal position
            if self.E.evalDistance(self.T.getDistGoal()):
                self.E.setEvent(3)
        #final wait
        elif self.E.getEvent() == 3:
                self.controller.endCurrentRoutine() #but note that no data will be logged in this case
        
        
        #================#
        # Output Logging #
        #================#
        
        # log data during action period
        if self.logActive and self.E.getEvent() == 2:
            
            #Wantlist
            #expTime tStart tAction currTime trial inputType angle 
            #startPos goalPos turtlePos turtleAng 
            #commandPos eyePos headPos mousePos
            #screenSize buffSize maxDistCommandTurtle maxDistCommandStart
            
            #expTime tStart tAction currTime trial inputType angle startPos goalPos turtlePos turtleAng 
            line = [ self.controller.gTimeManager.experimentTime(), 
                     self.tStart,
                     self.tAction,
                     time(),
                     self.numTrial,
                     self.inputSelection, 
                     self.angDev,
                     self.startPos[0]/100.0, #convert to 0-1 range
                     self.startPos[1]/100.0, #convert to 0-1 range 
                     self.goalPos[0]/100.0, #convert to 0-1 range 
                     self.goalPos[1]/100.0, #convert to 0-1 range
                     self.beepDistStart,
                     self.interBeepInterval,
                    ]
            
            #turtlePos
            var = self.T.getPos();
            if len(var) == 2:
                line.extend(var)
            else:
                line.extend(['NaN','NaN'])
            
            #turtleAng
            var = self.T.getRot();
            if isinstance(var, float) == 1:
                line.extend([var])
            else:
                line.extend('NaN')
                
            #commandPos
            var = self.commandPos;
            if len(var) == 2:
                line.extend(var)
            else:
                line.extend(['NaN','NaN'])
            
            #eyePos
            var = self.eyePos;
            if len(var) == 2:
                line.extend(var)
            else:
                line.extend(['NaN','NaN'])    
            
            #headPos
            var = self.headPos;
            if len(var) == 2:
                line.extend(var)
            else:
                line.extend(['NaN','NaN']) 
                
            #mousePos
            var = self.mousePos;
            if len(var) == 2:
                line.extend([var[0]/self.screenSize[0], var[1]/self.screenSize[1]]) #convert to 0-1 range
            else:
                line.extend(['NaN','NaN'])
            
            #screenSize buffSize maxDistCommandTurtle maxDistCommandStart
            line.extend([self.screenSize[0], self.screenSize[1], self.buffSize, self.maxDistCommandTurtle, self.maxDistCommandStart])
            
            #write output
            self.csvLogger.writerow(line)
