from pyglet.gl import *

from display import renderer
from display.mode import mono

class Renderer(mono.Renderer):
        
    def __init__(self, **kwds):
        super(Renderer,self).__init__(**kwds)
        self.description = "stereo alternative left/right"
        self.cam = renderer.StereoCamera(mirror=self.mirror)
        self.cam.set_aperture(self.fov)
        self.stereo_alternate_left = True
        
        if kwds.has_key('focallength'):
            self.cam.set_focal_lenght( kwds['focallength'] )
        
        if kwds.has_key('eyeseparation'):
            self.cam.set_interoccular_distance(kwds['eyeseparation'])
            
        @self.window.event
        def on_mouse_scroll(x, y, scroll_x, scroll_y):        
#            self.cam.set_focal_lenght( self.cam.get_focal_lenght() + float(scroll_y)/300.0) 
            self.cam.iod += scroll_y * self.cam.focalLength / 200
            self.cam.update()
            
    def render(self):
        renderer.Renderer.render(self)
                
        # alternate the eye
        self.stereo_alternate_left = not self.stereo_alternate_left
        if (self.stereo_alternate_left) :
            f = self.cam.frustumLeft
            l = self.cam.lookAtLeft
        else:
            f = self.cam.frustumRight
            l = self.cam.lookAtRight
           
        glViewport( 0, 0, self.window.width, self.window.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        if self.flipScreen:
            glFrustum( f[1], f[0], f[3], f[2], f[4], f[5] )
        else:
            glFrustum( f[0], f[1], f[2], f[3], f[4], f[5] )
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt( l[0], l[1], l[2], l[3], l[4], l[5], l[6], l[7], l[8] )
        self.onframe(self.window.width, self.window.height, 0 if self.stereo_alternate_left else 1)
  
