'''
Center Reach Out Task Module

Created on Feb 21, 2011

@author: Nathan 
@since: Winter 2011

@license: Distributed under the terms of the GNU General Public License (GPL).
'''
# external modules
import pyglet
from pyglet.gl import *
import platform
import numpy as np
from pyglet.clock import _default_time_function as time


from abstract.AbstractClasses import DrawableModule


class ModuleMain(DrawableModule):
    """
    Center reach-out task
    """
    
    defaultInitConf = {
        'name': 'reachout',
        'sourceName': 'reactor',       #name of module providing sensor data
        'refSensor': 1,
        'handSensor': 2,
        'cubeCenter': [0,0,0],
        'cubeSize': 1,
        'cubeColor': [1.0, 1.0, 1.0],
        'showCube': True   
    }
    
    defaultRunConf = {
        'targetPosition': 'center', 
        'targetRadius': 0.5,
        'boundingRadius': 3,
        'targetColor': [1.0, 1.0, 1.0],
        'targetVibColor': [1.0, 0.0, 0.0]        
    }
    
    confDescription = [
        ('name', 'str', "Center Reach-Out Task"),
        ('sourceName', 'str', "Name of source module containing sensor positions"),        
        ('refSensor', 'int', "Number for reference sensor (place at hip for re-referencing)"),
        ('handSensor', 'int', "Number for hand sensor"),
        ('cubeCenter', 'str', "Center position for the cube"),
        ('cubeSize', 'int', "Length of a face of the cube (in meters)"),
        ('cubeColor', 'str', "RGB color of bounding cube"),
        ('showCube', 'bool', "Show cube or hide it?"),
        ('targetPosition', 'str', "Where reach target is located.", ['center','fLBCorner','fLTCorner',
                                                                     'fRBCorner','fRTCorner','bLBCorner',
                                                                     'bLTCorner','bRBCorner','bRTCorner',
                                                                     'random']),    
        ('targetRadius', 'float', "Radius of target sphere"),
        ('boundingRadius', 'float', "Precision of target touch. Number*targetRadius. Larger = less precision required, smaller = more"),
        ('targetColor', 'str', "RGB color of target"),
        ('targetVibColor', 'str', "RGB color of target when vibrating")        
    ]
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableModule.__init__(self, controller, initConfig, runConfigs)
                                
        #Parse init conf
        if(isinstance(self.initConf["cubeCenter"],str)):
            ccenter = eval(self.initConf["cubeCenter"])
        else:
            ccenter = self.initConf["cubeCenter"]
            
        if(isinstance(self.initConf["cubeColor"],str)):
            ccolor = eval(self.initConf["cubeColor"])
        else:
            ccolor = self.initConf["cubeColor"]
                    
        #Create cube + Target
        self.cube = Cube(ccenter,self.initConf["cubeSize"],ccolor)
        self.target = Target()
  
        if platform.system() == "Darwin" or platform.system() == "Linux":
            self.log("WARNING: Darwin or Linux detected. Vibration motor library will not work...")  

        #self.motors = Motors()

        # Attach to source
        try:
            self.source = self.controller.gModuleList[self.initConf['sourceName']]
        except:
            raise RuntimeError("Cannot find instance of source module" + self.controller.gModuleList['sourceName'] + 
                               "Check that the source component is before IK")
        
        #Arrays will be indexed from 0; numbers on mocap start at 1
        self.refSensor = self.initConf['refSensor'] - 1 
        self.handSensor = self.initConf['handSensor'] - 1

            
    def draw(self, window_width, window_height, eye=-1):
        DrawableModule.draw(self, window_width, window_height, eye)
        
        glPushMatrix()
        
        #Draw cube
        if(self.initConf["showCube"]):
            self.cube.draw()
            
        #Draw target
        self.target.draw()
    
        glPopMatrix()
        
    def start(self, dt=0, duration=-1, configName=None):
        DrawableModule.start(self, dt, duration, configName)
                
        self._setupTarget()
        
        pyglet.clock.schedule_interval(self._update, 0.02) # start updating at a regular interval
        
    def stop(self, dt=0):
        DrawableModule.stop(self, dt)
        pyglet.clock.unschedule(self._update)

    def _update(self, dt):
        # Check if target is reached
        if self._targetReached():
            self.target.setVibrating(True)
            self.target.oscillate(dt)
            self.target.setCurPos(np.add(self.target.position,self.target.offset))
        else:
            self.target.reset()


    def _setupTarget(self):
        if(isinstance(self.activeConf["targetColor"],str)):
            tcolor = eval(self.activeConf["targetColor"])
        else:
            tcolor = self.activeConf["targetColor"]

        if(isinstance(self.activeConf["targetVibColor"],str)):
            tvcolor = eval(self.activeConf["targetVibColor"])
        else:
            tvcolor = self.activeConf["targetVibColor"]

        np.random.seed()
        self.target.setup(self._getCoordsFromPos(self.activeConf["targetPosition"]),self.activeConf["targetRadius"],tcolor,tvcolor)
        self.target.reset()

    def _targetReached(self):
        #Get hand position
        curPosMatrix = self.source.getPositions()
        ref = curPosMatrix[:,self.refSensor]
        hpos = curPosMatrix[:,self.handSensor]

        curpos = np.subtract(hpos,ref)*np.array([-1,1,1])       #re-ref hand pos + swap coords for mocapsys
        #self.Qh = self.hand.position + np.array([0.0,4.0,5.0])   

        d = np.sqrt(np.sum((self.target.position-curpos)**2))
        bdist = self.activeConf['boundingRadius']*self.target.radius     #bounding box around target

        if (d <= bdist):
            return True
        else:
            return False

    def _getCoordsFromPos(self,pos):
        c = self.cube.getCenter()
        l = self.cube.getLength()
        if(pos == "center"):
            return c
        elif(pos == "fLBCorner"):
            return np.add(c,[-0.5*l,-0.5*l,0.5*l])
        elif(pos == "fLTCorner"):
            return np.add(c,[-0.5*l,0.5*l,0.5*l])
        elif(pos == "fRBCorner"):
            return np.add(c,[0.5*l,-0.5*l,0.5*l])
        elif(pos == "fRTCorner"):
            return np.add(c,[0.5*l,0.5*l,0.5*l])
        elif(pos == "bLBCorner"):
            return np.add(c,[-0.5*l,-0.5*l,-0.5*l])
        elif(pos == "bLTCorner"):
            return np.add(c,[-0.5*l,0.5*l,-0.5*l])
        elif(pos == "bRBCorner"):
            return np.add(c,[0.5*l,-0.5*l,-0.5*l])
        elif(pos == "bRTCorner"):
            return np.add(c,[0.5*l,0.5*l,-0.5*l])
        elif(pos == "random"):            
            x = c[0] + np.random.rand()*l - 0.5*l
            y = c[1] + np.random.rand()*l - 0.5*l
            z = c[2] + np.random.rand()*l - 0.5*l
            return [x,y,z]     
        

class Cube(object):

    def __init__(self, cen=[0,0,0],flen=1,col=[1.0,1.0,1.0]):
        self.center = cen
        self.fLen = flen
        self.color = col
    
    def draw(self):
        c = self.center
        
        glLineWidth(2)
        glColor3f(self.color[0],self.color[1],self.color[2])

        # Cube Coordinates
        glBegin(GL_LINES)
        
        # Front Face
        glNormal3f( 0.0, 0.0, 1.0)
        glVertex3f(c[0] + self.fLen*-0.5,c[1] + self.fLen* -0.5, c[2] + self.fLen* 0.5)     # Bottom Left Of The Texture and Quad
        glVertex3f(c[0] + self.fLen* 0.5,c[1] + self.fLen* -0.5, c[2] + self.fLen* 0.5)     # Bottom Right Of The Texture and Quad
        glVertex3f(c[0] + self.fLen* 0.5,c[1] + self.fLen*  0.5, c[2] + self.fLen* 0.5)     # Top Right Of The Texture and Quad
        glVertex3f(c[0] + self.fLen*-0.5,c[1] + self.fLen*  0.5, c[2] + self.fLen* 0.5)     # Top Left Of The Texture and Quad
        glVertex3f(c[0] + self.fLen* -0.5,c[1] + self.fLen*  -0.5,c[2] + self.fLen*  0.5)     # Top Right Of The Texture and Quad
        glVertex3f(c[0] + self.fLen*-0.5,c[1] + self.fLen*  0.5, c[2] + self.fLen* 0.5)     # Top Left Of The Texture and Quad
        # Back Face
        glNormal3f( 0.0, 0.0,-1.0)         ## Normal Facing Away
        glVertex3f(c[0] + self.fLen*-0.5,c[1] + self.fLen* -0.5,c[2] + self.fLen* -0.5)     # Bottom Right Of The Texture and Quad        
        glVertex3f(c[0] + self.fLen*-0.5,c[1] + self.fLen*  0.5,c[2] + self.fLen* -0.5)     # Top Right Of The Texture and Quad
        glVertex3f(c[0] + self.fLen* 0.5,c[1] + self.fLen*  0.5,c[2] + self.fLen* -0.5)     # Top Left Of The Texture and Quad
        glVertex3f(c[0] + self.fLen* 0.5,c[1] + self.fLen* -0.5,c[2] + self.fLen* -0.5)     # Bottom Left Of The Texture and Quad
        glVertex3f(c[0] + self.fLen* -0.5,c[1] + self.fLen*  0.5,c[2] + self.fLen* -0.5)     # Top Left Of The Texture and Quad
        glVertex3f(c[0] + self.fLen* 0.5,c[1] + self.fLen* 0.5,c[2] + self.fLen* -0.5)     # Bottom Left Of The Texture and Quad
        # Top Face
        glNormal3f( 0.0, 1.0, 0.0)         ## Normal Facing Up
        glVertex3f(c[0] + self.fLen*-0.5,c[1] + self.fLen*  0.5,c[2] + self.fLen* -0.5)     # Top Left Of The Texture and Quad
        glVertex3f(c[0] + self.fLen*-0.5,c[1] + self.fLen*  0.5,c[2] + self.fLen*  0.5)     # Bottom Left Of The Texture and Quad
        glVertex3f(c[0] + self.fLen* 0.5,c[1] + self.fLen*  0.5,c[2] + self.fLen*  0.5)     # Bottom Right Of The Texture and Quad
        glVertex3f(c[0] + self.fLen* 0.5,c[1] + self.fLen*  0.5,c[2] + self.fLen* -0.5)     # Top Right Of The Texture and Quad
        # Bottom Face
        glNormal3f( 0.0,-1.0, 0.0)         ## Normal Facing Down
        glVertex3f(c[0] + self.fLen*-0.5,c[1] + self.fLen* -0.5,c[2] + self.fLen* -0.5)     # Top Right Of The Texture and Quad
        glVertex3f(c[0] + self.fLen* 0.5,c[1] + self.fLen* -0.5,c[2] + self.fLen* -0.5)     # Top Left Of The Texture and Quad
        glVertex3f(c[0] + self.fLen* 0.5,c[1] + self.fLen* -0.5,c[2] + self.fLen*  0.5)     # Bottom Left Of The Texture and Quad
        glVertex3f(c[0] + self.fLen*-0.5,c[1] + self.fLen* -0.5,c[2] + self.fLen*  0.5)     # Bottom Right Of The Texture and Quad
        # Right face
        glNormal3f( 1.0, 0.0, 0.0)         ## Normal Facing Right
        glVertex3f(c[0] + self.fLen* 0.5,c[1] + self.fLen* -0.5,c[2] + self.fLen* -0.5)     # Bottom Right Of The Texture and Quad
        glVertex3f(c[0] + self.fLen* 0.5,c[1] + self.fLen*  0.5,c[2] + self.fLen* -0.5)     # Top Right Of The Texture and Quad
        glVertex3f(c[0] + self.fLen* 0.5,c[1] + self.fLen*  0.5,c[2] + self.fLen*  0.5)     # Top Left Of The Texture and Quad
        glVertex3f(c[0] + self.fLen* 0.5,c[1] + self.fLen* -0.5,c[2] + self.fLen*  0.5)     # Bottom Left Of The Texture and Quad
        glVertex3f(c[0] + self.fLen* 0.5,c[1] + self.fLen*  -0.5,c[2] + self.fLen*  0.5)     # Top Left Of The Texture and Quad
        glVertex3f(c[0] + self.fLen* 0.5,c[1] + self.fLen* -0.5,c[2] + self.fLen*  -0.5)     # Bottom Left Of The Texture and Quad
        # Left Face
        glNormal3f(-1.0, 0.0, 0.0)         ## Normal Facing Left
        glVertex3f(c[0] + self.fLen*-0.5,c[1] + self.fLen* -0.5,c[2] + self.fLen* -0.5)     # Bottom Left Of The Texture and Quad
        glVertex3f(c[0] + self.fLen*-0.5,c[1] + self.fLen* -0.5,c[2] + self.fLen*  0.5)     # Bottom Right Of The Texture and Quad
        glVertex3f(c[0] + self.fLen*-0.5,c[1] + self.fLen*  0.5,c[2] + self.fLen*  0.5)     # Top Right Of The Texture and Quad
        glVertex3f(c[0] + self.fLen*-0.5,c[1] + self.fLen*  0.5,c[2] + self.fLen* -0.5)     # Top Left Of The Texture and Quad
    
        glEnd()

    def getCenter(self):
        return self.center
    
    def getLength(self):
        return self.fLen

        
class Target(object):
    
    def __init__(self, rad=1, pos=[0,0,0], wire=False, col=[1.0,1.0,1.0], vcol=[1.0,0.,0.]):
        self.radius = rad
        self.position = pos
        self.wireFrame = wire
        self.color = col
        self.vcolor = vcol
        
        self.stacks = 20                #slices/stacks for rendering
        self.vibrating = False
        self.offset = [0,0,0]


    def draw(self):
        if not self.vibrating:
            glColor3f(self.color[0],self.color[1],self.color[2])
        else:
            glColor3f(self.vcolor[0],self.vcolor[1],self.vcolor[2])
 
        sphere = gluNewQuadric()
        gluQuadricNormals(sphere, GLU_SMOOTH)
    
        if self.wireFrame:
            gluQuadricDrawStyle(sphere, GLU_LINE)
        else:
            gluQuadricDrawStyle(sphere, GLU_FILL)
                  
        glTranslatef(self.position[0], self.position[1], self.position[2])
        gluSphere(sphere,self.radius,self.stacks,self.stacks)
        glTranslatef(-self.position[0], -self.position[1], -self.position[2])
        gluDeleteQuadric(sphere)
    
    def oscillate(self,dt):
        omega = 10 #Hz
        r = 0.02
        
        t = time() - dt
        x = r*np.cos(2.0*np.pi*t*omega)
        y = 0
        z = r*np.sin(2.0*np.pi*t*omega)

        self.offset = [x,y,z]
        
    def setup(self,opos,rad,col,vcol):
        self.orgpos = opos
        self.position = self.orgpos
        self.radius = rad
        self.color = col
        self.vcolor = vcol

    def reset(self):
        self.vibrating = False
        self.position = self.orgpos
        self.offset = [0,0,0]
    
    def setCurPos(self, pos):
        self.position = pos
    
    def setRadius(self,rad):
        self.radius = rad

    def setVibrating(self,bval):
        self.vibrating = bval
        
    def setColor(self,col):
        self.color = col
        
    def setVColor(self,vcol):
        self.vcolor = vcol
        
    def setWireFrame(self,wf):
        self.wireFrame = wf
        
    def isVibrating(self):
        return self.vibrating
        
        
class Motors():
    
    def __init__(self):
        self.p = windll.inpout32
        self.p.Out32(0x378, 0)

    def update(self, i):
        if i==-1:
            self.p.Out32(0x378, 0)

        if i==0:
            self.p.Out32(0x378, 16)

        if i==1:
            self.p.Out32(0x378, 32)

        if i==2:
            self.p.Out32(0x378, 64)

        if i==3:
            self.p.Out32(0x378, 128)

    def updateTransient(self,i,dt):
        def f1(dt=0):
            self.update(i)

        def f2(dt=0):
            self.update(-1)
            
        clock.schedule_once(f1,0.0)
        clock.schedule_once(f2,dt)