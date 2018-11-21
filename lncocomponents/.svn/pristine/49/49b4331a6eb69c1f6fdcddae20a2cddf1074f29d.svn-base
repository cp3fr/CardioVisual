"""
@author: Tobias Leugger
@since: Spring 2010
"""

from pyglet.gl import *
from pyglet.window import key
from pyglet.window import mouse

import random, time

from visuotactile.visuoTactile import ModuleMain
from display.renderer import Camera
from scene.setup import Setup

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
    global cam, mg, view, setup, precision
    if symbol == key.ESCAPE:
        window.close()
    if symbol == key.SPACE:
        cam.rx = cam.ry = cam.rz = 0
        cam.x = cam.y = cam.z = 0
    elif symbol == key.F:
        window.set_fullscreen(not window.fullscreen)
    elif symbol == key.LEFT:
        view.x -= precision
    elif symbol == key.RIGHT:
        view.x += precision
    elif symbol == key.UP:
        view.y += precision
    elif symbol == key.DOWN:
        view.y -= precision
    elif symbol == key.PAGEUP:
        view.z += precision
    elif symbol == key.PAGEDOWN:
        view.z -= precision
    elif symbol == key.TAB:
        view = setup.nextElement()
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
    cam.z += scroll_y / 3.0
    

@window.event
def on_draw():
    global cam, controller
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    cam.apply()
    for elem in controller.gDisplay.toDrawList:
        elem[1].draw(0, 0)
    

def vibrate(dt=None):
    global mg, nextMode
    rand = nextMode
    nextMode += 1
    nextMode %= 8
    if rand == 0:
        mg.start({'delayVt': (-0.1, -0.1)})
    elif rand == 1:
        mg.start({'strokeDirection': -1})
    elif rand == 2:
        mg.start({'vtSync': False, 'delayVt': (0.1, 0.2)})
    elif rand == 3:
        mg.start({'strokeDirection': -1, 'vtSync': False})
    elif rand == 4:
        mg.start({'vibrationType': 'random', 'delayVt': (0.08, 0.08)})
    elif rand == 5:
        mg.start({'vibrationType': 'random'})
    elif rand == 6:
        mg.start({'vibrationType': 'random', 'vtSync': False, 'delayVt': (0.3, 0.4)})
    elif rand == 7:
        mg.start({'vibrationType': 'random', 'vtSync': False})
    pyglet.clock.schedule_once(stop, 3)
        
def stop(dt=None):
    global mg
    mg.stop()

# Some classes to mimick the functions of the controller needed
class MiniLogger():
    def logMe(self, modName, logData):
        now = time.time() * 1000
        logStr = "%s, %.0f: " % (modName, now)
        logStr += str(logData)
        print(logStr)
            
class MiniDisplay():
    def __init__(self):
        self.toDrawList = []

class MiniController():
    def __init__(self):
        self.gLogger = MiniLogger()
        self.gDisplay = MiniDisplay()
    
controller = MiniController()
cam = Camera()
mg = ModuleMain(controller=controller)
setup = Setup()
setup.addElement(mg)
setup.addElement(mg.motors[0].visualMotor)
setup.addElement(mg.motors[1].visualMotor)
setup.addElement(mg.motors[2].visualMotor)
setup.addElement(mg.motors[3].visualMotor)
view = setup.currentElement()
precision = 0.1
nextMode = 0
controller.gDisplay.toDrawList.append((0, mg))
vibrate()
pyglet.clock.schedule_interval(vibrate, 5)

pyglet.app.run()
