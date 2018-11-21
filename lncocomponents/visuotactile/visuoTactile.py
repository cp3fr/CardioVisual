"""
@author: Tobias Leugger
@since: Spring 2010
"""

from pyglet.gl import *
import random

from scene.scene import SceneElement
from abstract.AbstractClasses import DrawableModule

class VisualMotor(SceneElement):
    """
    A visual representation of a motor in the virtual scene
    """
    def __init__(self, mg, name):
        SceneElement.__init__(self)
        self.mg = mg
        self.name = name
        self._vibrating = False
        self._nextVibrationStep = 0.01
    
    def draw(self):
        if self._vibrating:
            glColor3f(0., 0., 1.)
        else:
            glColor3f(1., 1., 1.)
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        sphere = gluNewQuadric()
        gluSphere(sphere, 0.05, 32, 32) # TODO: (normal) put this constant somewhere else
        glPopMatrix()
        
    def vibrate(self, duration):
        if not self._vibrating:
            pyglet.clock.schedule_interval(self._updateVibrate, 0.05) # TODO: (normal) put this constant somewhere else
            pyglet.clock.schedule_once(self.stop, duration)
            self.mg.log({'action':'start', 'duration':str(duration)}, self.name)
        self._vibrating = True
            
    def stop(self, dt = 0):
        if self._vibrating:
            self._vibrating = False
            pyglet.clock.unschedule(self._updateVibrate)
            self.mg.log({'action':'stop'}, self.name)
        
    def _updateVibrate(self, dt):
        self.y += self._nextVibrationStep
        self._nextVibrationStep = 0.01 if self._nextVibrationStep != 0.01 else -0.01



class TactileMotor(SceneElement):
    """
    A tactile motor in the real world
    """
    def __init__(self, mg, name):
        SceneElement.__init__(self)
        self.mg = mg
        self.name = name
        self._vibrating = False
    
    def draw(self):
        if self._vibrating:
            glColor3f(1., 0., 0.)
        else:
            glColor3f(1., 1., 1.)
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        sphere = gluNewQuadric()
        gluSphere(sphere, 0.05, 32, 32) # TODO: (normal) put this constant somewhere else
        glPopMatrix()
        
    def vibrate(self, duration):
        if not self._vibrating:
            pyglet.clock.schedule_once(self.stop, duration)
            self.mg.log({'action':'start', 'duration':str(duration)}, self.name)
        self._vibrating = True
            
    def stop(self, dt = 0):
        if self._vibrating:
            self._vibrating = False
            self.mg.log({'action':'stop'}, self.name)



class Motor():
    """
    Represents a pair of visual and tactile motor
    """
    _motorNumber = 0
    
    def __init__(self, mg, visualMotor, tactileMotor, name):
        self.mg = mg
        Motor._motorNumber += 1
        self._tacticleVibrating = False
        self._visualVibrating = False
        
        self.visualMotor = visualMotor(self.mg, name = name + " visual " + str(Motor._motorNumber))
        self.tactileMotor = tactileMotor(self.mg, name = name + " tactile " + str(Motor._motorNumber))
        self.tactileMotor.y = -0.2
    
    def draw(self):
        self.visualMotor.draw()
        self.tactileMotor.draw()
        
    def activate(self, activateVisual, activateTactile, vibrationDuration, delayVt):
        vibrationDuration = determineTimeFromInterval(vibrationDuration)
        
        if activateVisual == False:
            self._activateTactile(duration = vibrationDuration)
            return
        if activateTactile == False:
            self._activateVisual(duration = vibrationDuration)
            return
            
        delayVt = determineTimeFromInterval(delayVt)
        if delayVt == 0.:
            self._activateVisual(duration = vibrationDuration)
            self._activateTactile(duration = vibrationDuration)
        elif delayVt > 0.:
            self._activateVisual(duration = vibrationDuration)
            pyglet.clock.schedule_once(self._activateTactile, delayVt, vibrationDuration)
        else:
            self._activateTactile(duration = vibrationDuration)
            pyglet.clock.schedule_once(self._activateVisual, -delayVt, vibrationDuration)
        
    def stop(self):
        self.visualMotor.stop()
        self.tactileMotor.stop()
        
    def _activateVisual(self, dt=0, duration=0.):
        #print "Motor: activate visual"
        self.visualMotor.vibrate(duration)
    
    def _activateTactile(self, dt=0, duration=0.):
        #print "Motor: activate tactile"
        self.tactileMotor.vibrate(duration)



class ModuleMain(SceneElement, DrawableModule):
    """
    A group of Motor objects arranged in a line 
    """
    defaultInitConf = {
        'name': 'visuotactile',             # any string  
        'numMotors': 4,                     # an integer bigger than 0
        'distanceBetweenMotors': 0.25       # any float
    }
    
    defaultRunConf = {    
        'vibrationType': 'stroke',          # 'stroke', 'random'
        'strokeDirection': 1,               # 1, -1 (only for stroke)
        'vtSync': True,                     # bool
        'delayVt': '(0.0, 0.0)',            # (float, float) (also negative)
        'vibrationDuration': '(0.2, 0.2)',  # (float, float) (positive)
        'activateVisual': True,             # bool
        'activateTactile': True             # bool
    }
    
    confDescription = [
        ('name', 'str', "Name of this component"),
        ('numMotors', 'int', "Number of motors"),
        ('distanceBetweenMotors', 'float', "Distance between the motors"),  
        ('vibrationType', 'str', "The type of vibration", ['stroke', 'random']),
        ('strokeDirection', 'int', "Whether to start the stroke with the first or last motor"), 
        ('vtSync', 'bool', "Whether to always activate the visual and corresponding tactile motor at the same time"),
        ('delayVt', 'str', "Interval in seconds to randomly choose the delay between the activation of the visual and the corresponding tactile motor. Can be negative."),
        ('vibrationDuration', 'str', "Interval in seconds to randomly choose the duration of a motor activation"), 
        ('activateVisual', 'bool', "Whether to activate the visual motor"),
        ('activateTactile', 'bool', "Whether to activate the tactile motor"),
    ]
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        SceneElement.__init__(self)
        DrawableModule.__init__(self, controller, initConfig, runConfigs)
        
        self._vibrations = []
        self.motors = []
        if self.initConf['numMotors'] < 1:
            raise ValueError, "MotorGroup must have at least 1 Motor"
        for index in range(self.initConf['numMotors']):
            self.motors.append(Motor(self, VisualMotor, TactileMotor, self.initConf['name']))
            self.motors[index].visualMotor.x = self.initConf['distanceBetweenMotors'] * index
            self.motors[index].tactileMotor.x = self.initConf['distanceBetweenMotors'] * index
            
    def draw(self, window_width, window_height, eye=-1):
        DrawableModule.draw(self, window_width, window_height, eye)
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        for motor in self.motors:
            motor.draw()
        glPopMatrix()
        
    def start(self, dt=0, duration=-1, configName=None):
        """
        Activate motors with the parameters passed in the conf
        """
        DrawableModule.start(self, dt, duration, configName)
        self._vibrate()
        
    def stop(self, dt=0):
        DrawableModule.stop(self, dt)
 
        # unschedule any further vibrations
        pyglet.clock.unschedule(self._vibrate)
        
        # stop all current vibrations
        for vib in self._vibrations:
            vib.stopVibration()
        self._vibrations = []
        
        # tell all motors to stop
        for motor in self.motors:
            motor.stop()
            
    def log(self, logData, motorName=None):
        """
        Appends the name passed motor name to the logData
        """
        if motorName:
            logData['motorName'] = motorName
        DrawableModule.log(self, logData)
            
    def _vibrate(self, dt=0):
        if self.activeConf['vibrationType'] == 'stroke':
            self._stroke()
        else:
            self._random()
            
    def _stroke(self):
        """
        Simulate a stroking motion if no other vibration active
        in positive or negative direction, with visual-tactile synchrony or asynchrony
        """
        if len(self._vibrations) == 0:
            # Start a new stroke only if no other vibration is active
            if self.activeConf['vtSync']:
                stroke = StrokeVibration(self, self.activeConf['strokeDirection'], True, True, self.activeConf['vibrationDuration'], self.activeConf['delayVt'])
                self._vibrations.append(stroke)
                stroke.startVibration()
            else:
                strokeVisual = StrokeVibration(self, self.activeConf['strokeDirection'], True, False, self.activeConf['vibrationDuration'], (0., 0.))
                strokeTactile = StrokeVibration(self, -self.activeConf['strokeDirection'], False, True, self.activeConf['vibrationDuration'], (0., 0.))
                self._addAndStartAsyncVibs(strokeVisual, strokeTactile, self.activeConf['delayVt'])
                    
    def _random(self):
        """
        Randomly activate motors if no other vibrations active
        """
        if len(self._vibrations) == 0:
            # Start a new random pattern only if no other vibration is active
            if self.activeConf['vtSync']:
                rand = RandomVibration(self, True, True, self.activeConf['vibrationDuration'], self.activeConf['delayVt'])
                self._vibrations.append(rand)
                rand.startVibration()
            else:
                randVisual = RandomVibration(self, True, False, self.activeConf['vibrationDuration'], (0., 0.))
                randTactile = RandomVibration(self, False, True, self.activeConf['vibrationDuration'], (0., 0.))
                self._addAndStartAsyncVibs(randVisual, randTactile, self.activeConf['delayVt'])
    
    def removeVibration(self, vibration):
        """
        Removes a vibrations from the list of vibrations
        """
        self._vibrations.remove(vibration)
        if len(self._vibrations) == 0:
            # continue vibrating if all vibrations are finished
            pyglet.clock.schedule_once(self._vibrate, 1) # TODO: (normal) put this constant somewhere else
            pass
                    
    def _addAndStartAsyncVibs(self, vibVisual, vibTactile, delayVt):
        """
        Adds the asynchronous visual and tactile vibration to the list of vibrations
        and schedules them according to the delay
        """
        self._vibrations.append(vibVisual)
        self._vibrations.append(vibTactile)
        delayVt = determineTimeFromInterval(delayVt)
        if delayVt == 0.:
            vibVisual.startVibration()
            vibTactile.startVibration()
        elif delayVt > 0.:
            vibVisual.startVibration()
            #print vibTactile
            #print "added vibTactile"
            pyglet.clock.schedule_once(vibTactile.startVibration, delayVt)
        else:
            #print vibVisual
            #print "added vibVisual"
            pyglet.clock.schedule_once(vibVisual.startVibration, -delayVt)
            vibTactile.startVibration()



class Vibration():
    def __init__(self, motorGroup, activateVisual, activateTactile, vibrationDuration, delayVt):
        self._numMotorsVibrated = 0
        self._motorGroup = motorGroup
        self._activateVisual = activateVisual
        self._activateTactile = activateTactile
        self._vibrationDuration = vibrationDuration
        self._delayVt = delayVt
        
    def startVibration(self, dt=0):
        self._motorGroup.motors[self._activeMotor].activate(activateVisual = self._activateVisual, activateTactile = self._activateTactile, vibrationDuration = self._vibrationDuration, delayVt = self._delayVt)
        self._numMotorsVibrated = 0
        pyglet.clock.schedule_interval(self._updateVibration, 0.25) # TODO: (normal) put this constant somewhere else
        
    def stopVibration(self):
        pyglet.clock.unschedule(self._updateVibration)
        
    def _updateVibration(self, dt):
        self._numMotorsVibrated += 1
        if self._numMotorsVibrated < len(self._motorGroup.motors):
            self._activeMotor = self._nextMotor()
            self._motorGroup.motors[self._activeMotor].activate(activateVisual = self._activateVisual, activateTactile = self._activateTactile, vibrationDuration = self._vibrationDuration, delayVt = self._delayVt)
        else:
            pyglet.clock.unschedule(self._updateVibration)
            self._motorGroup.removeVibration(self)



class StrokeVibration(Vibration):
    def __init__(self, motorGroup, direction, activateVisual, activateTactile, vibrationDuration, delayVt):
        Vibration.__init__(self, motorGroup, activateVisual, activateTactile, vibrationDuration, delayVt)
        if direction >= 0:
            self._activeMotor = 0
            self._strokeDirection = 1
        else:
            self._activeMotor = -1
            self._strokeDirection = -1
        
    def _nextMotor(self):
        return self._activeMotor + self._strokeDirection



class RandomVibration(Vibration):
    def __init__(self, motorGroup, activateVisual, activateTactile, vibrationDuration, delayVt):
        Vibration.__init__(self, motorGroup, activateVisual, activateTactile, vibrationDuration, delayVt)
        self._activeMotor = random.randrange(len(self._motorGroup.motors))
        
    def _nextMotor(self):
        next = random.randrange(len(self._motorGroup.motors) - 1)
        if next >= self._activeMotor:
            next += 1
        return next


def determineTimeFromInterval(interval):
    """
    Takes an interval in seconds and randomly 
    returns a time in seconds in this interval
    (millisecond precision)
    """ 
    if not isinstance(interval, tuple):
        interval = eval(interval)
    if interval[0] == interval[1]:
        return interval[0]
    # Convert to milliseconds, then back to seconds
    return float(random.randint(int(interval[0])*1000, int(interval[1])*1000))/1000


    