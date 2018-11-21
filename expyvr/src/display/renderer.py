# -*- coding: utf-8 -*-
#===============================================================================
# Copyright (c) 2009-2011 EPFL (Ecole Polytechnique federale de Lausanne) 
# Laboratory of Cognitive Neuroscience (LNCO) 
# 
# ExpyVR is free software ; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation ; either version 2 of the License, or (at your option) any later version.
# 
# ExpyVR is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY ; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with ExpyVR ; if not, write to the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA.
# 
# Authors : Tobias Leugger leugger.tobias@web.de
#          Bruno Herbelin bruno.herbelin@epfl.ch
#          Nathan Evans   nathan.evans@epfl.ch
# Web site : http://lnco.epfl.ch/expyvr
#===============================================================================

"""
ExpyVR renderer and camera

@author: Danilo Jimenez Rezende
@since: Spring 2010

Updates: Bruno Herbelin & Joan Llobera -summer 2011
         Joan Llobera -autum 2011

"""
# general
import os
import numpy as np
from datetime import datetime
from math import tan
# For windows/event management
from pyglet.gl import *
from pyglet import clock, event, image
from pyglet.gl import wgl
from pyglet.window import key, mouse
from pyglet.window import Win32Window
from pyglet.clock import _default_time_function as time
# expyvr
from display.tools import rot_, rot, _rot
    
# Module globals
SCENE_NEAR = 0.01
SCENE_FAR = 1000.0
IOD = 0.001 # Meter
FOCAL_LENGHT = 0.1

class _Win32Window(Win32Window):
        
    def __init__(self, *args, **kwargs):
        super(_Win32Window, self).__init__(*args, **kwargs)
        self._fliptime = 0.0
        self._flipperiod = 0.0
        
    def flip(self):
        self.draw_mouse_cursor()
        self._flipperiod = self._fliptime
        wgl.wglSwapLayerBuffers(self._dc, wgl.WGL_SWAP_MAIN_PLANE)
        # remember timing of flip
        self._fliptime = time()
        self._flipperiod = self._fliptime - self._flipperiod
        
    def getFlipTime(self):
        return self._fliptime 
        
    def getFlipPeriod(self):
        return self._flipperiod 
    
class Renderer(object):

    def __init__(self, **kwds):
        self._controller = None
        self.cam = None
        self.window = None    
        self.onframe = None
        self.onframehud = None
        self.fps_display = None
        self.info_label = None
        self.fov = 45.0
        self.nearZ = 0.3
        self.farZ = 30.0
        self.screenZ = 1.0
        self.color = (0.0,0.0,0.0)
        self.screenid = 1
        self.size = (800, 600)
        self.visible = False
        self.flipScreen = False
        self.mirror = False
        self.fullscreen = False
        self.hidecursor = False
        self.show_info = False
        self.wireframe = False
        self.mousecameracontrol = False
        self.name = ""
        self.description = ""
        
        # fps display is a used to compute fps, but also is scheduled often for enforce refresh of display
        self.fps_display = clock.ClockDisplay(pyglet.font.load('Consolas', 14, bold=True, italic=False))
        self.fps_display.unschedule()
        
        if kwds.has_key('name'):
            self.name = kwds['name']
        if kwds.has_key('fov'):
            self.fov = kwds['fov']
        if kwds.has_key('flipScreen'):
            self.flipScreen = kwds['flipScreen']
        if kwds.has_key('mirror_3D'):
            self.mirror = kwds['mirror_3D']
        if kwds.has_key('fullscreen'):
            self.fullscreen = kwds['fullscreen']
        if kwds.has_key('hidecursor'):
            self.hidecursor = kwds['hidecursor']
        if kwds.has_key('mousecameracontrol'):
            self.mousecameracontrol = kwds['mousecameracontrol']
        if kwds.has_key('screenid'):
            self.screenid = kwds['screenid']
        if kwds.has_key('color'):
            self.color = kwds['color']
        if kwds.has_key('size'):
            self.size = kwds['size']
            
    def on_resize(self, width, height):
        glClearColor(self.color[0], self.color[1], self.color[2], 1.0)
        return event.EVENT_HANDLED

    def on_key_press(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            self.window.close()
        elif symbol == key.F5:
            self.cam.invertEyes = not self.cam.invertEyes 
        elif symbol == key.F1:
            self.show_info = not self.show_info
        elif symbol == key.F2:
            self.wireframe = not self.wireframe
            if self.wireframe:
                glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            else:
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        elif symbol == key.F4:
            now = datetime.today()
            image.get_buffer_manager().get_color_buffer().save(os.path.join(self._controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.name +'.png'))
        elif symbol == key.F3:
            fs = not self.window.fullscreen
            self.window.set_fullscreen(fs, self.screen)
        elif self._controller is not None:
            self._controller.gKeyboardListener.distributeKeyPress(symbol)
    
    def on_key_release(self, symbol, modifiers):
        if self._controller is not None:
            self._controller.gKeyboardListener.distributeKeyRelease(symbol)
            
    def on_mouse_press(self, x, y, button, modifiers):
        if self._controller is not None:
            if self.flipScreen:
                self._controller.gMouseListener.distributeButtonPress(self.window.width-x, self.window.height-y, button)
            else:
                self._controller.gMouseListener.distributeButtonPress(x, y, button)
            
    def on_mouse_release(self, x, y, button, modifiers):
        if self._controller is not None:
            if self.flipScreen:
                self._controller.gMouseListener.distributeButtonRelease(self.window.width-x, self.window.height-y, button)
            else:
                self._controller.gMouseListener.distributeButtonRelease(x, y, button)
        
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):    
        if self._controller is not None:
            if self.flipScreen:
                if self._controller.gMouseListener.distributeMotion(self.window.width-x, self.window.height-y, -dx, -dy, buttons):
                    return
            else:
                if self._controller.gMouseListener.distributeMotion(x, y, dx, dy, buttons):
                    return
            
        self.cam.update()
        
        if self.mousecameracontrol:
            # take into account mirror
            if self.mirror:
                dx = -dx
            # Camera XY rotation 
            if buttons & mouse.LEFT:
                self.cam.R = np.dot(rot(-0.5*dx*np.pi/360.0, self.cam.up), self.cam.R)
                self.cam.R = np.dot(rot(+0.5*dy*np.pi/360.0, self.cam.horiz), self.cam.R)
            # Camera XY translation
            elif buttons & mouse.RIGHT:
                self.cam.Q += ( (self.cam.horiz * dx) + (self.cam.up * dy) ) / 30.0
            # Camera Z translation and rotation
            elif buttons & mouse.MIDDLE:
                self.cam.R = np.dot(rot(+0.5*dx*np.pi/360.0, self.cam.forward), self.cam.R)
                self.cam.Q += self.cam.forward * ( dy / 30.0 )
        
    def on_mouse_motion(self, x, y, dx, dy):
        if self._controller is not None:
            self._controller.gMouseListener.distributeMotion(x, y, dx, dy, 0)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):      
        if self.mousecameracontrol: 
            #        self.cam.Q += self.cam.forward * (scroll_y / 10.0 )
            self.cam.set_aperture( self.cam.aperture + float(scroll_y) )

    def on_draw(self):
        if self.visible:
            # render the 3D scene
            self.cam.update()
            self.render()
            # render 2d HUD
            self.renderHUD()
        
    def on_show(self):          # BHBN; force update of the window to ensure update of display every frame
        clock.schedule(self.fps_display.update_text)
        self.visible = True
        
    def on_hide(self):          
        self.fps_display.unschedule()
        self.visible = False

    def on_close(self):
        self.visible = False
#            # Let display know we're not gonna be there anymore
        self._controller.gDisplay.removeRenderer(self)

    def setController(self, controller):
        self._controller = controller

    def setOnFrameMethods(self, onframemethod, onframehudmethod):
        self.onframe = onframemethod
        self.onframehud = onframehudmethod
            
    def setVisible(self, visible=True):
        if self.window is not None:
            self.window.set_visible(visible)
                    
    def close(self):
        if self.window is not None:
            self.visible = False
            self.window.close() 
        
    def getWindow(self, id = 0):
        return self.window
        
    def _log(self, logData):
        """
        Wrapper for logging inside the display
        """
        self._controller.gLogger.logMe('Renderer', self.name, logData)

    def render(self):    
        """
        The method implementing the rendering; to be defined in subclasses
        """
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def renderHUD(self):
        """
        The method implementing the rendering of HUD (no need to redifine)
        """
        # prepare rendering
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        # Blending Function For transparency Based On Source Alpha Value
        glEnable(GL_BLEND)        
        glBlendEquation(GL_FUNC_ADD)
#        glBlendFunc(GL_SRC_ALPHA, GL_DST_ALPHA)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        if self.flipScreen:
            glOrtho(self.window.width, 0, self.window.height, 0, -1, 1)
        else:
            glOrtho(0, self.window.width, 0, self.window.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        # draw all HUD modules
        self.onframehud(self.window.width, self.window.height)
        # draw info
        if self.show_info:
            self.draw_info()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glPopAttrib()
    
    def draw_info(self):
        if self.info_label is None:
            self.info_label = pyglet.text.Label(text='',
                                       color=(128, 128, 128, 255),
                                       font_name='Consolas',
                                       font_size=12,
                                       anchor_x='left', anchor_y='center',
                                       width=600, multiline=True,
                                       x=0, y=0)
        self.fps_display.draw()
        glTranslatef(10, 100, 0)
        angles = _rot(self.cam.R)
        self.info_label.text = "[F1] info -- [F2] wireframe -- [F3] fullscreen -- [F4] screenshot -- [F5] Swap eyes"
        self.info_label.text += "\n\n%s"%(self.name)
        self.info_label.text += "\nCamera position : %.2f, %.2f, %.2f"%(self.cam.Q[0], self.cam.Q[1],self.cam.Q[2])
        self.info_label.text += "\n         angles : %.2f, %.2f, %.2f"%(angles[0]*180.0/np.pi, angles[1]*180.0/np.pi, angles[2]*180.0/np.pi)
        if isinstance(self.cam, StereoCamera):
            self.info_label.text += "\n  field of view : %.2f, focal : %.3f, iod : %.4f"%(self.cam.aperture, self.cam.get_focal_lenght(), self.cam.get_interoccular_distance())
        else:
            self.info_label.text += "\n  field of view : %.2f"%(self.cam.aperture)
        self.info_label.draw() 

class Camera(object):
        
    def __init__(self, mirror = False):
        self.frustum = ( )
        self.lookAt = ( )
        self.invertEyes = False
        self.mirror = mirror
        #absolute coordinates
        self.Q=np.zeros(3)
        self.R=np.eye(3)
        self.T = np.zeros(3)
        # default values
        self.near = SCENE_NEAR
        self.set_width_height_ratio(4.0 / 3.0)
        self.set_aperture(50.0)
    
    def set_position(self, pos):
        self.Q = pos.copy()
    def set_correction(self, shift):
        self.T = shift.copy()
    def set_orientation(self, ori):
        self.R = ori.copy()
    def set_angles(self, euler):
        ori = rot_(euler*2.0*np.pi/360.0)
        self.R = ori.copy()
        
    def set_width_height_ratio(self, ratio):
        self.whRatio = ratio
        
    def set_aperture(self, a):
        self.aperture = a
        self.perpDelta = self.near * tan( self.aperture*np.pi/360.0 )

    def update(self,correctionfactor=1.0):
        self.forward = np.dot(self.R, np.array([0.,0.,-1.]))
        self.up = np.dot(self.R, np.array([0.,1.,0.]))
        self.horiz =  np.dot(self.R, np.array([1.,0.,0.]))
        self.lookAt = ( self.Q[0], self.Q[1], self.Q[2],
                        self.Q[0] + self.forward[0], self.Q[1] + self.forward[1], self.Q[2] + self.forward[2],
                        self.up[0], self.up[1], self.up[2] )
        if self.mirror:
            self.frustum =( self.whRatio * self.perpDelta*correctionfactor, -self.whRatio * self.perpDelta*correctionfactor,
                            -self.perpDelta, self.perpDelta, self.near, SCENE_FAR )
        else:
            self.frustum =( -self.whRatio * self.perpDelta*correctionfactor, self.whRatio * self.perpDelta*correctionfactor,
                            -self.perpDelta, self.perpDelta, self.near, SCENE_FAR )
        
    
# see http://paulbourke.net/miscellaneous/stereographics/stereorender/ for details
class StereoCamera(Camera):
        
    def __init__(self, mirror = False):
        Camera.__init__(self, mirror)
        
        self.frustumLeft = ( )
        self.frustumRight = ( )
        self.lookAtRight = ( )
        self.lookAtLeft = ( )
        # default
        self.set_focal_lenght(FOCAL_LENGHT)
        self.iod = self.focalLength / 20.0
        self.invertEyes = False
        
    def get_focal_lenght(self):
        return self.focalLength
        
    def set_focal_lenght(self, f):
        self.focalLength = max(f,SCENE_NEAR)
        self.near = self.focalLength / 5.0
        self.parallaxCorrection = self.near / self.focalLength;
        self.perpDelta = self.near * tan( self.aperture*np.pi/360.0 )
        
    def get_interoccular_distance(self):
        return self.iod 
    
    def set_interoccular_distance(self, iod):
        self.iod = iod

    def update(self,correctionfactor=1.0):
        # generic update
        Camera.update(self)

        #correctionfactor=1.0
        # left eye
        eyePosition = self.Q - ( self.horiz * (self.iod/2.0) )
        self.lookAtLeft = ( eyePosition[0], eyePosition[1], eyePosition[2],
                            eyePosition[0] + self.forward[0], eyePosition[1] + self.forward[1], eyePosition[2] + self.forward[2],
                            self.up[0], self.up[1], self.up[2] )
        
        self.frustumLeft =( -self.whRatio*self.perpDelta*correctionfactor + self.iod/2.0*self.parallaxCorrection,
                             self.whRatio*self.perpDelta*correctionfactor + self.iod/2.0*self.parallaxCorrection,
                             -self.perpDelta, self.perpDelta, self.near, SCENE_FAR )
        # right eye
        eyePosition = self.Q + ( self.horiz * (self.iod/2.0) )
        self.lookAtRight = ( eyePosition[0], eyePosition[1], eyePosition[2],
                             eyePosition[0] + self.forward[0], eyePosition[1] + self.forward[1], eyePosition[2] + self.forward[2],
                             self.up[0], self.up[1], self.up[2] )
        
        self.frustumRight =( -self.whRatio*self.perpDelta*correctionfactor - self.iod/2.0*self.parallaxCorrection,
                             self.whRatio*self.perpDelta*correctionfactor - self.iod/2.0*self.parallaxCorrection,
                             -self.perpDelta, self.perpDelta, self.near, SCENE_FAR )
    
