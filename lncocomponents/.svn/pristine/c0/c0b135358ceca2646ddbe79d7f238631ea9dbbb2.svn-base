#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

from math import pi, sin, cos
from random import *
from time import time

from pyglet.gl import *
import pyglet

#We have to modify PYTHONPATH to include the sources tree
#must know the OS delimiter... for window$$ & unix compatibility
ds = os.path.sep
sys.path.append(os.path.abspath(os.curdir) +ds+ '..'+ds+'..'+ds+'src')

from opticflow.opticFlow import RectangleField
from opticflow.opticFlow import TorusField


# Define a simple function to create ctypes arrays of floats:
def vec(*args):
    return (GLfloat * len(args))(*args)

try:
    # Try and create a window with stereo active
    config = Config(sample_buffers=1, samples=4,
            depth_size=16, double_buffer=True, stereo=True)
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
    gluPerspective(60., width / float(height), 10.1, 1000.)
    glMatrixMode(GL_MODELVIEW)

    return pyglet.event.EVENT_HANDLED

def update(dt):
    global starfield
    starfield.update(dt, 10)

pyglet.clock.schedule(update)
pyglet.clock.set_fps_limit(60)

@window.event
def on_draw():
    global tz, starfield
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    #animation
    starfield.draw()

def setup():
    # One-time GL setup
    glClearColor(0, 0, 0, 1)
    glColor3f(1, 0, 0)
    glEnable(GL_DEPTH_TEST)
    glDisable(GL_CULL_FACE)
    glDisable(GL_LIGHTING)
    glShadeModel(GL_FLAT);

    glEnable(GL_BLEND)
    #glEnable(GL_MULTISAMPLE)
    #glSampleCoverage(1.0, GL_FALSE)

    glEnable(GL_POINT_SMOOTH);
    glEnable(GL_SAMPLE_COVERAGE);
    glHint(GL_POINT_SMOOTH_HINT, GL_NICEST);
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_FASTEST);

    glPointSize(10)
    glPointParameterf( GL_POINT_SIZE_MIN, 0.0)
    glPointParameterf( GL_POINT_SIZE_MAX, 180.0)
    glPointParameterf( GL_POINT_FADE_THRESHOLD_SIZE, 0.01)
    glPointParameterfv( GL_POINT_DISTANCE_ATTENUATION, vec(1.0, 2.0, 0.5) )

    glEnable (GL_FOG)
    glHint(GL_FOG_HINT, GL_NICEST)
    #glFogi(GL_FOG_MODE, GL_EXP2)
    #glFogf(GL_FOG_DENSITY, 0.03)
    glFogfv(GL_FOG_COLOR, vec(0.0, 0.0, 0.0, 1.0) )
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogf(GL_FOG_START, 0.0)
    #glFogf(GL_FOG_END, 4.0 + 2.5 * 2.0)
    glFogf(GL_FOG_END, 50.0)



setup()
#starfield = TorusField(30.0, 15.0, 80, 0.0, 60, 0.0, 30)
#starfield.Xaxis = False

starfield = RectangleField(50.0, 15.0, 20, 0.1, 15, 0.51, 50)
#starfield.Zrotate = True;

pyglet.app.run()
