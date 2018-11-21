from pyglet.gl import *

from display import renderer
from display.mode import mono

# import platform, os
from ctypes import *
from ctypes.util import find_library
# from ctypes.wintypes import BOOL
# from time import sleep
# from os import environ
# from os.path import *

class Renderer(mono.Renderer):
        
    def __init__(self, **kwds):
        super(Renderer,self).__init__(**kwds)
        self.description = "Oculus VR HMD"
        self.cam = renderer.StereoCamera(mirror=self.mirror)
        self.cam.set_aperture(self.fov)
        
        if kwds.has_key('focallength'):
            self.cam.set_focal_lenght( kwds['focallength'] )
        
        if kwds.has_key('eyeseparation'):
            self.cam.set_interoccular_distance(kwds['eyeseparation'])
        
        dllfile = find_library("oculusOpenHMD_headfix.dll")
        if dllfile is None:
            print "Could not find oculusOpenHMD_headfix.dll", 
        else:
            print "\n\nLoading ", dllfile
        
            self.OVR = cdll.LoadLibrary( dllfile ) 
            
            if self.OVR:
                r = self.OVR.initOculus()
                if r < 0:
                    print "\n\n Could not initialize an Oculus\n\n"
                    
            else:
                print "Could not load Oculus DLL"
        
        @self.window.event
        def on_mouse_scroll(x, y, scroll_x, scroll_y):        
            self.cam.set_interoccular_distance( self.cam.get_interoccular_distance() + self.cam.get_focal_lenght()*float(scroll_y)/100) 
#            self.cam.set_focal_lenght( self.cam.get_focal_lenght() + float(scroll_)/300.0) 
            self.cam.update()
            
    def close(self):
        self.OVR.endOculus()
        renderer.Renderer.close(self)
        
    def render(self):
        renderer.Renderer.render(self)

        self.OVR.updateGL()
        
        # LEFT
        l = self.cam.lookAtLeft
        self.OVR.prerenderLeftEye( c_double(l[0]), c_double(l[1]), c_double(l[2]), c_double(l[3]), c_double(l[4]), c_double(l[5]), c_double(l[6]), c_double(l[7]), c_double(l[8]))
        self.onframe(self.window.width/2, self.window.height, 0)
  
        # RIGHT
        l = self.cam.lookAtRight
        self.OVR.prerenderRightEye( c_double(l[0]), c_double(l[1]), c_double(l[2]), c_double(l[3]), c_double(l[4]), c_double(l[5]), c_double(l[6]), c_double(l[7]), c_double(l[8]))
        self.onframe(self.window.width/2, self.window.height, 1)
        
        glViewport( 0, 0, self.window.width, self.window.height)
        self.OVR.draw()

    def renderHUD(self):
        
        # LEFT
        glViewport(50 + 100, 90, int((self.window.width)/2/1.5), int(self.window.height/1.5))
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
        self.onframehud((self.window.width)/2, self.window.height)
        # draw info
        if self.show_info:
            self.draw_info()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glPopAttrib()
        
        # RIGHT
        glViewport(self.window.width/2 +50, 90, int((self.window.width)/2/1.5), int(self.window.height/1.5))
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
            glOrtho((self.window.width)/2, 0, self.window.height, 0, -1, 1)
        else:
            glOrtho(0, (self.window.width)/2, 0, self.window.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        # draw all HUD modules
        self.onframehud((self.window.width)/2, self.window.height)
        # draw info
        if self.show_info:
            self.draw_info()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glPopAttrib()

'''        
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
'''
        
