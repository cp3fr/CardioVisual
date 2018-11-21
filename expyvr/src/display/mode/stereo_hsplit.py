from pyglet.gl import *

from display import renderer
from display.mode import mono

class Renderer(mono.Renderer):
        
    def __init__(self, **kwds):
        super(Renderer,self).__init__(**kwds)
        self.description = "stereo horizontal split"
        self.cam = renderer.StereoCamera(mirror=self.mirror)
        self.cam.set_aperture(self.fov)
        
        if kwds.has_key('focallength'):
            self.cam.set_focal_lenght( kwds['focallength'] )
        
        if kwds.has_key('eyeseparation'):
            self.cam.set_interoccular_distance(kwds['eyeseparation'])
        
        @self.window.event
        def on_mouse_scroll(x, y, scroll_x, scroll_y):        
            self.cam.set_interoccular_distance( self.cam.get_interoccular_distance() + self.cam.get_focal_lenght()*float(scroll_y)/100) 
#            self.cam.set_focal_lenght( self.cam.get_focal_lenght() + float(scroll_)/300.0) 
            self.cam.update()
        
    def render(self):
        renderer.Renderer.render(self)
                   
        # LEFT
        glViewport( 0, 0, self.window.width/2, self.window.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        if self.flipScreen:
            f = self.cam.frustumRight
            glFrustum( f[1]/2, f[0]/2, f[3], f[2], f[4], f[5] )
        else:
            f = self.cam.frustumLeft
            glFrustum( f[0]/2, f[1]/2, f[2], f[3], f[4], f[5] )
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        l = self.cam.lookAtLeft
        gluLookAt( l[0], l[1], l[2], l[3], l[4], l[5], l[6], l[7], l[8] )
        self.onframe(self.window.width/2, self.window.height, 0)
  
        # RIGHT
        glViewport(self.window.width/2, 0, self.window.width/2, self.window.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        if self.flipScreen:
            f = self.cam.frustumLeft
            glFrustum( f[1]/2, f[0]/2, f[3], f[2], f[4], f[5] )
        else:
            f = self.cam.frustumRight
            glFrustum( f[0]/2, f[1]/2, f[2], f[3], f[4], f[5] )
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        l = self.cam.lookAtRight
        gluLookAt( l[0], l[1], l[2], l[3], l[4], l[5], l[6], l[7], l[8] )
        self.onframe(self.window.width/2, self.window.height, 1)

    def renderHUD(self):

        # LEFT
        glViewport( 0, 0, self.window.width/2, self.window.height)
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
        
        # RIGHT
        glViewport(self.window.width/2, 0, self.window.width/2, self.window.height)
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
        

        
