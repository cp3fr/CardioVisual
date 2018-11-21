# -*- coding: utf-8 -*-
'''
Copyright (c) 2009-2011 EPFL (Ecole Polytechnique federale de Lausanne) 
Laboratory of Cognitive Neuroscience (LNCO) 

ExpyVR is free software ; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation ; either version 2 of the License, or (at your option) any later version.

ExpyVR is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY ; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with ExpyVR ; if not, write to the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA.

Authors : Tobias Leugger leugger.tobias@web.de
          Bruno Herbelin bruno.herbelin@epfl.ch
          Nathan Evans   nathan.evans@epfl.ch
Web site : http://lnco.epfl.ch/expyvr

openglViewer.py
Created on Dec 28, 2010

@author: bruno
'''

# generic toolbox for scripts
import os, csv, re, serial, socket, threading, math
import numpy as np
from datetime import datetime
from pyglet import image, media, resource
from pyglet.gl import *
from pywidget import shape
# scripting expyvr toolbox
from pyglet.clock import _default_time_function as time
from abstract.AbstractClasses import BasicModule, DrawableModule
from controller import getPathFromString
# opengl expyvr toolbox
from display.objloader import OBJ, MTL, MORPH
from display.tools import *
from display.shader import FragmentShader, ShaderError, ShaderProgram, VertexShader

try:
    import avatar.avatarlib as avatarlib
except:
    pass

class ModuleMain(DrawableModule):
    """
    A simple module to encapsulate OpenGL rendering
    """
    defaultInitConf = {
        'name': 'opengl',
        'initCode': 'self.r=0;self.mesh = OBJ(getPathFromString("$EXPYVRROOT$/expyvr/resources/data/icosahedron.obj"))',
        'cleanupCode': '',
        'GLSLvertex': '',
        'GLSLfragment': '',
        'keyboard_movable': False
    }
    
    defaultRunConf = {
        'updateCode': 'self.r=self.r+10*dt',
        'preRenderCode': 'glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)',
        'renderCode': 'glRotatef(self.r,0,1,0);glCallList(self.mesh.gl_list)',
        'scale': 1.0,
        'x': 0.0,
        'y': 0.0,
        'z': -3.0
    }
    
    confDescription = [
        ('name', 'str', "Module executing a python script dédicated to OpenGL rendering."),
        ('initCode', 'str', "Code (or filename) to load data and initialize the module"),
        ('cleanupCode', 'str', "Code (or filename) to end module properly"),
        ('GLSLvertex', 'str', "Full path and filename of the GLSL vextex shader script"),
        ('GLSLfragment', 'str', "Full path and filename of the GLSL fragment shader script"),
        ('keyboard_movable', 'bool', "Use keyboard arrows to move the object"),
        ('updateCode', 'str', "Code (or filename) to update data (executed as is). Variable 'dt' is the update delta time."),
        ('preRenderCode', 'str', "OpenGL code (or filename) to setup the scene before render (converted to display list)"),
        ('scale', 'float', "Scale factor *"),
        ('x', 'float', "X coordinate *"),  
        ('y', 'float', "Y coordinate *"),
        ('z', 'float', "Z coordinate *"),
        ('renderCode', 'str', "Code (or filename) to render (executed as is)"),        
        ('starting', 'info', "True when the update function is called for the first time when starting a routine."),    
        ('getStartingTimes()', 'info', "Returns tupple of times when the routine was started [absTime, ExpTime, dispTime].")    
    ]

    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableModule.__init__(self, controller, initConfig, runConfigs)
        
        # execute the code of initialization
        try:
            f = open(getPathFromString(self.initConf['initCode']))
        except IOError:
            exec( self.initConf['initCode'] )
        else:
            exec( f.read() )
            f.close()
            
        # read GLSL scripts and compile them
        self.shader = None
        fshader, vshader = None, None
        try:
            filename = self.initConf['GLSLfragment'].rstrip()
            if len(filename):
                fshader = FragmentShader(open(getPathFromString(filename)))
            filename = self.initConf['GLSLvertex'].rstrip()
            if len(filename):
                vshader = VertexShader(open(getPathFromString(filename)))
                
            if fshader is not None or vshader is not None:
                self.shader = ShaderProgram(fshader, vshader)
        except:
            self.shader = None
            self.log( "Not using GLSL shader (File error)")
        else:
            try:
                if self.shader is not None:
                    self.log( "Successfully loaded GLSL shader(s).")
                    self.shader.use()
            except ShaderError, e:
                self.shader = None
                self.log ("Not using GLSL shader\nGLSL error log:\n%s"%str(e) )
                
        # ok, successful or not, we do not need the shader program now
        glUseProgram(0)
            
        self.prerenderlists = {}
        self.rendercode = {}
        self.updatecode = {}
        self.starting = False
        
        for confName, conf in self.runConfs.items():
            # Generate a display list for each pre-rendering code
            code = ''
            try:
                f = open(getPathFromString(conf['preRenderCode']))
            except IOError:
                code = conf['preRenderCode']
            else:
                code = f.read() 
                f.close()
                
            if len(code) > 0:
                self.prerenderlists[confName] = glGenLists(1)
                glNewList(self.prerenderlists[confName], GL_COMPILE)
                exec(code)
                glEndList()
            else:
                self.prerenderlists[confName] = None
            # compile the code to be executed by python interpreter at each update
            code = ''
            try:
                f = open(getPathFromString(conf['updateCode']))
            except IOError:
                code = conf['updateCode']
            else:
                code = f.read() 
                f.close()
            if len(code) > 0:
                self.updatecode[confName] = compile( code, '', 'exec' )
            else:
                self.updatecode[confName] = None
            code = ''
            try:
                f = open(getPathFromString(conf['renderCode']))
            except IOError:
                code = conf['renderCode']
            else:
                code = f.read() 
                f.close()
            if len(code) > 0:
                code += '\n'
                self.rendercode[confName] = compile( code, '<string>', 'exec' )
            else:
                self.rendercode[confName] = None
        
        # register keys for manual adjustment of position
        if (self.initConf['keyboard_movable'] ):
            self.displacement = 0.1
            self.controller.registerKeyboardAction( 'LEFT UP RIGHT DOWN PAGEUP PAGEDOWN HOME END', self.handlekey )
        
        self.x, self.y, self.z = [0,0,0]
        
    def update(self, dt):
        if self.started:
            exec( self.updatecode[self.activeConfName] )
        
    def draw(self, window_width, window_height, eye=-1):
        DrawableModule.draw(self, window_width, window_height, eye)
        
        # Turn blending on
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        if self.shader is not None:
            self.shader.use() 

        # 1. execute the PRE-RENDER display list 
        if self.prerenderlists[self.activeConfName] is not None:
            glCallList( self.prerenderlists[self.activeConfName] )
        
        # 2. Apply transformations
        glTranslatef(self.x,self.y,self.z)
        glScalef(self.scale, self.scale, self.scale)
        
        # 3. execute rendering code 
        if self.rendercode[self.activeConfName] is not None:
            exec( self.rendercode[self.activeConfName] )
        
        if self.shader is not None:
            glUseProgram(0)
        glPopAttrib()
        
    def start(self, dt=0, duration=-1, configName=None):
        """
        Activate the mesh display engine with the parameters passed in the conf
        """
        DrawableModule.start(self, dt, duration, configName)
        self.scale = self.activeConf['scale']
        self.x = self.activeConf['x']
        self.y = self.activeConf['y']
        self.z = self.activeConf['z']
        if self.updatecode[self.activeConfName] is not None:
            self.starting = True
            self.update(0)
            self.starting = False
            pyglet.clock.schedule(self.update)

    def stop(self, dt=0):
        DrawableModule.stop(self, dt)
        pyglet.clock.unschedule(self.update)

    def cleanup(self):
        DrawableModule.cleanup(self)
        # execute the code of cleanup
        if len(self.initConf['cleanupCode']) > 0 :
            try:
                f = open(getPathFromString(self.initConf['cleanupCode']))
            except IOError:
                exec( self.initConf['cleanupCode'] )
            else:
                exec( f.read() )
                f.close()
        # UNregister keys for manual adjustment of position
        if self.initConf['keyboard_movable']:
            self.controller.unregisterKeyboardAction( 'LEFT UP RIGHT DOWN PAGEUP PAGEDOWN HOME END', self.handlekey )
        
    def handlekey(self, keypressed = None):
        if keypressed == 'LEFT':
            self.x -= self.displacement
        elif keypressed == 'RIGHT':
            self.x += self.displacement
        elif keypressed == 'UP':
            self.y += self.displacement
        elif keypressed == 'DOWN':
            self.y -= self.displacement
        elif keypressed == 'PAGEUP':
            self.z += self.displacement
        elif keypressed == 'PAGEDOWN':
            self.z -= self.displacement
        elif keypressed == 'HOME':
            self.displacement *= 2.0
        elif keypressed == 'END':
            self.displacement /= 2.0
        print self.getName(), self.x, self.y, self.z
