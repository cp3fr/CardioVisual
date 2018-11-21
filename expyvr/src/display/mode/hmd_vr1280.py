import numpy as np
from display.tools import rot_

from pyglet.gl import *
#from pyglet import clock, font
from pyglet import clock, event, image
from datetime import datetime
import os
from pyglet.window import key, mouse

from display import renderer

        
class Renderer(renderer.Renderer):
    
    def __init__(self, **kwds):
        super(Renderer,self).__init__(**kwds)
        self.description = "VR1280 HMD"
        self.cam = renderer.StereoCamera(mirror=self.mirror)
        # fixed field of view : http://vresources.org/HMD_rezanalysis.html
        self.fov = 48.0
        self.cam.set_aperture(self.fov)
        
        if kwds.has_key('focallength'):
            self.cam.set_focal_lenght( kwds['focallength'] )
        
        if kwds.has_key('eyeseparation'):
            self.cam.set_interoccular_distance(kwds['eyeseparation'])
        
        # setup gl config flags
        configgl = pyglet.gl.Config(sample_buffers=1, samples=4,
                    depth_size=16,  double_buffer = True, stereo = False)
        # test it
        screens = pyglet.window.get_platform().get_default_display().get_screens()
        if not screens[0].get_matching_configs(configgl):
            # probably not happy with sample buffers
            configgl.sample_buffers = 0
            configgl.samples = 0
            
        # fixed size 
        self.size = (2560,1024)
        self.window = renderer._Win32Window(self.size[0],self.size[1],resizable=False, vsync=True, 
                                            visible=False, config=configgl, style=pyglet.window.Window.WINDOW_STYLE_BORDERLESS)
        
        self.window.set_mouse_visible(not self.hidecursor)         
        
        @self.window.event
        def on_resize(width, height):
            self.cam.set_width_height_ratio( float(width / 2) / float(height))
            return self.on_resize(width, height)

        @self.window.event
        def on_key_release(symbol, modifiers):
            self.on_key_release(symbol, modifiers)
            
        @self.window.event
        def on_mouse_press(x, y, button, modifiers):
            self.on_mouse_press(x, y, button, modifiers)
        
        @self.window.event
        def on_mouse_release(x, y, button, modifiers):
            self.on_mouse_release(x, y, button, modifiers)
            
        @self.window.event
        def on_mouse_drag(x, y, dx, dy, buttons, modifiers):    
            self.on_mouse_drag(x, y, dx, dy, buttons, modifiers)
    
        @self.window.event
        def on_mouse_motion(x, y, dx, dy):    
            self.on_mouse_motion(x, y, dx, dy)
            
        @self.window.event
        def on_mouse_scroll(x, y, scroll_x, scroll_y):        
            self.cam.iod += scroll_y * self.cam.focalLength / 200
            self.cam.update()

        @self.window.event
        def on_draw():
            self.on_draw()
            
        @self.window.event
        def on_show():
            self.on_show()
            
        @self.window.event
        def on_hide():          
            self.on_hide()

        @self.window.event
        def on_close():
            self.on_close()
            
        @self.window.event
        def on_key_press(symbol, modifiers):
            if symbol == key.ESCAPE:
                self.window.close()
            elif symbol == key.E:
                self.cam.invertEyes = not self.cam.invertEyes 
            elif symbol == key.I:
                self.show_info = not self.show_info
            elif symbol == key.W:
                self.wireframe = not self.wireframe
                if self.wireframe:
                    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
                else:
                    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            elif symbol == key.S:
                now = datetime.today()
                #this will only get 1 eye!!
                image.get_buffer_manager().get_color_buffer().save(os.path.join(self._controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.name +'.png'))
            elif self._controller is not None:
                self._controller.gKeyboardListener.distributeKeyPress(symbol)
        

    """
    The method implementing the rendering 
    """
    def render(self):
        renderer.Renderer.render(self)
   
        # LEFT
        glViewport( 0, 0, self.window.width/2, self.window.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        f = self.cam.frustumLeft
        glFrustum( f[0], f[1], f[2], f[3], f[4], f[5] )
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        l = self.cam.lookAtLeft
        gluLookAt( l[0], l[1], l[2], l[3], l[4], l[5], l[6], l[7], l[8] )
        self.onframe(self.window.width, self.window.height, 0)
  
        # RIGHT
        glViewport(self.window.width/2, 0, self.window.width/2, self.window.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        f = self.cam.frustumRight
        glFrustum( f[0], f[1], f[2], f[3], f[4], f[5] )
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        l = self.cam.lookAtRight
        gluLookAt( l[0], l[1], l[2], l[3], l[4], l[5], l[6], l[7], l[8] )
        self.onframe(self.window.width, self.window.height, 1)
        
        
    def renderHUD(self):
                
        # prepare rendering 
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        # Blending Function For transparency Based On Source Alpha Value
        glEnable(GL_BLEND)        
        glBlendEquation(GL_FUNC_ADD)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_DEPTH_TEST)
        
        ##### LEFT ######
        glViewport( 0, 0, self.window.width/2, self.window.height)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        if self.flipScreen:
            glOrtho(self.window.width/2, 0, self.window.height, 0, -1, 1)
        else:
            glOrtho(0, self.window.width/2, 0, self.window.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        # draw all HUD modules
        self.onframehud(self.window.width/2, self.window.height)
        # draw info
        if self.show_info:
            self.draw_info()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        
        ##### RIGHT ######
        glViewport(self.window.width/2, 0, self.window.width/2, self.window.height)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        if self.flipScreen:
            glOrtho(self.window.width/2, 0, self.window.height, 0, -1, 1)
        else:
            glOrtho(0, self.window.width/2, 0, self.window.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        # draw all HUD modules
        self.onframehud(self.window.width/2, self.window.height)
        # draw info
        if self.show_info:
            self.draw_info()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        
        
        glPopAttrib()
        