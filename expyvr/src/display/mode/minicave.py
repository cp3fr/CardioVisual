
from pyglet.gl import *
from pyglet import clock
from pyglet.window import key, mouse


from display import renderer

#to take screenshots we will need:
from datetime import datetime
from pyglet import clock, event, image        


#to load the dll we will need:
import platform, os
from ctypes import *
from ctypes.util import find_library
#from display.renderer import Window
        
        
        
#two values to debug this class in computers with smaller displays and graphic cards without quad buffers
STEREOCAVE=1
DEBUG=0
USE_MOCAP=0 
#if USE_MOCAP is put to 1 it reaches to connect to the server,
# but the position tracked is not updated. LOOK IN THE DLL. JL15.02.2012


if DEBUG:
    '''assuming the debugging computer has 2 screens with 1680x1050, each of the 2 windows of the cave will appear at top left of 1 screen'''
    FINAL_WIN_HEIGHT = 768
    FINAL_WIN_WIDTH = 1580
    SIZEWINDOW0=[0,0,FINAL_WIN_WIDTH/2,FINAL_WIN_HEIGHT]
    SIZEWINDOW1=[1680,0, FINAL_WIN_WIDTH/2, FINAL_WIN_HEIGHT]
else:
    '''the final mode involves the minicave as set in the IIG lab (config November 2011, by Quentin Sylvestre & Joan Llobera)'''
    FINAL_WIN_HEIGHT = 768*2;
    FINAL_WIN_WIDTH = (1024+768*2);
    SIZEWINDOW0=[0,FINAL_WIN_HEIGHT,FINAL_WIN_WIDTH/2,FINAL_WIN_HEIGHT]
    SIZEWINDOW1=[0,0,FINAL_WIN_WIDTH/2,FINAL_WIN_HEIGHT ] 
#Note:remember that the config is also set up in the config_minicave.xml file

        
        
        
        
class Renderer(renderer.Renderer):
    
    #screen = None
    #minicave = Minicave()
        
    libcave = None
    dllname='StephMediaLibs.dll'

    W0 = None #_Window 
    W1 = None
    currentWindow=0
        
        
        
    def __init__(self, **kwds):
        #1: we load the DLL.
        if DEBUG:
                print "Minicave class in debug mode"
                self.dllname='StephMediaLibs_d.dll'
                
        try:
            if platform.system() == "Windows":
                dllfile = find_library(self.dllname)
                if dllfile is None:
                    raise RuntimeError("Could not find minicave library named StephMediaLibs.dll")
                else: 
                    self.libcave = cdll.LoadLibrary(dllfile) 
                    print "The Minicave DLL "++ dllfile+" loaded successfully"
            else :       
                print "The Minicave DLL (stephmedialibs) is not available on mac"
                raise RuntimeError("The Minicave DLL (stephmedialibs) not available on OSX")
        except Exception:
            print "An exception importing minicave library named:" + self.dllname
        if self.libcave is None:
            raise RuntimeError("stephmedialibs dll was not loaded")   
    
        #2: we create the 2 windows needed:
        super(Renderer,self).__init__(**kwds)
        self.description = "minicave"
        self.cam = renderer.Camera()
        self.cam.set_aperture(self.fov)
        
        stereo_quad=False
        borderless=True
        if STEREOCAVE:
            stereo_quad = True        
        
        # setup gl config flags with
        configgl = pyglet.gl.Config(sample_buffers=1, samples=4,
                    depth_size=16,  double_buffer = True, stereo = stereo_quad)
        
        print 'size of the window is:' + repr(SIZEWINDOW0[2])+',  '+ repr(SIZEWINDOW0[3])
        size=(SIZEWINDOW0[2],SIZEWINDOW0[3])
        #windowID=0
        #wname='CAVE'
        #wnameID=wname+'0'
                
        temp=renderer._Win32Window(size[0],size[1], vsync=True, visible=True, config=configgl,style=pyglet.window.Window.WINDOW_STYLE_BORDERLESS)
        temp.set_location(SIZEWINDOW0[0],SIZEWINDOW0[1])
        self.W0=temp
        #print("Added CAVE window: " + repr(wnameID))

        size=(SIZEWINDOW1[2],SIZEWINDOW1[3])
        #windowID=1
        #wnameID=wname+'1'
        
        temp=renderer._Win32Window(size[0],size[1], vsync=True, visible=True, config=configgl,style=pyglet.window.Window.WINDOW_STYLE_BORDERLESS)
        temp.set_location(SIZEWINDOW1[0],SIZEWINDOW1[1])
        self.W1=temp
        #print("Added CAVE window: " + repr(wnameID) )
    
        #to get the main functions as in the default mode:
        self.window = self.W1
        
        #TODO: REMOVE MOUSE AND GUARANTEE FOCUS
        self.window.set_mouse_visible(not self.hidecursor) 
        """
        #if self.screenid - 1 < len(self.window.display.get_screens()) and self.screenid > 0:
        #    self.screen = self.window.display.get_screens()[self.screenid-1]
        #else:
            self.screen = None
        self.window.set_mouse_visible(not self.fullscreen) #  guarantee mouse hidden when in fullscreen.
        self.window.set_fullscreen(self.fullscreen, self.screen)
        """
        
        
        #@self.window.event
        #@self.W0.event
        #def on_resize(width, height):
            #self.cam.set_width_height_ratio( float(width) / float(height))
        #    return self.on_resize(width, height)
    

        @self.W0.event
        def on_key_press(symbol, modifiers):
            self.on_key_press(symbol, modifiers)
        @self.W1.event
        def on_key_press(symbol, modifiers):
            self.on_key_press(symbol, modifiers)
        

        @self.W0.event
        def on_key_release(symbol, modifiers):
            self.on_key_release(symbol, modifiers)
        @self.W1.event
        def on_key_release(symbol, modifiers):
            self.on_key_release(symbol, modifiers)
                

        @self.W0.event
        def on_mouse_press(x, y, button, modifiers):
            self.on_mouse_press(x, y, button, modifiers)
        @self.W1.event
        def on_mouse_press(x, y, button, modifiers):
            self.on_mouse_press(x, y, button, modifiers)
        

        @self.W0.event
        def on_mouse_release(x, y, button, modifiers):
            self.on_mouse_release(x, y, button, modifiers)
        @self.W1.event
        def on_mouse_release(x, y, button, modifiers):
            self.on_mouse_release(x, y, button, modifiers)
            

        @self.W0.event
        def on_mouse_drag(x, y, dx, dy, buttons, modifiers):    
            self.on_mouse_drag(x, y, dx, dy, buttons, modifiers)
        @self.W1.event
        def on_mouse_drag(x, y, dx, dy, buttons, modifiers):    
            self.on_mouse_drag(x, y, dx, dy, buttons, modifiers)            

        
        @self.W0.event
        def on_mouse_motion(x, y, dx, dy):    
            self.on_mouse_motion(x, y, dx, dy)
        @self.W1.event
        def on_mouse_motion(x, y, dx, dy):    
            self.on_mouse_motion(x, y, dx, dy)
    
        @self.W0.event
        def on_mouse_scroll(x, y, scroll_x, scroll_y):        
            self.on_mouse_scroll(x, y, scroll_x, scroll_y)
        @self.W1.event
        def on_mouse_motion(x, y, dx, dy):    
            self.on_mouse_motion(x, y, dx, dy)

        @self.W0.event
        def on_draw():
            self.on_draw()
        #NOTE: W1 has no event on draw. See the function draw lower on

        
        @self.W0.event
        def on_show():
            self.on_show()
        @self.W1.event
        def on_show():
            self.on_show()

            
        @self.W0.event
        def on_hide():          
            self.on_hide()
            
        @self.W1.event
        def on_hide():          
            self.on_hide()            

        @self.W0.event
        def on_close():
            self.on_close()
        @self.W1.event
        def on_close():
            self.on_close()
    
    def on_key_press(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            self.W1.close()
            self.W0.close()            
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
            image.get_buffer_manager().get_color_buffer().save(os.path.join(self._controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.name +'.png'))
        elif symbol == key.F:
            fs = not self.window.fullscreen
            # guarantee mouse focus and hidden when in fullscreen.
            self.window.set_mouse_visible(not fs) 
            self.window.set_fullscreen(fs, self.screen)
        elif self._controller is not None:
            self._controller.gKeyboardListener.distributeKeyPress(symbol)
    
       
        

    """
    THE METHODS OF THE CLASS RENDERER THAT ARE REDEFINED********************************************************************
    """
        
            
    def setOnFrameMethods(self, onframemethod, onframehudmethod):
        self.onframe = onframemethod
        self.onframehud = onframehudmethod
        self.init(self.onframe)                
        print 'I have INITIATED minicave configuration with its peculiar system based on 2 windows rendering DIFFERENT things'
            
    """
    The method implementing the rendering 
    """
    def render(self):
        renderer.Renderer.render(self)
        self.draw();
    

      

    """
    THE METHODS SPECIFIC TO USE THE MINICAVE DLL********************************************************************
    """


    
    def init(self,onFrame):
        self.libcave.init(c_int(USE_MOCAP)) #init without MOCAP
        self.onFrame=onFrame
        if STEREOCAVE:
                self.libcave.setStereo()
        
        
    #    def setStereo(self):
    #       self.libcave.setStereo()
        
    def updateAnimationNow(self):
        return self.libcave.updateAnimationNow()
        
    def isItTimeToRenderLeftEye(self):
        return self.libcave.isItTimeToRenderLeftEye()
        
        
    def draw(self):
        #print 'output 0'
        if self.W1 is not None and self.W0 is not None:
            
            
            self.W0.switch_to()
            
            a=self.libcave.allWallsForWindowIdDrawn(self.currentWindow)
            while not a:
                #makeMotion = pt_renderer->isApplyAnimation(); # WE NEED TO CHECK WHETHER IT IS TIME TO UPDATE THE ANIMATION!!!
                if STEREOCAVE:
                    sType=self.isItTimeToRenderLeftEye()
                    self.onFrame(SIZEWINDOW0[0],SIZEWINDOW0[1],sType)
                else:
                    #print 'I AM HERE'
                    self.onFrame(SIZEWINDOW0[0],SIZEWINDOW0[1],90)
                a=self.libcave.allWallsForWindowIdDrawn(self.currentWindow)
            
            self.currentWindow=1
            
            self.W1.switch_to()        

            a=self.libcave.allWallsForWindowIdDrawn(self.currentWindow)
            while not a:
                #makeMotion = pt_renderer->isApplyAnimation(); # WE NEED TO CHECK WHETHER IT IS TIME TO UPDATE THE ANIMATION!!!
                if STEREOCAVE:
                    sType=self.isItTimeToRenderLeftEye()
                    #print 'stype:' + repr(sType)
                    self.onFrame(SIZEWINDOW1[0],SIZEWINDOW1[1],sType)
                else:
                    self.onFrame(SIZEWINDOW1[0],SIZEWINDOW1[1],90)
                a=self.libcave.allWallsForWindowIdDrawn(self.currentWindow)
            
            self.currentWindow=0
        else:
            print('The windows W0 and W1 are none')   
        