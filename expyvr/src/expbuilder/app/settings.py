"""
@author: Tobias Leugger
@since: Spring 2010

@attention: Adapted from parts of the PsychoPy library
@copyright: 2009, Jonathan Peirce, Tobias Leugger
@license: Distributed under the terms of the GNU General Public License (GPL).


"""

from param import Param
import display.mode 

class CameraSettings:
    """
    This component stores general info about the camera
    """
    def __init__(self, exp, posX=0, posY=0, posZ=0, angleX=0, angleY=0, angleZ=0):
        self.exp = exp
        self.params = {}
        self.order = ['posX', 'posY', 'posZ', 'angleX', 'angleY', 'angleZ'] 
        self.params['posX'] = Param(float(posX), valType='float', 
            hint="The x position of the camera")
        self.params['posY'] = Param(float(posY), valType='float', 
            hint="The y position of the camera")
        self.params['posZ'] = Param(float(posZ), valType='float', 
            hint="The z position of the camera")
        self.params['angleX'] = Param(float(angleX), valType='float', 
            hint="The angle around the x-axis of the camera")
        self.params['angleY'] = Param(float(angleY), valType='float', 
            hint="The angle around the y-axis of the camera")
        self.params['angleZ'] = Param(float(angleZ), valType='float', 
            hint="The angle around the z-axis of the camera")
        
    def getType(self):
        return self.__class__.__name__



class WindowSettings:
    """
    This component stores general info about a window where the experiment is
    displayed
    
    
    input parameters simplified by JL November 2011
    """
    '''

    def __init__(self, exp, name='win', mode='mono', size=(800,600), fov=60.0, fullscreen=False, flip=False, color=(0.0,0.0,0.0), screenid=1):
        self.exp = exp
        self.params = {}
        self.order = ['mode', 'size', 'fov', 'fullscreen', 'screenid', 'flipScreen', 'color']
        self.params['mode'] = Param(mode, valType='str', 
            allowedVals=['mono', 'stereo', 'hmd', 'stereo alternate','minicave'],  hint="Which output rendering mode to use")
        self.params['size'] = Param(size, valType='code',  hint="Window size (W,H) in pixel")
        self.params['fullscreen'] = Param(fullscreen, valType='bool',  hint="Window starts fullscreen?")
        self.params['screenid'] = Param(screenid, valType='int',  hint="Screen target for fullscreen")
        self.params['flipScreen'] = Param(flip, valType='bool',  hint="Flip scene to top")
        self.params['fov']= Param(fov, valType='float',  hint="Horizontal field of view (degrees)")
        self.params['color'] = Param(color, valType='code',  hint="Window background color (R,G,B)")
    '''
    def __init__(self, exp, name='win', mode='mono', size=(800,600), fov=50.0, 
                 fullscreen=False, hidecursor=False, mousecameracontrol=False, flip=False, color=(0.0,0.0,0.0), screenid=1,
                 focallength=0.1, eyeseparation=0.001):
        self.exp = exp
        self.params = {}
        self.order = ['mode', 'size', 'fullscreen', 'screenid', 'hidecursor', 'mousecameracontrol', 'flipScreen', 'mirror_3D', 'color','fov','focallength', 'eyeseparation']
        
        self.params['mode'] = Param(mode, valType='str', allowedVals=display.mode.__all__,  hint="Which rendering device to use")
        self.params['size'] = Param(size, valType='code',  hint="Window size (W,H) in pixel")
        self.params['fullscreen'] = Param(fullscreen, valType='bool',  hint="Window starts fullscreen?")
        self.params['hidecursor'] = Param(hidecursor, valType='bool',  hint="Hide cursor?")
        self.params['mousecameracontrol'] = Param(mousecameracontrol, valType='bool',  hint="Control the camera with the mouse")
        self.params['flipScreen'] = Param(flip, valType='bool',  hint="Flip screen up side down (and swap eyes in stereo)")
        self.params['mirror_3D'] = Param(flip, valType='bool',  hint="Mirror the rendering of 3D objects (not HUD)")
        self.params['screenid'] = Param(screenid, valType='int',  hint="Screen target for fullscreen")
        self.params['fov']= Param(fov, valType='float',  hint="Horizontal field of view (degrees)")
        self.params['focallength']= Param(focallength, valType='float',  hint="Focal length for stereoscopy")
        self.params['eyeseparation']= Param(eyeseparation, valType='float',  hint="Horizontal eyes separation for stereoscopy")
        self.params['color'] = Param(color, valType='code',  hint="Window background color (R,G,B)")
    

    
    def getType(self):
        return self.__class__.__name__


        
class LoggerSettings():
    """
    This component stores general info about how to log the experiment
    """
    def __init__(self, exp, expname='expyvr', logtype='console', logfreq=60, savepath='$EXPYVRROOT$/log'):
        self.exp = exp
        self.params = {}
        self.order = ['expname', 'logtype', 'logfreq', 'savepath']
        self.params['expname'] = Param(expname, valType='str', 
            hint="The name of this experiment")
        self.params['logtype'] = Param(logtype, valType='str', 
            allowedVals=['console','console-file','file'],
            hint="Whether to log to a file (file), to console (console) or to both (console-file)")
        self.params['logfreq'] = Param(int(logfreq), valType='int', 
            hint="interval time to wait between saving logs to file, in seconds.")        
        self.params['savepath'] = Param(savepath, valType='str', 
            hint="Path to save the log data ( '/' separated, may contain system enviroment variables like $EXPYVRROOT$ )") 
        
    def getType(self):
        return self.__class__.__name__
    