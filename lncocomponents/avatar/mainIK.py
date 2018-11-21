'''
Animate an avatar by attaching sensors to joints (IK).
Can use pre-loaded or real-time sensor data

@author: Nathan, Tobias Leugger
@since: Early 2011
'''

from pyglet.gl import *
from ctypes import *
import avatar.IK as iklib
import numpy as np

from abstract.AbstractClasses import BasicModule

class ModuleMain(BasicModule):
    defaultInitConf = {
        'name': 'mocapIK',
        'avatarName': 'avatar',       #name of module to attach IK to
        'sourceName': 'reactor',       #name of module providing sensor data
        'refSensor': 1,
        'headSensor': 2,
        'leftHandSensor': 3,
        'rightHandSensor': 4,
        'leftLegSensor': 5,
        'rightLegSensor': 6        
    }
    
    defaultRunConf = {
        'armsIK': True,
        'bodyIK': False,
        'legsIK': False
    }
    
    confDescription = [
       ('name', 'str', "Inverse Kinematics"),
       ('avatarName', 'str', "Name of avatar module to whom you wish to attach IK"),
       ('sourceName', 'str', "Name of source module containing sensor positions"),
       ('refSensor', 'int', "Number for reference sensor (place at hip for re-referencing)"),
       ('headSensor', 'int', "Number for head sensor (for body IK)"),
       ('leftHandSensor', 'int', "Number for left hand sensor"),
       ('rightHandSensor', 'int', "Number for right hand sensor"),
       ('leftLegSensor', 'int', "Number for left leg sensor"),
       ('rightLegSensor', 'int', "Number for right leg sensor"),
       ('armsIK', 'bool', "Attach sensors (defined above) to perform arm IK", True),
       ('bodyIK', 'bool', "Attach sensors (defined above) to perform body IK", False),
       ('legsIK', 'bool', "Attach sensors (defined above) to perform legs IK", False)   
   ]
 
        
    def __init__(self, controller, initConfig=None, runConfigs=None):
        BasicModule.__init__(self, controller, initConfig, runConfigs)
        
        # Get Avatar library 
        try:
            self.HALCA = self.controller.gModuleList['avatarlib']
        except:
            raise RuntimeError("Cannot find instance of HALCA already loaded. Check that the IK component is after the avatar")

        # Get Avatar
        try:
            self.avatarID = self.controller.gModuleList[self.initConf['avatarName']].avatar
        except:
            raise RuntimeError("Couldn't get avatar ID. Ensure avatar component is before IK component.")

        #init IK library
        self.IK = iklib.IK(self.avatarID,self.HALCA)
       
        # Attach to source
        try:
            self.source = self.controller.gModuleList[self.initConf['sourceName']]
        except:
            raise RuntimeError("Cannot find instance of source module" + self.controller.gModuleList['sourceName'] + 
                               "Check that the source component is before IK")
        
        #Arrays will be indexed from 0; numbers on mocap start at 1
        self.refSensor = self.initConf['refSensor'] - 1 
        self.headSensor = self.initConf['headSensor'] - 1      
        self.leftHandSensor = self.initConf['leftHandSensor'] - 1 
        self.rightHandSensor = self.initConf['rightHandSensor'] - 1
        self.leftLegSensor = self.initConf['leftLegSensor'] - 1
        self.rightLegSensor = self.initConf['rightLegSensor'] - 1
        
    def start(self, dt=0, duration=-1, configName=None):
        """
        Activate with the parameters passed in the conf
        """
        BasicModule.start(self, dt, duration, configName)

        #Start IK updates 
        pyglet.clock.schedule_interval(self._updateIK,self.source.getUpdateInterval())

    def stop(self, dt=0):
        BasicModule.stop(self, dt)
          
    def _updateIK(self,dt):
        '''
            Get bone positions from source module and set them in the IK module. 
            Then perform IK computations
        '''        
        #self.HALCA.Idle(None)
        
        #Get a matrix of sensor positions
        curPosMatrix = self.source.getPositions()
        ref = curPosMatrix[:,self.refSensor]                
        
        if(self.activeConf['armsIK']):
            lrawpos = curPosMatrix[:,self.leftHandSensor]
            rrawpos = curPosMatrix[:,self.rightHandSensor]
            ROFFSET = 0.0
            #swap y and z (coordinate systems)
            lpos = [-(lrawpos[0]-ref[0]), lrawpos[2]-(ref[2]+ROFFSET), lrawpos[1]-ref[1]]
            rpos = [-(rrawpos[0]-ref[0]), rrawpos[2]-(ref[2]+ROFFSET), rrawpos[1]-ref[1]]
            self.IK.setLeftArmPos(lpos)
            self.IK.setRightArmPos(rpos)
            
        if(self.activeConf['bodyIK']):
            hrawpos = curPosMatrix[:,self.headSensor]
            hpos = [-(hrawpos[0]-ref[0]), hrawpos[2]-ref[2], hrawpos[1]-ref[1]]
            self.IK.setHeadPos(hpos)
            
        if(self.activeConf['legsIK']):
            lrawpos = curPosMatrix[:,self.leftLegSensor]
            rrawpos = curPosMatrix[:,self.rightLegSensor]
            ROFFSET = 0.0
            #swap y and z (coordinate systems)
            lpos = [-(lrawpos[0]-ref[0]), lrawpos[2]-(ref[2]+ROFFSET), lrawpos[1]-ref[1]]
            rpos = [-(rrawpos[0]-ref[0]), rrawpos[2]-(ref[2]+ROFFSET), rrawpos[1]-ref[1]]

            self.IK.setLeftLegPos(lpos)
            self.IK.setRightLegPos(rpos)
            
            
        self.IK.doIK(self.activeConf['armsIK'],self.activeConf['bodyIK'],self.activeConf['legsIK'])


#Helper functions
def cvecf(args):
    return (c_float * len(args))(*args)

def cveci(args):
    return (c_int * len(args))(*args)
