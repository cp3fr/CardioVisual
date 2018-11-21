'''
Trajectory following module

Created on March 11, 2011

@author: Nathan 
@since: Spring 2011

@license: Distributed under the terms of the GNU General Public License (GPL).
'''
# external modules
import pyglet
from pyglet.gl import *
import platform
import numpy as np
import tracker
from pyglet.clock import _default_time_function as time

from abstract.AbstractClasses import DrawableModule


class ModuleMain(DrawableModule):
    """
    Continuous trajectory following task
    """
    
    defaultInitConf = {
        'name': 'trajectory',
        'trajRadius': 1,
        'force2D': True,
        'showSurface': True,
        'sourceName': 'IRCam',       #name of module providing sensor data
        'refSensor': 1,
        'handSensor': 2
    }
    
    defaultRunConf = {
        'trialType': 'mixed',
        'fbBias': 'none',
        'maxBias': 0,
        'biasW': 1,
        'trajVelocity': (0.5,1.0),
        'trajDirection': 'CW',
        'targetRadius': 0.5,
        'boundingRadius': 3,
        'targetColor': [1.0, 1.0, 1.0],
        'targetTouchColor': [1.0, 0.0, 0.0],
        'fbSphereRadius': 0.3,
        'fbSphereColor': [0.0, 0.0, 1.0],
        'fbSphereTouchColor': [1.0, 0.0, 0.0]
    }
    
    confDescription = [
        ('name', 'str', "Center Reach-Out Task"),
        ('force2D', 'bool', "Restrict path to XZ plane?"),
        ('trajRadius', 'float', "Radius of trajectory"),
        ('showSurface', 'bool', "Show trajectory surface or not?"),
        ('sourceName', 'str', "Name of source module containing sensor positions"),
        ('refSensor', 'int', "Number for reference sensor (for Reactor mocap)"),
        ('handSensor', 'int', "Number for hand sensor (for Reactor mocap)"),
        ('trialType', 'str', "Which type of feedback?", ['mixed','visual','proprioceptive','calibration']),
        ('fbBias', 'str', "Feedback corresponds or is perturbed?", ['none','random']),
        ('maxBias', 'float', "Maximum bias for perturbation (for random mode; in meters)"),  
        ('biasW', 'float', "Max oscillating frequency for dynamically updating bias (b = b*cos(Wt))"),                
        ('trajVelocity', 'str', "Velocity range of target on trajectory (in Hz). Set same number twice to fix velocity"),        
        ('trajDirection', 'str', "For 2D trajectories, which direction (clockwise,counter,random)?", ['CW','CCW','random']),
        ('targetRadius', 'float', "Radius of target sphere"),
        ('fbSphereRadius', 'float', "Radius of sphere representing visual feedback"),
        ('boundingRadius', 'float', "Precision of target touch. Number*targetRadius. Larger = less precision required, smaller = more"),
        ('targetColor', 'str', "RGB color of target"),
        ('targetTouchColor', 'str', "RGB color of target when in contact"),
        ('fbSphereColor', 'str', "RGB color of feedback sphere"),
        ('fbSphereTouchColor', 'str', "RGB color of feedback when in contact")
    ]
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableModule.__init__(self, controller, initConfig, runConfigs)
                                                    
        #Create trajectory + target + fb spheres
        self._trajRadius = self.initConf['trajRadius']
        self._in2D = self.initConf['force2D']
        self.trajSurface = Sphere()
        self.target = Sphere()
        self.fbSphere = Sphere()
        self.prevPropPos = 0                                    #previous timestep's proprioceptive position
  
        # Attach to source
        try:
            self.source = self.controller.gModuleList[self.initConf['sourceName']]
        except:
            raise RuntimeError("Cannot find instance of source module" + self.controller.gModuleList['sourceName'] + 
                               "Check that the source component is before the trajectory component")
        
        #Arrays will be indexed from 0; numbers on mocap start at 1
        self.refSensor = self.initConf['refSensor'] - 1 
        self.handSensor = self.initConf['handSensor'] - 1
        
        
        # Setup trigger sending (for EEG events)
        if not self.controller.gModuleList.has_key('trigManager') or not self.controller.gModuleList.has_key('triggerSend'):
            self.log("Warning: Trigger Manager or Sender not yet initialized. Triggers will not be sent.")
            self.trigSender = None
        else:
            trigManager = self.controller.gModuleList['trigManager']
            self.tCode = trigManager.getCode("inContact")              #get a free code for first interaction
            self.trigSender = self.controller.gModuleList['triggerSend']
    
            
    def draw(self, window_width, window_height, eye=-1):
        DrawableModule.draw(self, window_width, window_height, eye)
        
        glPushMatrix()
        
        # Lighting
        specular= [0.65, 0.65, 0.65, 1.0]
        mat_specular = [1.0,1.0,1.0,1.0]
        ambient = [0.25,0.25,0.25,1.0]
        lightpos = np.array([0,0,0])

        glEnable(GL_DEPTH_TEST)
        gl_specular = (GLfloat * len(specular))(*specular)
        glLightfv(GL_LIGHT0, GL_SPECULAR, gl_specular)
        gl_mat_specular = (GLfloat * len(mat_specular))(*mat_specular)
        glMaterialfv(GL_FRONT,GL_SPECULAR, gl_mat_specular)
        gl_ambient = (GLfloat * len(ambient))(*ambient)
        glLightfv(GL_LIGHT0, GL_AMBIENT,gl_ambient)

        gl_position = (GLfloat * len(lightpos))(*lightpos)
        glLightfv(GL_LIGHT0,GL_POSITION, gl_position)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        
        #Draw trajectory surface
        if(self.initConf["showSurface"]):
            self.trajSurface.draw()
            
        #Draw target
        self.target.draw()
    
        #Feedback sphere 
        if(self.activeConf["trialType"] == 'mixed') or (self.activeConf["trialType"] == 'calibration'):
            self.fbSphere.draw()
    
        glPopMatrix()
        
    def start(self, dt=0, configName=None):
        DrawableModule.start(self, dt, configName)                
        self._setupSpheres()
        pyglet.clock.schedule_interval(self._update, 0.02) # start updating at a regular interval
        
    def stop(self, dt=0):
        DrawableModule.stop(self, dt)
        pyglet.clock.unschedule(self._update)


    def _setupSpheres(self):

        #Trajectory sphere        
        self.trajSurface.setup([0,0,0],self.initConf["trajRadius"],[1.0, 1.0, 1.0],[1.0, 1.0, 1.0])
        self.trajSurface.setWireFrame(True)
        self.trajSurface.reset()                                                        

        #Target sphere
        if(isinstance(self.activeConf["targetColor"],str)):
            tcolor = eval(self.activeConf["targetColor"])
        else:
            tcolor = self.activeConf["targetColor"]

        if(isinstance(self.activeConf["targetTouchColor"],str)):
            tvcolor = eval(self.activeConf["targetTouchColor"])
        else:
            tvcolor = self.activeConf["targetTouchColor"]

        np.random.seed()
        self.target.setup(self._getStartCoordsFromRadius(self._trajRadius,self._in2D),self.activeConf["targetRadius"],tcolor,tvcolor)
        exec("velRange =" + self.activeConf["trajVelocity"])
        vel = np.random.uniform(velRange[0],velRange[1])
        self.target.setupTrajectory(self._in2D,self.activeConf["trajDirection"],vel)
        self.target.reset()
        
        #Feedback sphere
        if(isinstance(self.activeConf["fbSphereColor"],str)):
            fbcolor = eval(self.activeConf["fbSphereColor"])
        else:
            fbcolor = self.activeConf["fbSphereColor"]

        if(isinstance(self.activeConf["fbSphereTouchColor"],str)):
            fbtcolor = eval(self.activeConf["fbSphereTouchColor"])
        else:
            fbtcolor = self.activeConf["fbSphereTouchColor"]

        self.fbSphere.setup([0,0,0],self.activeConf["fbSphereRadius"],fbcolor,fbtcolor)
        self.fbSphere.reset()
        
        if(self.activeConf["fbBias"] == 'random'):
            self.fbSphere.setMaxBias(self.activeConf["maxBias"])
            self.fbSphere.setupOffset(self._in2D)


        #######
        # Log per-trial information
        self.log("trialType," + self.activeConf["trialType"])                               #trial type
        self.log("rotationVel," + str(vel))                                                 #trial rotation velocity
        self.log("rotationDir," + self.target.curDirection)                                 #trial rotation direction
                
    '''
    Given the radius of a sphere (around which trajectories travel), 
    return a random starting position
    '''
    def _getStartCoordsFromRadius(self,rad,in2D):
        
        if(in2D):
            theta = np.random.uniform(0,2*np.pi)
            x = np.cos(theta)
            y = np.sin(theta)
            z = 0
            
        else:
            # Use Marsaglia algorithm to find a random point on the sphere
            x1 = np.random.uniform(-1.0,1.0)
            x2 = np.random.uniform(-1.0,1.0)
            while ((x1**2 + x2**2) >= 1):
                x1 = np.random.uniform(-1.0,1.0)
                x2 = np.random.uniform(-1.0,1.0)
            
            x = 2*x1*np.sqrt(1-x1**2-x2**2)
            y = 2*x2*np.sqrt(1-x1**2-x2**2)
            z = 1 - 2*(x1**2 + x2**2)
        
        #rescale to trajectory radius (point on unit sphere)
        pos = np.array([x,y,z]) * rad

        return pos.tolist()


    def _update(self, dt):                
        curPosMatrix = self.source.getData()               #Get hand position        

        #Update feedback sphere
        sourceType = str(self.source.__class__)
        if sourceType == 'ReactorModule.ModuleMain':
            ref = curPosMatrix[:,self.refSensor]
            hpos = curPosMatrix[:,self.handSensor]
            curproppos = np.subtract(hpos,ref)*np.array([-1,1,1])       #re-ref hand pos + swap coords for mocapsys            

        elif sourceType == 'IRCamModule.ModuleMain':            
            curproppos = curPosMatrix[:]            
            #curproppos[1] = -curproppos[1];                         #reverse from tracker's y coordinate
        
        else:
            curproppos = np.array(self.target.position)                 #cheat - fake hand feedback to follow
        

        #Set Feedback sphere position according to bias or not
        if(self.activeConf["fbBias"] == 'none'):
            self.fbSphere.setCurPos(curproppos)
        elif(self.activeConf["fbBias"] == 'random'):
            self.fbSphere.updateOffset(self.activeConf['biasW'], dt)       #update dynamical offset 
            self.fbSphere.setCurPos(curproppos + self.fbSphere.offset)
        
        #Update target sphere
        if self._targetReached(curproppos) and not self.target.started:
            if not self.trigSender is None:
                self.trigSender.write(self.tCode)                   #send first-contact trigger code (for EEG analysis)
            
            self.target.setStarted(True)
            self.target.setContact(True)                            #note: for proprio only, ensure "touch" color is same; don't give feedback

        elif self._targetReached(curproppos):                           #already in motion
            self.target.setContact(True)
        elif self.activeConf["trialType"] == 'visual':
            self.target.setStarted(True)                            #automatically start for visual
            self.target.setContact(True)                            #give same color as if in contact (to compare to other conditions)
        else:
            self.target.setContact(False)

        if self.activeConf["trialType"] == 'calibration':
            self.target.setCurPos([0,0,0])           #update position
        elif self.target.started:
            self.target.setCurPos(self._getNewTargetPos(self.target.velocity,dt))           #update position
            
        ######
        # LOG Everything
        ######
        self.log("tarpos," + str(self.target.position))     #target position
        self.log("vispos," + str(self.fbSphere.position))   #visual position
        self.log("propos," + str(curproppos))               #proprio position (from tracking)
        self.log("tarvel," + str((np.divide(np.subtract(self.target.position,self.target.prevpos),dt))))       #target position
        self.log("visvel," + str((np.divide(np.subtract(self.fbSphere.position,self.fbSphere.prevpos),dt))))   #visual position
        self.log("provel," + str((np.divide(np.subtract(curproppos,self.prevPropPos),dt))))                    #proprio position (from tracking)
        self.log("incontact," + str(self.target.inContact))                            #whether visual is in contact
        
        #Set current positions as previous
        self.target.setPrevPos(self.target.position)
        self.fbSphere.setPrevPos(self.fbSphere.position)
        self.prevPropPos = curproppos

    def _getNewTargetPos(self,vel,dt):
        t = time() - dt
        R = self._trajRadius
        
        u = self.target.u
        n = self.target.n
        newpos = R*np.cos(2.0*np.pi*vel*t)*u + (R*np.sin(2.0*np.pi*vel*t)*np.cross(n,u))    #new position on circle projection
        
        return newpos
        
    def _targetReached(self,curpos):
#        if self.activeConf["trialType"] == 'calibration':
#            return False
        
        d = np.sqrt(np.sum((self.target.position-curpos)**2))
        bdist = self.activeConf['boundingRadius']*self.target.radius     #bounding box around target
        if (d <= bdist):
            return True
        else:
            return False


class Sphere(object):
    
    def __init__(self, rad=1, pos=[0,0,0], wire=False, col=[1.0,1.0,1.0], vcol=[1.0,0.,0.]):
        self.radius = rad
        self.orgpos = pos
        self.position = pos
        self.prevpos = pos
                        
        self.wireFrame = wire
        self.color = col
        self.vcolor = vcol
        
        self.stacks = 20                #slices/stacks for rendering
        self.started = False
        self.inContact = False
        
        #Visual bias
        self.maxBias = 0
        self.offset = [0,0,0]

        #For trajectory
        self.curDirection = ''
        self.velocity = 0
        self.u = [0,0,0]       #unit vector to start position
        self.n = [0,0,0]       #unit vector for directional bearing
        

    def draw(self):
        if not self.inContact:
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

    '''
    Setup unit vectors to define target trajectory
    '''
    def setupTrajectory(self, in2D, dir, vel):
        self.velocity = vel
        
        #Unit vector to starting position
        pt = np.array(self.orgpos)
        self.u = pt / np.linalg.norm(pt)               

        #Unit vector for direction to travel
        if(in2D):
            if(dir == 'CW'):
                rdir = [0,0,-1]
                self.curDirection = dir
            elif(dir == 'CCW'):
                rdir = [0,0,1]
                self.curDirection = dir
            elif(dir == 'random'):
                r = np.random.random()
                if(r > 0.5):
                    rdir = [0,0,-1]
                    self.curDirection = 'CW'
                else:
                    rdir = [0,0,1]
                    self.curDirection = 'CCW'
        else:
            rdir = np.random.randn(3)
            
        self.n = rdir / np.linalg.norm(rdir)
        

    def setupOffset(self, in2D):
        rdir = np.random.randn(3)
        
        if(in2D):
            rdir[2] = 0     #flatten Z 
        
        self.offset = rdir / np.linalg.norm(rdir)
        
        mag = np.random.rand()*self.maxBias
        self.offset = mag * self.offset

    '''
    Dynamically Update bias offset:  B = B_0 * cos( omega*t )
        omega = in HZ
    '''
    def updateOffset(self,omega,dt):        
        t = time() - dt
        self.offset = self.offset * np.cos(omega*t)

    def reset(self):
        self.started = False
        self.inContact = False
        self.position = self.orgpos
        self.offset = [0,0,0]
    
    def setMaxBias(self,b):
        self.maxBias = b
        
    def setCurPos(self, pos):
        self.position = pos
        
    def setPrevPos(self, pos):
        self.prevpos = pos
    
    def setRadius(self,rad):
        self.radius = rad

    def setContact(self,bval):
        self.inContact = bval
        
    def setColor(self,col):
        self.color = col
        
    def setVColor(self,vcol):
        self.vcolor = vcol

    def setStarted(self,bval):
        self.started = bval
        
    def setWireFrame(self,wf):
        self.wireFrame = wf
