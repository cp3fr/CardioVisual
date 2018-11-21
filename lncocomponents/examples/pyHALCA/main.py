"""
This is an example of a minimum setup for using HALCA with Python + Pyglet

Requirements:
Python >= 2.6   (tested with 2.6)
pyglet 1.1.4
NumPy 1.5.x     (helps with matrix manipulations - not strictly necessary)
HALCA DLL       (place in DLL search path; C:\windows\system or C:\windows\system32 is a good bet)

@author: Nathan Evans
@date: 3 April 2011
"""

from pyglet.gl import *
from pyglet.window import key
from pyglet.window import mouse

import numpy as np
import time
import halca
from halca import cvecf

##############################################

# Try and create a window with multisampling (antialiasing)
try:
    config = Config(sample_buffers=1, samples=4, 
                    depth_size=16, double_buffer=True)
    window = pyglet.window.Window(resizable=True, config=config)
except pyglet.window.NoSuchConfigException:
    window = pyglet.window.Window(resizable=True)   # No multisampling for old hardware


@window.event
def on_resize(width, height):
    # Override the default on_resize handler to create a 3D projection
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(50., width / float(height), .1, 1000.)
    glMatrixMode(GL_MODELVIEW)
    return pyglet.event.EVENT_HANDLED


@window.event
def on_key_press(symbol, modifiers):
    global cam, view, precision
    if symbol == key.ESCAPE:
        window.close()
    if symbol == key.SPACE:
        cam.rx = cam.ry = cam.rz = 0
        cam.x = cam.y = cam.z = 0
    elif symbol == key.F:
        window.set_fullscreen(not window.fullscreen)
    elif symbol == key.LEFT:
        cam.x -= precision
    elif symbol == key.RIGHT:
        cam.x += precision
    elif symbol == key.UP:
        cam.y += precision
    elif symbol == key.DOWN:
        cam.y -= precision
    elif symbol == key.PAGEUP:
        cam.z += precision
    elif symbol == key.PAGEDOWN:
        cam.z -= precision
    elif symbol == key._1:
        precision = 0.01
    elif symbol == key._2:
        precision = 0.05
    elif symbol == key._3:
        precision = 0.2
    elif symbol == key._4:
        precision = 1.
        
@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    global cam
    if buttons & mouse.LEFT:
        cam.ry += dx * 1.0
        cam.ry %= 360
        cam.rx -= dy * 1.0
        cam.rx %= 360
    elif buttons & mouse.RIGHT:
        cam.x += 5.0 * dx / float(window.width)
        cam.y += 5.0 * dy / float(window.height)

@window.event
def on_mouse_scroll(x, y, scroll_x, scroll_y):
    global cam
    cam.z -= scroll_y / 3.0    

@window.event
def on_draw():
    global cam, HALCA, avatar, aPos
    glEnable(GL_DEPTH_TEST)                                 
    glDisable(GL_CULL_FACE)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_MODELVIEW)        
    glLoadIdentity()
    cam.apply()
    
    #Draw avatar
    glPushMatrix()
    glRotatef(-90.0,1,0,0)                                  #rotate to look at camera with body upright 
    HALCA.setTranslation(avatar,0,byref(cvecf(aPos)))       #move whole body (joint=0)
    HALCA.DrawOne(avatar)
    glPopMatrix()
    
     
@window.event   
def on_close():
    global HALCA
    HALCA.ShutDown(None)

            
class Camera():    
     def __init__(self):
         self.set()

     def set(self, translation=[0.0, 0.0, 0.0], rotation=[0.0, 0.0, 0.0]):
         self.x,  self.y,  self.z  = translation
         self.rx, self.ry, self.rz = rotation
    
     def apply(self):
         glRotatef(self.rx, 1, 0, 0)
         glRotatef(self.ry, 0, 1, 0)
         glRotatef(self.rz, 0, 0, 1)
         glTranslatef(-self.x, -self.y, -self.z) 




###############
# Parameters  #
###############
precision = 0.1             #for moving camera (distance per input)
avatarDir = "C:\\"          #root data directory for avatar data (ie: directory where 'data' directory is)
aPos = [0,3,0]              #avatar position (translation)


###############
# HALCA Setup #
###############
aConfName = 'AMan0004.cfg'                 #name of avatar
avaConf = {
    'dataDir': avatarDir,
    'VA_TRANS': False,
    'DQUAT_TRANSF': False,
}

HALCA = halca.Avatars(avaConf).lib              # initialize an instance of HALCA

# Add avatar to HALCA
print 'name: ' + aConfName[:-4] + " fname: " + aConfName
avatar = HALCA.addCharacter(aConfName[:-4], aConfName)      #strip file extension - HALCA wants just name
if(avatar == -1):
    raise RuntimeError("Problem loading avatar. Check Animation / Configuration / Path, etc")    
else:
    print "---> Successfully loaded avatar: " + aConfName[:-4] + " (" + str(avatar) + ")"
    print "---> Total number of avatars loaded in HALCA: " + str(HALCA.numCharacters(None))

HALCA.Idle(None)


##########
# Run It #
##########
cam = Camera()
pyglet.app.run()