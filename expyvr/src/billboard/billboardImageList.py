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
billboardImageList.py
@author: bruno 
@since: Autumn 2010

'''
from os import path
import glob, csv, re

from datetime import datetime
from pyglet.gl import *
from pyglet import image

#pylnco modules
from abstract.AbstractClasses import DrawableModule
from controller import getPathFromString

class ModuleMain(DrawableModule):
    """
    A simple module to display Images on a 3D billboard
    """
    defaultInitConf = {
        'name': 'ImagesList',
        'logToCSV': False,
        'files': 'directory/name*.jpg',
        'preload': False,
        'keys': 'LEFT RIGHT'
    }
    
    defaultRunConf = {
        'index': 0.0,
        'flip': False,
        'aspectratio': 1.0,
        'scale': 1.0,
        'depth': 1.5,
        'stereo': 'both',
        'x': 0.0,
        'y': 0.0,
        'angle': 0.0,
        'alpha': 1.0,
        'pause_on_start': False
    }
            
    confDescription = [
        ('name', 'str', "Module displaying the image files taken from a folder on a 3D billboard"),
        ('logToCSV', 'bool', "Save initial and final image names to file( <date>_<modulename>.csv )"),
        ('files', 'str', "Path and base filename of numbered images, with a '*' where number is (e.g. '$EXPDIR$/img*.jpg')."),
        ('preload', 'bool', "Preload all pictures to RAM at initialization time"),
        ('keys', 'str', "List of TWO keys to listen to (space-separated list of keys, e.g. 'LEFT RIGHT')"),
        ('index', 'code', "Index of the picture to display (decimal values are interpolations, can be a python code like random.randint(0,8)) *"),
        ('scale', 'float', "Scale factor (in 3D) *"),
        ('aspectratio', 'float', "Aspect ratio correction (1.0 by default)"),
        ('x', 'float', "Horizontal position (in 3D) *"),  
        ('y', 'float', "Vertical position (in 3D) *"),  
        ('depth', 'float', "Depth position (distance from screen to the image in 3D) *"),  
        ('angle', 'float', "Angle of rotation in degree *"),  
        ('alpha', 'float', "Opacity factor [0 1] = (1.0-transparency) *"),  
        ('flip', 'bool', "Flip horizontally (mirror)"),
        ('stereo', 'str', "If stereo, to which eye should this image be sent to", ['both', 'left', 'right']),
        ('pause_on_start', 'bool', "Pause the simulation when starting"),
    ]
    
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableModule.__init__(self, controller, initConfig, runConfigs)
            
        # initialize logger
        self.logActive = self.initConf['logToCSV']
        if self.logActive:
            now = datetime.today()
            self.csvLogger = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.initConf['name'] +  '.csv') , 'w'), lineterminator = '\n')        
                 
        self.pictures = {}
        self.textures = {}
        self.eye = -1
        self.index = 0
        self.pause = False
        self.index_1 = 0
        self.index_2 = 0
        self.alpha = 1.0
        
        # load all the images we're going to display
        fileList = glob.glob(getPathFromString(self.initConf['files']))
        for f in fileList:
            (filepath, filename) = path.split(f)
            (shortname, extension) = path.splitext(filename)
            ids = re.match("[^\d]*(\d+)[^\d]*", shortname)
            if ids is not None:
                i = int(ids.group(1))
                self.pictures[i] = f
        
        # determine total number of files in the list
        self.totalNumImages = len(fileList)
        
        # create the texture support for rendering
        if self.totalNumImages > 0:
            self.currentImage_1 = image.load(self.pictures[ self.pictures.keys()[0] ])
            self.currentImage_2 = image.load(self.pictures[ self.pictures.keys()[0] ])
            self.ogl_texture_1 = self.currentImage_1.get_texture()
            self.ogl_texture_2 = self.currentImage_2.get_texture()
            self.ogl_vertexlist = pyglet.graphics.vertex_list(4, ('v2f', (-1, -1, 1, -1, 1, 1, -1, 1)), ('t3f', self.ogl_texture_1.tex_coords))

        # preloading of all pictures
        if self.initConf['preload']:
            for i in self.pictures:
                print "loading picture ", i, "(", self.pictures[i], ")"
                self.textures[i] = image.load(self.pictures[i])
    
    
    def draw(self, window_width, window_height, eye=-1):
        DrawableModule.draw(self, window_width, window_height, eye)
        
        # shall we display it ?
        if ( eye < 0 or self.eye < 0 or self.eye == eye ):
            
            glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_TEXTURE_BIT)
            glPushMatrix()            
            glEnable(GL_DEPTH_TEST)
            glTranslatef(self.x, self.y, - self.depth)
            glRotatef(self.angle, 0,0,1)
            glScalef(self.scale, self.scale , 1.0)
            glShadeModel(GL_FLAT)
            glEnable(GL_BLEND)
            glActiveTexture(GL_TEXTURE0)
            glEnable(GL_TEXTURE_2D)
            #glBlendEquation(GL_MAX)
            glBlendEquation(GL_FUNC_ADD)
#            glBlendFunc(GL_ONE, GL_ONE)# transparency based on Source Alpha Value
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)# transparency based on Source Alpha Value
            
            # compute indices
            self.index_1 = int(self.index)
            self.index_2 = self.index_1 + 1
            alpha_2 = float(self.index) - float(self.index_1)
            alpha_1 = 1.0 - alpha_2
            
#            print self.index, self.index_1, self.index_2, alpha_1, alpha_2
            
            # set the texture from index
            self.setCurrentTexture_1(self.index_1)
            
            # apply transformations
            glScalef( float(self.currentImage_1.width) / float(self.currentImage_1.height), self.activeConf['aspectratio'] , 1.0)
            if self.activeConf['flip']:
                glScalef(-1.0, 1.0, 1.0) 
            
            # draw billboard 
            glPushMatrix()       
            glColor4f(1.0, 1.0, 1.0, self.alpha * alpha_1)     
            self.ogl_vertexlist.draw(GL_QUADS)     
            glPopMatrix()    

            if (alpha_2 > 0.01):                
                glColor4f(1.0, 1.0, 1.0, self.alpha * alpha_2)      
                self.setCurrentTexture_2(self.index_2)
                # draw billboard front
                glTranslatef(0.0, 0.0, 0.0001)
                self.ogl_vertexlist.draw(GL_QUADS)         
                  
            # revert state
            glPopMatrix()
            glPopAttrib()
        
        # pause the time manager only after displaying the first frame
        if self.pause:
            self.controller.gTimeManager.pause()
            self.pause = False
            
            
    def setCurrentTexture_1(self, intindex):
        
        glBindTexture(GL_TEXTURE_2D, self.ogl_texture_1.id)    
                
        # load picture if not preloaded
        if not self.textures.has_key(intindex):
            self.textures[intindex] = image.load(self.pictures[intindex])
            self.currentImage_1 = None
            
        # not already done, set current image
        if self.currentImage_1 != self.textures[intindex]:
            self.currentImage_1 =  self.textures[intindex]
            # Draw this image on the currently bound texture at target
            self.currentImage_1.blit_to_texture(self.ogl_texture_1.target, self.ogl_texture_1.level, 0, 0, 0)
             
    def setCurrentTexture_2(self, intindex):
        
        glBindTexture(GL_TEXTURE_2D, self.ogl_texture_2.id)    
                
        # load picture if not preloaded
        if not self.textures.has_key(intindex):
            self.textures[intindex] = image.load(self.pictures[intindex])
            self.currentImage_2 = None
            
        # not already done, set current image
        if self.currentImage_2 != self.textures[intindex]:
            self.currentImage_2 =  self.textures[intindex]
            # Draw this image on the currently bound texture at target
            self.currentImage_2.blit_to_texture(self.ogl_texture_2.target, self.ogl_texture_2.level, 0, 0, 0)
 
                
    def start(self, dt=0, duration=-1, configName=None):
        DrawableModule.start(self, dt, duration, configName)
        
        self.keys = self.initConf['keys'].split()
        if len(self.keys) > 1:
            self.controller.registerKeyboardAction( self.initConf['keys'], self.handlekey )

        if (self.activeConf['stereo'] != 'both'):
            self.eye = 0 if self.activeConf['stereo'] == 'left' else 1;
        else:
            self.eye = -1
           
        if self.activeConf['pause_on_start']:
            self.pause = True
            
        self.angle = self.activeConf['angle']
        self.x = self.activeConf['x']
        self.y = self.activeConf['y']
        self.depth = self.activeConf['depth']
        self.scale = self.activeConf['scale']
        self.index = self.activeConf['index']
        self.alpha = self.activeConf['alpha']
        # determine number of initial image
        self.indexAtStart = self.index

        
    def stop(self, dt=0):
        
        # determine number of final image
        self.indexAtEnd = self.index
        
        # fill in logs if required
        if self.logActive:
            # log time
            line = [ str("%.4f"%self.controller.gTimeManager.experimentTime()), self.controller._currentRoutine, self.controller._currentCondition ]
            # log total number of images, start image and final image
            line.extend( [self.totalNumImages, self.indexAtStart, self.indexAtEnd])
            self.csvLogger.writerow(line)
        
        DrawableModule.stop(self, dt)
        self.controller.unregisterKeyboardAction( self.initConf['keys'], self.handlekey )
        
    def cleanup(self):
        DrawableModule.cleanup(self)
        self.textures = {}
        self.pictures = {}
        
    def setIndex(self, i):
        self.index = i

    def handlekey(self, keypressed = None):
        if keypressed == self.keys[0]:
            self.setIndex((self.index -1.0)%self.totalNumImages)
        elif keypressed == self.keys[1]:
            self.setIndex((self.index +1.0)%self.totalNumImages)