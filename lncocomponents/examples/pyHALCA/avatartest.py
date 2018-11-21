'''
Created on Aug 26, 2010

@author: nathan
'''
from pyglet.gl import *
from pyglet.window import key
from pyglet.window import mouse

import random, time
from array import array

from display.renderer import Camera

#from avatar import mainavatar
from avatar import avatarlib


try:
    # Try and create a window with multisampling (antialiasing)
    config = Config(sample_buffers=1, samples=4, 
                    depth_size=16, double_buffer=True)
    window = pyglet.window.Window(resizable=True, config=config)
except pyglet.window.NoSuchConfigException:
    # Fall back to no multisampling for old hardware
    window = pyglet.window.Window(resizable=True)



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
    global cam
    if symbol == key.ESCAPE:
        window.close()
    if symbol == key.SPACE:
        cam.rx = cam.ry = cam.rz = 0
        cam.x = cam.y = cam.z = 0
    elif symbol == key.F:
        window.set_fullscreen(not window.fullscreen)
        
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
    cam.z += scroll_y / 3.0
    

@window.event
def on_draw():
    global cam
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    cam.apply()
    glEnable(GL_DEPTH_TEST)
    glDisable(GL_CULL_FACE)
    drawAvatar()

  
def drawAvatar(dt=None):
    global lib, newAvatar,apos
    glPushMatrix() 
    glRotatef(180.0,0,1,0)
    glRotatef(-90.0,1,0,0)
    lib.Draw(newAvatar)
    lib.Idle(None)
    lib.setTranslation(newAvatar,0,byref(apos))
    glPopMatrix()



    
def stop(dt=None):
    global lib
    lib.Shutdown()




    
cam = Camera(Q=[0.5, 0.0, 2.0])


def initAva():
    global lib, newAvatar, apos
    
    activeConf = {
        'dataDir': 'C:\\',    #data directory for avatars (HALCA init)
        'name': 'AMan0004',                         # any string (only during init)
        'avatarConfig': 'AMan0004.cfg',             # file name of avatar config to load
        'defaultPos': [0,0,0] }
        
    print "Loading Library"
    lib = avatarlib.Avatars(activeConf['dataDir']).lib
    
    #add avatar
    print "Adding character"
    print activeConf['name']
    print activeConf['avatarConfig']
    
    newAvatar = lib.addCharacter(activeConf['name'],activeConf['avatarConfig']) 
    
    print "Idle"
    lib.Idle(None)
    
    print "Moving Avatar"
    pos = activeConf['defaultPos']
    floatType = (c_float * len(pos))
    apos = floatType(*pos)
    #print byref(apos)
    lib.setTranslation(newAvatar,0,byref(apos))

    #pt = POINTER(c_float)
    #cast(apos, POINTER(c_float))
    #apos(pos[0],pos[1],pos[2])
    #pt(apos)

initAva()
#drawAvatar()
#pyglet.clock.schedule_interval(drawAvatar, 0.02)

pyglet.app.run()






