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

'''
billboardCamera.py
Created on Jul 8, 2010
@author: bruno

filling in the delay queue
---------------------------
Given a delay of X seconds, it is not possible to display anything before X sec 
has passed after the module activity started (blue line) ; 
so, even if you specify a display starting at the same time, the module will 
not be able to show the image immediately.

auto calibration to camera update frequency
---------------------------------------------
Depending on the cameras, the reading of frames may be slow and update period 
cannot be the same than the display 60Hz. Therefore, I had to develop a calibration 
mechanism to automatically detect the camera update frequency, in order to compute 
how many frames have to be skipped to achieve the desired delay. This is done during 
the "filling of delay queue" process.

no magic with delay
---------------------
As the delay mechanism is necessarily a multiple of the update period of the 
camera, the program often cannot achieve the delay specified. It will always 
delay by the closer delay just above.
You should choose delay values multiple of your camera update period if you want precision.


'''

import time
from timeit import repeat
from pyglet.gl import *
from pyglet import image
import cv
import threading

from abstract.AbstractClasses import DrawableModule
from controller import getPathFromString

class CVUpdateThread ( threading.Thread ):
    def __init__(self, parent = None):
        threading.Thread.__init__(self)
        self.module = parent        
        
    def run(self):
        while self.module.opencvid > -1:
            # get the lock for the thread
            self.module.condition.acquire()
            # if the frame was read
            if not self.module.wasUpdated:
                # get opencv frame 
                if cv.GrabFrame(self.module.capture) > 0:
                    self.module.frame = cv.RetrieveFrame(self.module.capture)
                    
                    if self.module.activeConf['greyscale']:
                        cv.CvtColor(self.module.frame, self.module.grey, cv.CV_RGB2GRAY) 
                        cv.CvtColor(self.module.grey, self.module.frame, cv.CV_GRAY2RGB) 
                    
                    # tell the module the frame was updated
                    self.module.wasUpdated = True
                # wait for the module to update
                self.module.condition.wait()
            # free the lock for the module
            self.module.condition.release()
            # necessary to give the main thread time to acquire lock
            time.sleep(0)

class ModuleMain(DrawableModule):
    """
    A simple module to display images of a webcam using openCV
    """
    defaultInitConf = {
        'name': 'camera', 
        'opencvid': '0',
        'opencvmaxwidth': 1280,
        'opencvconfig': '',
        'update_time': 0.0,
        'bg_subtract_key': 'C',
        'bg_subtract_thresh': 25,
        'keyboard_movable': False
    }
    
    defaultRunConf = {
        'mask': '',
        'flip': False,
        'vertical': False,
        'aspectratio': 1.0,
        'scale': 1.0,
        'depth': 1.5,
        'delay': 0.0,
        'stereo': 'both',
        'x': 0.0,
        'y': 0.0,
        'angle': 0.0,
        'alpha': 1.0,
        'greyscale': False
    }
        
    confDescription = [
        ('name', 'str', "Module displaying the frames of a webcam on a 3D billboard"),
        ('opencvid', 'str', "Opencv identifier of the camera source.", ['0', '1']),
        ('opencvmaxwidth', 'int', "Maximum width of frames ; the smaller the faster (Height will be determined accordingly)."),
        ('update_time', 'float', "Duration of update in seconds, leave 0 for automatic calibration"),  
        ('bg_subtract_key', 'str', "List of keys which trigger background capture for removal (space-separated list of keys, e.g. 'A B C ENTER')"),
        ('bg_subtract_thresh', 'int', "Luminance difference threshold between background and foreground for substraction [1..255]"),  
        ('keyboard_movable', 'bool', "Use keyboard arrows to move the object"),
        ('delay', 'float', "Delay in second"),  
        ('mask', 'str', "Full path and filename of the image to use as transparency mask."),
        ('scale', 'float', "Scale factor (in 3D)"),
        ('aspectratio', 'float', "Aspect ratio correction (1.0 by default)"),
        ('x', 'float', "Horizontal position (in 3D) *"),  
        ('y', 'float', "Vertical position (in 3D) *"),  
        ('depth', 'float', "Depth position (distance from screen to the image in 3D) *"),  
        ('angle', 'float', "Angle of rotation in degree *"),  
        ('alpha', 'float', "Opacity factor [0 1] = (1.0-transparency) *"),  
        ('flip', 'bool', "Flip horizontally (mirror)"),
        ('stereo', 'str', "If stereo, to which eye should this camera be sent to.", ['both', 'left', 'right']),
        ('greyscale', 'bool', "Change RGB camera image to greyscale"),
    ]
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        """
        Create OpenCV and OpenGL objects to read the camera (with delay if necessary)
        and start the update thread reading camera frames.
        """
        DrawableModule.__init__(self, controller, initConfig, runConfigs)
                
        self.lists = {}
        self.masks = {}             
                
        # 0. READ MAX DELAY FROM RUN CONFIGS
        self.maxdelay = 0.0
        for conf in self.runConfs.values():
            if conf['delay'] > self.maxdelay:
                self.maxdelay = conf['delay']
                
        # 1. OPEN CAMERA        
        # get capture camera from opencv (unique ref per camera)
        self.opencvid = 1 if self.initConf['opencvid'] == '1' else 0
        self.capture = cv.CaptureFromCAM( self.opencvid ) 
        cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_CONVERT_RGB, True)
        cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_WIDTH , int( self.initConf['opencvmaxwidth'] ))
        cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FPS, 60)
        # get ref to (C pointer) to the frame queried (unique per capture) and test it
        self.frame = cv.QueryFrame(self.capture)          
        if self.frame is None:
            raise RuntimeError("Could not read frames from camera %d"%self.opencvid)    
        else:
            self.log("Camera %d opened. Frames are %d x %d px."%(self.opencvid, self.frame.width, self.frame.height))
            
        # 2. create image & textures for opengl 
        picture = image.ImageData(self.frame.width, self.frame.height, 'RGB', self.frame.tostring())
        pictureTexture =  picture.get_texture()
        self.texture = []

        # 3. compute frame rate 
        if self.initConf['update_time'] < 0.01:
            # perform auto calibration in case the update time is 0 or invalid
            self.calibrate(pictureTexture)
        else:
            # use the given update time if provided
            self.averageUpdateTime = self.initConf['update_time']
        
        # 4. compute frame delay & fill in the buffer of textures    
        self.maxFrameDelay = int (self.maxdelay / self.averageUpdateTime)
        for i in xrange(self.maxFrameDelay + 1):             
            # fill in the buffer of textures with camera frames
            self.frame = cv.QueryFrame(self.capture)
            self.grey = cv.CreateImage( (self.frame.width, self.frame.height), cv.IPL_DEPTH_8U, 1 )
            self.texture.insert( i, image.Texture.create(pictureTexture.width, pictureTexture.height) )
            glBindTexture(self.texture[i].target, self.texture[i].id)
            glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.frame.width, self.frame.height, GL_BGR, GL_UNSIGNED_BYTE, self.frame.tostring())

        # 5. CREATE a display list for each configuration
        for confName, conf in self.runConfs.items():
            if len(conf['mask']) > 1:
                self.masks[confName] = image.load(getPathFromString(conf['mask'])).get_texture()
                vl = pyglet.graphics.vertex_list(4, ('v2f', (-1, -1, 1, -1, 1, 1, -1, 1)), ('t3f', pictureTexture.tex_coords), ('m3f', self.masks[confName].tex_coords))
                glActiveTexture(GL_TEXTURE1)
                glClientActiveTexture(GL_TEXTURE1)
                glBindTexture(GL_TEXTURE_2D, self.masks[confName].id)
                glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_COMBINE)
                glTexEnvi(GL_TEXTURE_ENV, GL_COMBINE_RGB, GL_MODULATE)
                glTexEnvi(GL_TEXTURE_ENV, GL_COMBINE_ALPHA, GL_MODULATE)
            else:
                vl = pyglet.graphics.vertex_list(4, ('v2f', (-1, -1, 1, -1, 1, 1, -1, 1)), ('t3f', pictureTexture.tex_coords))
 
            # Compile a display list
            self.lists[confName] = glGenLists(1)
            glNewList(self.lists[confName], GL_COMPILE)
            glShadeModel(GL_FLAT)
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_BLEND)
            glBlendEquation(GL_FUNC_ADD)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)# transparency based on Source Alpha Value

#            glColor4f(1.0, 1.0, 1.0, 0.1)
            glScalef(float(pictureTexture.width) / float(pictureTexture.height), -1.0 * conf['aspectratio'] , 1.0)
            if conf['flip']:
                glScalef(-1.0, 1.0, 1.0)
            if conf['vertical']:
                glRotatef(90.0, 0.0, 0.0, 1.0)
            if self.masks.has_key( confName ):
                glActiveTexture(GL_TEXTURE1)
                glEnable(self.masks[confName].target)
                glBindTexture(self.masks[confName].target, self.masks[confName].id)
            vl.draw(GL_QUADS)  
            glEndList()
        
        # 6. Init variables and start thread
        self.alpha = 1.0
        self.scale = 1.0
        self.readIndex = 0
        self.writeIndex = 0
        self.wasUpdated = False
        self.frameDelay = 0
        self.eye = -1
        self.frame_background = None
        
        self.condition = threading.Condition()
        self.thread = CVUpdateThread(parent=self)
        self.thread.start()
        
        # register keys for manual adjustment of position
        if (self.initConf['keyboard_movable'] ):
            self.displacement = 0.1
            self.controller.registerKeyboardAction( 'LEFT UP RIGHT DOWN PAGEUP PAGEDOWN HOME END', self.handlekey )
        

    def cleanup(self):
        DrawableModule.cleanup(self)
        
        # request stop and wait for the thread to terminate
        self.condition.acquire()
        self.opencvid = -1
        self.condition.notifyAll()
        self.condition.release()
        self.thread.join(1.0)
        
        # release camera
        del self.capture
        
        # UNregister keys for manual adjustment of position
        if self.initConf['keyboard_movable']:    
            self.controller.unregisterKeyboardAction( 'LEFT UP RIGHT DOWN PAGEUP PAGEDOWN HOME END', self.handlekey )
        
    def draw(self, window_width, window_height, eye = -1):
        # shall we display it ?
        if ( eye < 0 or self.eye < 0 or self.eye == eye ):
            glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_TEXTURE_BIT)
            # use the texture at the reading index
            glActiveTexture(GL_TEXTURE0)
            glEnable(GL_TEXTURE_2D)
            glBindTexture(self.texture[self.readIndex].target, self.texture[self.readIndex].id)
            # draw the billboard
            glPushMatrix()
            glTranslatef(self.x, self.y, -self.depth)
            glRotatef(self.angle, 0,0,1)
            glScalef(self.scale, self.scale , 1.0)
            glColor4f(1.0, 1.0, 1.0, self.alpha)
            glCallList(self.lists[self.activeConfName])        
            glPopMatrix()
            # revert to previous state
            glPopAttrib()
        
    def start(self, dt=0, duration=-1, configName=None):
        """
        Prepare rendering of the camera
        """
        DrawableModule.start(self, dt, duration, configName)
        self.controller.registerKeyboardAction( self.initConf['bg_subtract_key'], self.getFrame )
        # rendering parameters
        self.x = self.activeConf['x']
        self.y = self.activeConf['y']
        self.depth = self.activeConf['depth']
        self.angle = self.activeConf['angle']
        self.scale = self.activeConf['scale']
        self.alpha = self.activeConf['alpha']
        
        if (self.activeConf['stereo'] != 'both'):
            self.eye = 0 if self.activeConf['stereo'] == 'left' else 1;
        else:
            self.eye = -1

        self.frameDelay = int ( self.activeConf['delay'] / self.averageUpdateTime )
        mesg = "Delay is {x:2.2f} second instead of {t:2.2f} ( {n} frames delay, updated every {u:2.2f}s)."
        self.log( mesg.format( n=self.frameDelay, x = float(self.frameDelay) * self.averageUpdateTime , t = self.activeConf['delay'], u=self.averageUpdateTime ))
            
        pyglet.clock.schedule_interval(self.update, self.averageUpdateTime)

    def stop(self, dt=0):
        DrawableModule.stop(self, dt)
        pyglet.clock.unschedule(self.update)
        self.controller.unregisterKeyboardAction( self.initConf['bg_subtract_key'], self.getFrame )
        
    def update(self, dt):
        """
        The update is called regularly to get a new cv frame and fill in
        the queue of frames to be displayed (with delay)
        """
        if not self.started:
            return
        # shall we update the texture of the camera?
        if (self.wasUpdated):
            self.condition.acquire()
            # use the next texture index to write into
            self.writeIndex = (self.writeIndex + 1) % (self.maxFrameDelay + 1)
            # fill texture
            glBindTexture(self.texture[self.writeIndex].target, self.texture[self.writeIndex].id)
                        
            if self.frame_background is not None:
                cv.AbsDiff( self.frame_background, self.frame, self.frame_diff) 
                cv.CvtColor(self.frame_diff, self.frame_thresh, cv.CV_RGB2GRAY)   
                cv.Smooth(self.frame_thresh, self.frame_thresh,  cv.CV_BLUR)
                cv.Threshold(self.frame_thresh, self.frame_thresh, self.initConf['bg_subtract_thresh'], 255, cv.CV_THRESH_BINARY)
                cv.MorphologyEx(self.frame_thresh, self.frame_thresh, None, self.se, cv.CV_MOP_CLOSE, 1)
                cv.MorphologyEx(self.frame_thresh, self.frame_thresh, None, self.se, cv.CV_MOP_OPEN, 1)
                cv.MixChannels([self.frame, self.frame_thresh], [self.frame_alpha], [(0, 0),(1, 1),(2, 2),(3, 3) ])
                glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.frame_alpha.width, self.frame_alpha.height, GL_BGRA, GL_UNSIGNED_BYTE, self.frame_alpha.tostring())

                # debugging : show the mask
#                cv.CvtColor(self.frame_thresh, self.frame, cv.CV_GRAY2RGB)
#                glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.frame.width, self.frame.height, GL_BGR, GL_UNSIGNED_BYTE, self.frame.tostring())
            else:
                glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.frame.width, self.frame.height, GL_BGR, GL_UNSIGNED_BYTE, self.frame.tostring())

            # set index for reading the former frame
            self.readIndex = (self.writeIndex - self.frameDelay) % (self.maxFrameDelay + 1)
            # end sync with thread
            self.wasUpdated = False
            self.condition.notify()
            self.condition.release()
        
        
    def calibrate(self, tmptexture):
        """
        Calibration is needed to compute the actual update period possible
        with the camera in use; the cv code to query frame is blocking, so 
        it slows down the update if the camera refresh is lower than the 
        desired update refresh rate. 
        """
        
        # let the camera start up and estimate the update time needed to read a frame and fill in a texture
        stime = time.clock()
        for i in xrange(10):
            # read a frame from the camera
            self.frame = cv.QueryFrame(self.capture)        
            # replace the content of the first image of the buffer with the last camera frame
            glBindTexture(tmptexture.target, tmptexture.id)
            glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.frame.width, self.frame.height, GL_BGR, GL_UNSIGNED_BYTE, self.frame.tostring())
        # how long to read the 10 frames ?
        deltat = time.clock() - stime
        # compute averate time for a frame, but over estimate it a bit
        self.averageUpdateTime = deltat / float(i)  
        
        self.log( "Camera calibrated to update every %2.2fs"%self.averageUpdateTime )
        

    def getFrame(self, keypressed = None):
        self.log("Capturing background")
        self.condition.acquire()
        self.frame_background = cv.CreateImage( (self.frame.width, self.frame.height), self.frame.depth, self.frame.nChannels )
        self.frame_diff = cv.CreateImage( (self.frame.width, self.frame.height), self.frame.depth, self.frame.nChannels )
        self.frame_alpha = cv.CreateImage( (self.frame.width, self.frame.height), self.frame.depth, 4 )
        self.frame_thresh = cv.CreateImage( (self.frame.width, self.frame.height), cv.IPL_DEPTH_8U, 1 )
        self.frame_tmp = cv.CreateImage( (self.frame.width, self.frame.height), cv.IPL_DEPTH_8U, 1 )
        cv.Copy(self.frame, self.frame_background)
        self.condition.notify()
        self.condition.release()
           
        self.se = cv.CreateStructuringElementEx(5,5,2,2,cv.CV_SHAPE_ELLIPSE)
        
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
            self.depth += self.displacement
        elif keypressed == 'PAGEDOWN':
            self.depth -= self.displacement
        elif keypressed == 'HOME':
            self.displacement *= 2.0
        elif keypressed == 'END':
            self.displacement /= 2.0
        print self.getName(), self.x, self.y, self.depth
        
    def saveCapture(self, filename):
        image = self.frame
        cv.SaveImage( getPathFromString(filename), image)
        