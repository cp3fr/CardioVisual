'''
Created on Jul 9, 2010

@author: bh
@since: Summer 2010

@license: Distributed under the terms of the GNU General Public License (GPL).
'''
# external modules
import pyglet
from pyglet import image
from pyglet.image import ImagePattern
from pyglet.gl import *
from math import pi, sin, cos, sqrt
from random import *
from time import time

#pylnco modules
from display.tools import vecf
from display import renderer

from abstract.AbstractClasses import DrawableModule

setupCallList = 0
NEAR_CLIP = 1.0

class ModuleMain(DrawableModule):
    """
    Optic flow simulation
    """
    
    defaultInitConf = {
        'name': 'opticflow'
    }
    
    defaultRunConf = {
        'movement': 'translation',
        'axis': 'Z',
        'speed': 10.0,
        'numberSlicesX': 20,
        'numberSlicesY': 20,
        'pointsBaseSize': 20,
        'randomFactorX': 0.5,
        'randomFactorY': 0.5,
        'nearClipDistance': 1.0,
        'verticalOffset': 0.0
    }
    
    confDescription = [
        ('name', 'str', "Optic flow of dots"),
        ('movement', 'str', "The type of flow simulation", ['translation','rotation']),
        ('axis', 'str', "The axis or rotation or vector of translation (OpenGL Y-up coordinates).", ['X', 'Y', 'Z', 'Random']),
        ('speed', 'float', "Speed of animation *"),
        ('verticalOffset', 'float', "Angle of vertical offset in degrees (rotate the field up or down) *"),
        ('numberSlicesX', 'int', "Number of slices of points in the main direction"),
        ('numberSlicesY', 'int', "Number of points per X slice"),
        ('randomFactorX', 'float', "Factor of randomization of points position in X."),
        ('randomFactorY', 'float', "Factor of randomization of points position in Y."),
        ('pointsBaseSize', 'int', "Base size of the points (modulated by distance)."),
        ('nearClipDistance', 'float', "Distance (from camera) for clipping particles"),
    ]
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableModule.__init__(self, controller, initConfig, runConfigs)
        
        self.starfield = {}
        
        for confName, conf in self.runConfs.items():
            if conf['movement']=='rotation':
                if (conf['axis'] == 'X'):
                    self.starfield[confName] = TorusField(13.0, 5.0, conf['numberSlicesX'], conf['randomFactorX'], conf['numberSlicesY'], conf['randomFactorY'], conf['pointsBaseSize'])
                    self.starfield[confName].Xaxis = True
                elif (conf['axis'] == 'Y'):
                    self.starfield[confName] = TorusField(13.0, 5.0, conf['numberSlicesX'], conf['randomFactorX'], conf['numberSlicesY'], conf['randomFactorY'], conf['pointsBaseSize'])
                    self.starfield[confName].Xaxis = False
                elif (conf['axis'] == 'Z'):
                    self.starfield[confName] = RectangleField(70.0, 40.0, conf['numberSlicesX'], conf['randomFactorX'], conf['numberSlicesY'], conf['randomFactorY'], conf['pointsBaseSize'])
                    self.starfield[confName].Zrotate = True
                else:
                    self.starfield[confName] = RandomTorusField(30.0, 14.0, conf['numberSlicesX'], conf['randomFactorX'], conf['numberSlicesY'], conf['randomFactorY'], conf['pointsBaseSize'])
            else:
                if (conf['axis'] == 'Random'):
                    self.starfield[confName] = RandomRectangleField(70.0, 40.0, conf['numberSlicesX'], conf['randomFactorX'], conf['numberSlicesY'], conf['randomFactorY'], conf['pointsBaseSize'])                          
                else:
                    self.starfield[confName] = RectangleField(70.0, 40.0, conf['numberSlicesX'], conf['randomFactorX'], conf['numberSlicesY'], conf['randomFactorY'], conf['pointsBaseSize'])                          
                    self.starfield[confName].Zrotate = False
                    if (conf['axis'] == 'X'):
                        self.starfield[confName].Xtranslate = True
                    elif (conf['axis'] == 'Y'):
                        self.starfield[confName].Ytranslate = True
            
    def draw(self, window_width, window_height, eye=-1):
        DrawableModule.draw(self, window_width, window_height, eye)
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        self.setup()
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
#        glLoadIdentity()
        glRotatef(self.verticalOffset, 1, 0, 0)
        self.starfield[self.activeConfName].draw()
        glPopMatrix()
        
        glPopAttrib()
        
    def start(self, dt=0, duration=-1, configName=None):
        global NEAR_CLIP
        """
        Activate the optic flow engine with the parameters passed in the conf
        """
        DrawableModule.start(self, dt, duration, configName)
            
        NEAR_CLIP = self.activeConf['nearClipDistance']      
        self.speed = self.activeConf['speed']
        self.verticalOffset = self.activeConf['verticalOffset']

        # start updating at a regular interval
        pyglet.clock.schedule_interval(self.update, 0.02)
        
    def stop(self, dt=0):
        DrawableModule.stop(self, dt)
        pyglet.clock.unschedule(self.update)

    def setup(self):
        global setupCallList
        
        if setupCallList == 0:
            # creation of glow texture for point sprites
            pattern = SmoothpointImagePattern()
            self.star = pattern.create_image(32, 32)
            spritetexture = self.star.get_texture()
            glTexParameteri( GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER, GL_LINEAR )
            glTexParameteri( GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER, GL_LINEAR )
            # creation of the call list for generic initialisation
            setupCallList = glGenLists(1)
            glNewList(setupCallList, GL_COMPILE)
            glDisable(GL_CULL_FACE)
            glDisable(GL_LIGHTING)
            glShadeModel(GL_FLAT);
            glEnable(GL_DEPTH_TEST)
            # configure blending
            glEnable( GL_BLEND )
            glBlendEquation(GL_FUNC_ADD)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            # this part configures point sprites
            glEnable( GL_POINT_SPRITE )
            glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_FASTEST)
            glPointParameterf( GL_POINT_SIZE_MIN, 1.0)
            glPointParameterf( GL_POINT_SIZE_MAX, 100.0)
    #        glPointParameterf( GL_POINT_FADE_THRESHOLD_SIZE, 60.0)
            glPointParameterfv( GL_POINT_DISTANCE_ATTENUATION, vecf(1.0, 0.0, 0.06) )
            glTexEnvi(GL_POINT_SPRITE, GL_COORD_REPLACE, GL_TRUE)
            # this part configures the fog
            glEnable (GL_FOG)
            glFogi(GL_FOG_MODE, GL_LINEAR)
            glFogf(GL_FOG_START, 0.0)
            glFogfv(GL_FOG_COLOR, vecf(0.0, 0.0, 0.0, 1.0) )
            # bind color and texture for rendering of point sprites
            glColor3f(1.0, 1.0, 1.0)
            glEnable(spritetexture.target)
            glBindTexture(spritetexture.target, spritetexture.id)
            glEndList()
        
        glCallList(setupCallList)
        glFogf(GL_FOG_END, self.starfield[self.activeConfName].length)
            
    def update(self, dt):
        self.starfield[self.activeConfName].update(dt, self.speed)
        
class RectangleField(object):
    length = 0.0
    Zrotate = False
    Xtranslate = False
    Ytranslate = False
    displist = -1
    
    def __init__(self, length, width, slices, slices_random, inner_slices, inner_slices_random, pointSize):
        # init measurements
        self.length = float(length)
        self.width = float(width)
        u_step = self.length / float(slices - 1)
        v_step = self.width / float(inner_slices - 1)
        center = self.length / 2.0
        # reset random        
        seed(time())
        # Compile a display list
        self.displist = glGenLists(1)
        glNewList(self.displist, GL_COMPILE)
        glPointSize(pointSize)
        glBegin(GL_POINTS)
        for u in frange(-self.length, 0.0, u_step, 3): 
            for v in frange(self.width / -2.0, self.width / 2.0, v_step, 3): 
                for w in frange(self.width / -2.0, self.width / 2.0, v_step, 3):
                    x = v + normalvariate(0.0, v_step * inner_slices_random)
                    y = w + normalvariate(0.0, v_step * inner_slices_random)
                    z = u + normalvariate(0.0, u_step * slices_random * (1.0 - abs( (u + center) / center )) )  
                    glVertex3f(x, y, z)
        glEnd()
        glEndList()
        # remember some variables for later draw
        self.tz = 0.0
        self.length = self.length + u_step

    def draw(self):
        global displist
        if self.Zrotate:
            #animation of rotation on Z axis
            glRotatef(self.tz, 0, 0, 1)
            glCallList(self.displist)
        else:
            if self.Ytranslate:
                glRotatef(90., 1,0,0)
                glTranslatef(0.0, 0.0, self.length / 2)
            if self.Xtranslate:
                glRotatef(90., 0,1,0)
                glTranslatef(0.0, 0.0, self.length / 2)
            #animation of translation#    
            glTranslatef(0.0, 0.0, self.tz)
            # drawing    
            glCallList(self.displist)
            glTranslatef(0.0, 0.0, -self.length)    
            glCallList(self.displist) 

    def update(self, dt, speed):
        self.tz += dt * speed
        self.tz %= 360.0 if self.Zrotate else self.length
        
class RandomRectangleField(object):
    length = 0.0
    displist = -1
    positions = []
    directions = []
    
    def __init__(self, length, width, slices, slices_random, inner_slices, inner_slices_random, pointSize):
        # init measurements
        self.pointSize = pointSize
        self.length = float(length)
        self.width = float(width)
        u_step = self.length / float(slices - 1)
        v_step = self.width / float(inner_slices - 1)
        center = self.length / 2.0
        # reset random        
        seed(time())
        # initial position 
        for u in frange(-self.length, 0.0, u_step, 3): 
            for v in frange(self.width / -2.0, self.width / 2.0, v_step, 3): 
                for w in frange(self.width / -2.0, self.width / 2.0, v_step, 3):
                    x = v + normalvariate(0.0, v_step * inner_slices_random)
                    y = w + normalvariate(0.0, v_step * inner_slices_random)
                    z = u + normalvariate(0.0, u_step * slices_random * (1.0 - abs( (u + center) / center )) )  
                    self.positions.append([x, y, z])
                    d = [normalvariate(0.0, 1.0), normalvariate(0.0, 1.0), normalvariate(0.0, 1.0)]
                    s = d[0]*d[0] + d[1]*d[1] + d[2]*d[2]
                    d[0] /= s
                    d[1] /= s
                    d[2] /= s
                    self.directions.append( d )
        # remember some variables for later draw
        self.length = self.length + u_step
        self.width = self.width + v_step
        self.tz = 0.0

    def draw(self):
#        glTranslatef(0.0, 0.0, self.tz)
        glPointSize(self.pointSize)
        glBegin(GL_POINTS)
        for p in self.positions:
            glVertex3f(p[0], p[1], p[2])
        glEnd()

    def update(self, dt, speed):
        self.tz += dt * speed
        self.tz %= self.length
        for i in range(len(self.positions)):
            self.positions[i][0] += self.directions[i][0] * dt * speed
            self.positions[i][1] += self.directions[i][1] * dt * speed
            self.positions[i][2] += self.directions[i][2] * dt * speed
            if abs(self.positions[i][0]) > self.width:
                self.directions[i][0] = -self.directions[i][0]
            if abs(self.positions[i][1]) > self.width:
                self.directions[i][1] = -self.directions[i][1]
            if self.positions[i][2] < -self.length or self.positions[i][2] > 0:
                self.directions[i][2] = -self.directions[i][2]

class TorusField(object):
    length = 0
    displist = -1
    Xaxis = False;

    def __init__(self, radius, inner_radius, slices, slices_random, inner_slices, inner_slices_random, pointSize):
        # init measurements
        self.length = radius + inner_radius
        u_step =  pi / float(slices - 1)
        v_step =  2.0 * pi / float(inner_slices - 1)
        # reset random        
        seed(time())
        # Compile a display list
        self.displist = glGenLists(1)
        glNewList(self.displist, GL_COMPILE)
        glPointSize(pointSize)
        # half torus
        glBegin(GL_POINTS)
        for u in frange(0.0, pi, u_step, 1): 
            cos_u = cos(u)
            sin_u = sin(u)
            for v in frange(0.0, 2.0 * pi, v_step, 1): 
                cos_v = cos(v)
                sin_v = sin(v)
                d = radius + inner_radius * cos_v
                x = d * (cos_u + normalvariate(0.0, inner_slices_random / 10.0))
                y = d * (sin_u + normalvariate(0.0, inner_slices_random / 10.0))
                z = inner_radius * ( sin_v  + normalvariate(0.0, slices_random / 2.0) )
                glVertex3f(x, y, z)
        glEnd()
        glEndList()
        # Basic vars init
        self.rz = 0.0
        self.length = self.length * 2.0

    def draw(self):
        if self.Xaxis:
            glRotatef(90.0, 0, 1, 0)  #align for vertical X rotation
        else:
            glRotatef(90.0, 1, 0, 0)  #align for horizontal Y rotation
        #drawing of torus starfield in 4 parts
        glRotatef(self.rz, 0, 0, 1)
        glCallList(self.displist)
        glRotatef(90.0, 0, 0, 1)
        glCallList(self.displist)
        glRotatef(90.0, 0, 0, 1)
        glCallList(self.displist)
        glRotatef(90.0, 0, 0, 1)
        glCallList(self.displist)
        
    def update(self, dt, speed):
        self.rz += dt * speed
        self.rz %= 360.0

class RandomTorusField(object):
    length = 0
    displist = -1
    positions = []
    directions = []

    def __init__(self, radius, inner_radius, slices, slices_random, inner_slices, inner_slices_random, pointSize):
        # init measurements
        self.pointSize = pointSize
        self.length = radius + inner_radius
        u_step =  pi / float(slices - 1)
        v_step =  2.0 * pi / float(inner_slices - 1)
        # reset random        
        seed(time())
        # half torus
        for u in frange(0.0, pi, u_step, 1): 
            cos_u = cos(u)
            sin_u = sin(u)
            for v in frange(0.0, 2.0 * pi, v_step, 1): 
                cos_v = cos(v)
                sin_v = sin(v)
                d = radius + inner_radius * cos_v
                x = d * (cos_u + normalvariate(0.0, inner_slices_random))
                y = d * (sin_u + normalvariate(0.0, inner_slices_random))
                z = inner_radius * ( sin_v  + normalvariate(0.0, slices_random) )
                self.positions.append([x, y, z])

        # Basic vars init
        self.rz = 0.0
        self.length = self.length * 1.2

    def draw(self):
        glPointSize(self.pointSize)
        glBegin(GL_POINTS)
        for p in self.positions:
            glVertex3f(p[0], p[1], p[2])
        glEnd()
        
    def update(self, dt, speed):
        self.rz += dt * speed
        self.rz %= 360.0


def frange(*args):
    """frange([start, ] end [, step [, mode]]) -> generator

    A float range generator. If not specified, the default start is 0.0
    and the default step is 1.0.

    Optional argument mode sets whether frange outputs an open or closed
    interval. mode must be an int. Bit zero of mode controls whether start is
    included (on) or excluded (off); bit one does the same for end. Hence:

        0 -> open interval (start and end both excluded)
        1 -> half-open (start included, end excluded)
        2 -> half open (start excluded, end included)
        3 -> closed (start and end both included)

    By default, mode=1 and only start is included in the output.
    """
    mode = 1  # Default mode is half-open.
    n = len(args)
    if n == 1:
        args = (0.0, args[0], 1.0)
    elif n == 2:
        args = args + (1.0,)
    elif n == 4:
        mode = args[3]
        args = args[0:3]
    elif n != 3:
        raise TypeError('frange expects 1-4 arguments, got %d' % n)
    assert len(args) == 3
    try:
        start, end, step = [a + 0.0 for a in args]
    except TypeError:
        raise TypeError('arguments must be numbers')
    if step == 0.0:
        raise ValueError('step must not be zero')
    if not isinstance(mode, int):
        raise TypeError('mode must be an int')
    if mode & 1:
        i, x = 0, start
    else:
        i, x = 1, start+step
    if step > 0:
        if mode & 2:
            from operator import le as comp
        else:
            from operator import lt as comp
    else:
        if mode & 2:
            from operator import ge as comp
        else:
            from operator import gt as comp
    while comp(x, end):
        yield x
        i += 1
        x = start + i*step
        
        
class SmoothpointImagePattern(ImagePattern):
    '''Create an image with a smooth point at the center.
    '''

    def __init__(self, color=(250,250,250,255)):
        '''Initialise with the given colors.

        :Parameters:
            `color1` : (int, int, int, int)
                4-tuple of ints in range [0,255] giving RGBA components of
                color to fill with.

        '''
        self.color = color

    def create_image(self, width, height):
        cw = float(width) / 2.0
        ch = float(height) / 2.0
        data = ''
        for i in range(width):
            for j in range(height):
                dist =  sqrt( (cw - float(i))*(cw - float(i)) + (ch - float(j))*(ch - float(j)) ) / float( min(cw, ch) )
                dist = 1.0 if dist > 1.0 else dist
                color = '%c%c%c%c' % (self.color[0], self.color[1], self.color[2], int( (1.0 - dist) * 255) )
                data = data + color
        return image.ImageData(width, height, 'RGBA', data)
