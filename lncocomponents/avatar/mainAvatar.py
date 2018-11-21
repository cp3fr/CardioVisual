'''
Main Avatar class. 

If no avatar library has been loaded, a new one is created and an avatar is added.
Additional avatars will be added to the pre-loaded library. 

@author: nathan
'''

from pyglet.gl import *
import avatar.avatarlib as avatarlib
from  os import path
from ctypes import *
from controller import getPathFromString
import numpy as np

from abstract.AbstractClasses import DrawableModule

#@todo: test if need to only Idle (update) after all avatars have been drawn - or if harm in doing so each time
#@todo: add support for shaders, VA_TRANS, DQUAT_TRANSF, etc
 

HALCA = None                        #global library

# Set the avatar data root
#avaRoot = path.abspath(path.join(path.dirname(path.abspath(__file__)), 'data'))
avaRoot = path.dirname(path.abspath(__file__))
if avaRoot[-1] != path.sep:
    avaRoot += path.sep      # HALCA needs a directory separator at the end


class ModuleMain(DrawableModule):    
    #Global config for all instances of avatars (HALCA params)
    globalConf = {
        'dataDir': avaRoot,
        'VA_TRANS': False,
        'DQUAT_TRANSF': False
    }

    defaultInitConf = {
        'name': 'avatar',
        'avatarCfg': 'AMan0004'     # file name of avatar config to load
    }
    
    defaultRunConf = {
        'position': [0,2,0],
        'glRotations': 'glRotatef(-90.0,1,0,0)',
        'shaderFile': ''
    }
        
    confDescription = [
       ('name', 'str', "Avatar"),
       ('avatarCfg', 'str', "Avatar CAL3D config file base name: corresponding .cfg file should be in ''lncocomponents/avatar/data'' directory."),
       ('position', 'str', "Default (translation) position [x,y,z]"),
       ('glRotations', 'str', "Rotation commands (to orient avatar) ie: glRotate(angle,x,y,z)"),
       ('shaderFile', 'str', "Shader file path. If empty, HALCA shaders used.")
   ]
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableModule.__init__(self, controller, initConfig, runConfigs)
        global HALCA, avaRoot
        
        #Load + init HALCA wrapper
        if not self.controller.gModuleList.has_key('avatarlib'):
            HALCA = avatarlib.Avatars(ModuleMain.globalConf).lib
            self.controller.addToModuleList('avatarlib', HALCA)
        else:
            HALCA = self.controller.gModuleList['avatarlib']
         
        #Massage filename + add avatar
        self.avatar = HALCA.addCharacter(self.initConf['avatarCfg'], self.initConf['avatarCfg']+'.cfg')
        if(self.avatar == -1):
            raise RuntimeError("Problem loading AVATAR. Check Animation / Configuration / Path, etc")    
        else:
            self.log("---> Successfully loaded avatar: " + self.initConf['name'] + " (" + str(self.avatar) + ")")
            self.log("---> HALCA Total number of avatars loaded: " + str(HALCA.numCharacters(None)))
        
        HALCA.Idle(None)
        
        self.controller.registerKeyboardAction( 'EQUAL MINUS', self.handlekey )

        
    def _moveAvatar(self,pos):
        if(isinstance(pos,str)):
            pos = eval(pos)
        HALCA.setTranslation(self.avatar,0,byref(cvecf(pos)))   #move whole body (joint=0)
        
    def _incAvatarScale(self):
        curScale = HALCA.getModelScale(self.avatar)             #get GLfloat array
        scale = np.ctypeslib.as_array(curScale[0],(3,1))        #make np array
        newScale = scale + 0.00005
        self.log("Increased avatar scale to: " + str(newScale))
        HALCA.setModelScale(self.avatar,cvecf(newScale))

    def _decAvatarScale(self):
        curScale = HALCA.getModelScale(self.avatar)             #get GLfloat array
        scale = np.ctypeslib.as_array(curScale[0],(3,1))        #make np array
        newScale = scale - 0.00005
        self.log("Decreased avatar scale to: " + str(newScale))
        HALCA.setModelScale(self.avatar,cvecf(newScale))
            
    def draw(self, window_width, window_height, eye=-1):
        DrawableModule.draw(self, window_width, window_height, eye)
        #global numAvatars, numDrawn
        glPushMatrix()
        
        if(len(self.activeConf['glRotations']) > 0):
            exec(compile( self.activeConf['glRotations'], '', 'exec' ))
                 
        self._moveAvatar(self.activeConf['position'])
        HALCA.DrawOne(self.avatar)

        glPopMatrix()
        
    def start(self, dt=0, duration=-1, configName=None):
        """
        Activate with the parameters passed in the conf
        """
        DrawableModule.start(self, dt, duration, configName)                    
        
    def stop(self, dt=0):
        DrawableModule.stop(self, dt)

    def cleanup(self):
        DrawableModule.cleanup(self)                

    def handlekey(self, keypressed = None):
        if keypressed == 'EQUAL':
            self._incAvatarScale()
        elif keypressed == 'MINUS':
            self._decAvatarScale()
        
#Helper functions
def cvecf(args):
    return (c_float * len(args))(*args)

def cveci(args):
    return (c_int * len(args))(*args)

def getArrayFromPointer(point):
    return np.array(ctypes.cast(lParam, ctypes.POINTER(ctypes.c_int)))

class Coord(Structure):
    _fields_ = [("x", c_float),
                ("y", c_float),
                ("z", c_float)]