import numpy as np
from display.tools import rot_

from pyglet.gl import *
from pyglet import clock, font
from pyglet.window import key, mouse

from display import renderer

        
class Renderer(renderer.Renderer):
    
    def __init__(self, **kwds):
        super(Renderer,self).__init__(**kwds)
        self.description = "stereo quad-buffer"
        self.cam = renderer.StereoCamera(mirror=self.mirror)
        self.cam.set_aperture(self.fov)
        
        if kwds.has_key('focallength'):
            self.cam.set_focal_lenght( kwds['focallength'] )
        
        if kwds.has_key('eyeseparation'):
            self.cam.set_interoccular_distance(kwds['eyeseparation'])
        
        # setup gl config flags
        configgl = pyglet.gl.Config(sample_buffers=1, samples=4,
                    depth_size=16,  double_buffer = True, stereo = True)
        # test it
        screens = pyglet.window.get_platform().get_default_display().get_screens()
        if not screens[0].get_matching_configs(configgl):
            # probably not happy with sample buffers
            configgl.sample_buffers = 0
            configgl.samples = 0
            
        # fixed size 
        self.window = renderer._Win32Window(self.size[0],self.size[1],resizable=True, vsync=True, 
                                            visible=False, config=configgl, style=pyglet.window.Window.WINDOW_STYLE_BORDERLESS)
        
        if self.screenid - 1 < len(self.window.display.get_screens()) and self.screenid > 0:
            self.screen = self.window.display.get_screens()[self.screenid-1]
        else:
            self.screen = None
        self.window.set_mouse_visible(not self.hidecursor) 
        self.window.set_fullscreen(self.fullscreen, self.screen)
        
        @self.window.event
        def on_resize(width, height):
            self.cam.set_width_height_ratio( float(width) / float(height))
            return self.on_resize(width, height)
    
        @self.window.event
        def on_key_press(symbol, modifiers):
            self.on_key_press(symbol, modifiers)

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
        

    """
    The method implementing the rendering 
    """
    def render(self):
        glDrawBuffer(GL_BACK)
        renderer.Renderer.render(self)
        glViewport( 0, 0, self.window.width, self.window.height)
   
        # RIGHT
        glDrawBuffer(GL_BACK_RIGHT) #  back buffer for right eye
        glClear(GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        if self.flipScreen:
            f = self.cam.frustumLeft
            glFrustum( f[1], f[0], f[3], f[2], f[4], f[5] )
        else:
            f = self.cam.frustumRight
            glFrustum( f[0], f[1], f[2], f[3], f[4], f[5] )
            
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        l = self.cam.lookAtRight
        gluLookAt( l[0], l[1], l[2], l[3], l[4], l[5], l[6], l[7], l[8] )
        self.onframe(self.window.width, self.window.height, 1)
        
        # LEFT
        glDrawBuffer(GL_BACK_LEFT) #  back buffer for left eye
        glClear(GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        if self.flipScreen:
            f = self.cam.frustumRight
            glFrustum( f[1], f[0], f[3], f[2], f[4], f[5] )
        else:
            f = self.cam.frustumLeft
            glFrustum( f[0], f[1], f[2], f[3], f[4], f[5] )
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        l = self.cam.lookAtLeft                
        gluLookAt( l[0], l[1], l[2], l[3], l[4], l[5], l[6], l[7], l[8] )
        self.onframe(self.window.width, self.window.height, 0)
  

    def renderHUD(self):
        
        # prepare rendering
        glDrawBuffer(GL_BACK)
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        # Blending Function For transparency Based On Source Alpha Value
        glEnable(GL_BLEND)        
        glBlendEquation(GL_FUNC_ADD)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_DEPTH_TEST)
        
        # RIGHT EYE
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glDrawBuffer(GL_BACK_RIGHT)
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

        # LEFT EYE
        glDrawBuffer(GL_BACK_LEFT)
        glLoadIdentity()
        # FIXME : ridiculous bug fix for ununderstandable problem of second eye not being rendered 
        glBegin(GL_POINTS)
        glVertex2i(-1,-1)
        glEnd()
        
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
          