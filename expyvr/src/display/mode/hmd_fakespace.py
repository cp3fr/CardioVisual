from pyglet.gl import *

from display import renderer
from display.mode import mono

class Renderer(mono.Renderer):
        
    # TODO : implement correctly with two StereoCameras
    
    def __init__(self, **kwds):
        super(Renderer,self).__init__(**kwds)
        self.description = "Fakespace HMD"
                
        # HMD properties of Fakespace Wide5 HMD 
        # ignore fov parameters
        self.WideFow      = 140.0     # Vertical, in degrees
        self.NarrowFow    = 80.0        # Vertical, in degrees
        self.WideLookdown    = 5.0        # In degrees
        self.NarrowLookdown  = 10.0        # In degrees
        self.LookOutward     = 11.25            # In degrees
                
    def render(self):
        renderer.Renderer.render(self)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        l = self.cam.lookAt
        gluLookAt( l[0], l[1], l[2], l[3], l[4], l[5], l[6], l[7], l[8] )
            
        glViewport(0, 0,self.window.width/2, self.window.height/2)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.WideFow,4.0/3.0,renderer.SCENE_NEAR,renderer.SCENE_FAR)
        glTranslatef(renderer.IOD / 2.0, 0.0, 0.0)
        glRotatef(self.WideLookdown,1,0,0)
        glRotatef(-self.LookOutward,0,1,0)
        glMatrixMode(GL_MODELVIEW)
        self.onframe(self.window.width, self.window.height, 0)
        
        glViewport( self.window.width/2, 0,self.window.width/2, self.window.height/2)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.WideFow,4.0/3.0,renderer.SCENE_NEAR,renderer.SCENE_FAR)
        glTranslatef(-renderer.IOD / 2.0, 0.0, 0.0)
        glRotatef(self.WideLookdown,1,0,0)
        glRotatef(+self.LookOutward,0,1,0)
        glMatrixMode(GL_MODELVIEW)
        self.onframe(self.window.width, self.window.height, 0)
        
        glViewport( 0, self.window.height/2,self.window.width/2, self.window.height/2)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.NarrowFow,4.0/3.0,renderer.SCENE_NEAR,renderer.SCENE_FAR)
        glTranslatef(renderer.IOD / 2.0, 0.0, 0.0)
        glRotatef(self.NarrowLookdown,1,0,0)
        glRotatef(-self.LookOutward,0,1,0)
        glMatrixMode(GL_MODELVIEW)
        self.onframe(self.window.width, self.window.height, 1)
        
        glViewport( self.window.width/2, self.window.height/2,self.window.width/2, self.window.height/2)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.NarrowFow,4.0/3.0,renderer.SCENE_NEAR,renderer.SCENE_FAR)
        glTranslatef(-renderer.IOD / 2.0, 0.0, 0.0)
        glRotatef(self.NarrowLookdown,1,0,0)
        glRotatef(self.LookOutward,0,1,0)
        glMatrixMode(GL_MODELVIEW)
        self.onframe(self.window.width, self.window.height, 1)


    def renderHUD(self):
        pass
    