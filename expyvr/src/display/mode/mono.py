
from pyglet.gl import *
from pyglet import clock
from pyglet.window import key, mouse

from display import renderer

        
class Renderer(renderer.Renderer):
    
    def __init__(self, **kwds):
        super(Renderer,self).__init__(**kwds)
        self.description = "mono"
        self.cam = renderer.Camera(mirror=self.mirror)
        self.cam.set_aperture(self.fov)
        
        self.screen = None
                
        # setup gl config flags with ARB multisampling, depth and dubble buffering.
        configgl = pyglet.gl.Config(sample_buffers=1, samples=4, depth_size=16,  double_buffer = True, stereo = False)
        # test it
        screens = pyglet.window.get_platform().get_default_display().get_screens()
        if not screens[0].get_matching_configs(configgl):
            # probably not happy with sample buffers
            configgl.sample_buffers = 0
            configgl.samples = 0
        
        self.window = renderer._Win32Window(self.size[0],self.size[1],resizable=True, vsync=True, visible=False, config=configgl)
        
        if self.screenid - 1 < len(self.window.display.get_screens()) and self.screenid > 0:
            self.screen = self.window.display.get_screens()[self.screenid-1]
        else:
            self.screen = None
        self.window.set_mouse_visible(not self.hidecursor) #  is mouse hidden? 
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
            self.on_mouse_scroll(x, y, scroll_x, scroll_y)

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
        renderer.Renderer.render(self)
        glViewport( 0, 0, self.window.width, self.window.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        f = self.cam.frustum
        if self.flipScreen:
            glFrustum( f[1], f[0], f[3], f[2], f[4], f[5] )
        else:
            glFrustum( f[0], f[1], f[2], f[3], f[4], f[5] )
            
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        l = self.cam.lookAt
        gluLookAt( l[0], l[1], l[2], l[3], l[4], l[5], l[6], l[7], l[8] )
        self.onframe(self.window.width, self.window.height)
        