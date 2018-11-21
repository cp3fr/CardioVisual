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
billboardImage.py
@author: bruno 
@since: Autumn 2010

'''
import os
from pyglet.gl import *
from pyglet import image
from pyglet import media

from abstract.AbstractClasses import DrawableModule
from controller import getPathFromString


class ModuleMain(DrawableModule):
    """
    A simple module to display videos on a 3D billboard. Supported video formats are:
        AVI
        DivX
        H.263
        H.264
        MPEG
        MPEG-2
        OGG/Theora
        Xvid
        WMV
    """
    defaultInitConf = {
        'name': 'billboardVideo',
        'keyboard_movable': False
    }
    
    defaultRunConf = {
        'filename': 'video_file_name.avi',
        'mask': '',
        'loop': True,
        'volume': 100,
        'flip': False,
        'aspectratio': 1.0,
        'scale': 1.0,
        'depth': 1.5,
        'alpha': 1.0,
        'stereo': 'both',
        'x': 0.0,
        'y': 0.0,
        'angle': 0.0,
        'hsplit_image': False,
        'pause_on_start': False
    }
            
    confDescription = [
        ('name', 'str', "Module displaying a video on a 3D billboard"),
        ('keyboard_movable', 'bool', "Use keyboard arrows to move the object"), 
        ('filename', 'str', "Full path and filename of the video to display (.avi, .mp2, .wmv)."),
        ('mask', 'str', "Full path and filename of the image to use as transparency mask."),
        ('loop', 'bool', "Loop playback"),
        ('volume', 'int', "Volume of audio output in %"),
        ('scale', 'float', "Scale factor (in 3D)"),
        ('aspectratio', 'float', "Aspect ratio correction (1.0 by default)"),
        ('x', 'float', "Horizontal position (in 3D) *"),  
        ('y', 'float', "Vertical position (in 3D) *"),  
        ('depth', 'float', "Depth position (distance from screen to the image in 3D) *"),  
        ('angle', 'float', "Angle of rotation in degree *"),  
        ('alpha', 'float', "Opacity factor [0 1] = (1.0-transparency) *"),  
        ('flip', 'bool', "Flip horizontally (mirror)"),
        ('stereo', 'str', "If stereo, to which eye should this video be sent to", ['both', 'left', 'right']),
        ('hsplit_image', 'bool', "The image is stereoscopic, with horizontal split [Left|Right]"),
        ('pause_on_start', 'bool', "Pause the simulation when starting"),
    ]
    
    pause = False
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableModule.__init__(self, controller, initConfig, runConfigs)
        
        try:
            from pyglet.media import avbin
            self.log("Using avbin library version %d"%media.avbin.get_version())
        except ImportError:
            raise RuntimeError("avbin.dll not found; cannot play videos")    
        
        self.videoPlayer = {}
        self.lists = {}
        self.masks = {}
        self.eye = -1
        self.alpha = 1.0
        
        # load all the videos we're going to display
        for conf in self.runConfs.values():
            fileName = conf['filename']
            if fileName in self.videoPlayer:
                # We've already loaded that file
                continue
            self.videoPlayer[fileName] = media.Player() 
            w = media.load( getPathFromString(fileName) )
            if w.video_format is None:
                raise RuntimeError( "The file %s is not a video"%fileName ) 
            self.videoPlayer[fileName].queue( w )
            
        # and create a display list for each configuration
        for confName, conf in self.runConfs.items():
            texture = self.videoPlayer[conf['filename']].get_texture()
            textcoord = list(texture.tex_coords)
            h_text_coord = textcoord[3]
                    
            if conf['hsplit_image']:
                sides = ['_left', '_right']
            else:
                sides = ['']
                
            for side in sides:       

                if side == '_left':
                    textcoord[3] = h_text_coord / 2.0
                    textcoord[6] = h_text_coord / 2.0
                    textcoord[0] = 0
                    textcoord[9] = 0
                elif side == '_right':
                    textcoord[3] = h_text_coord 
                    textcoord[6] = h_text_coord 
                    textcoord[0] = h_text_coord / 2.0
                    textcoord[9] = h_text_coord / 2.0
            
                        
                if len(conf['mask']) > 1:
                    self.masks[confName] = image.load( getPathFromString(conf['mask']) ).get_texture()
                    vl = pyglet.graphics.vertex_list(4, ('v2f', (-1, -1, 1, -1, 1, 1, -1, 1)), ('t3f', tuple(textcoord)), ('m3f', self.masks[confName].tex_coords))
                    glActiveTexture(GL_TEXTURE1)
                    glClientActiveTexture(GL_TEXTURE1)
                    glBindTexture(GL_TEXTURE_2D, self.masks[confName].id)
                    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_COMBINE)
                    glTexEnvi(GL_TEXTURE_ENV, GL_COMBINE_RGB, GL_MODULATE)
                    glTexEnvi(GL_TEXTURE_ENV, GL_COMBINE_ALPHA, GL_MODULATE)
                else:
                    vl = pyglet.graphics.vertex_list(4, ('v2f', (-1, -1, 1, -1, 1, 1, -1, 1)), ('t3f', tuple(textcoord)))
                    
                # Compile a display list
                self.lists[confName + side] = glGenLists(1)
                glNewList(self.lists[confName + side], GL_COMPILE)
                glShadeModel(GL_FLAT)
                glEnable(GL_DEPTH_TEST)
                glEnable(GL_BLEND)
                glBlendEquation(GL_FUNC_ADD)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)# transparency based on Source Alpha Value
                glScalef(conf['scale'] * float(texture.width) / float(texture.height), conf['scale'] * conf['aspectratio'] , 1.0)
                if conf['flip']:
                    glScalef(-1.0, 1.0, 1.0)
                if self.masks.has_key( confName ):
                    glActiveTexture(GL_TEXTURE1)
                    glEnable(self.masks[confName].target)
                    glBindTexture(self.masks[confName].target, self.masks[confName].id)
                vl.draw(GL_QUADS)       
                glEndList()
            
        # register keys for manual adjustment of position
        if self.initConf['keyboard_movable']:
            self.displacement = 0.1
            self.controller.registerKeyboardAction( 'LEFT UP RIGHT DOWN PAGEUP PAGEDOWN HOME END', self.handlekey )
 

    def draw(self, window_width, window_height, eye=-1):
        DrawableModule.draw(self, window_width, window_height, eye)
        # shall we display it ?
        if ( eye < 0 or self.eye < 0 or self.eye == eye ):
            glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_TEXTURE_BIT)
            # read next frame from video
            texture = self.videoPlayer[self.activeConf['filename']].get_texture()
            # apply it in texture 0
            glActiveTexture(GL_TEXTURE0)
            glEnable(texture.target)
            glBindTexture(texture.target, texture.id)
            # draw the billboard
            glTranslatef(self.x, self.y, -self.depth)
            glRotatef(self.angle, 0,0,1)
            glColor4f(1.0, 1.0, 1.0, self.alpha)
            
            # choose side if horizontal split image if required
            side = ''
            if self.activeConf['hsplit_image']:
                side = '_left' if eye==0 else '_right'
            
            # draw billboard
            glCallList(self.lists[self.activeConfName + side]) 
                 
            # revert to previous state
            glPopAttrib()
        # pause the time manager only after displaying the first frame
        if self.pause:
            self.controller.gTimeManager.pause()
            self.pause = False
        
    def start(self, dt=0, duration=-1, configName=None):
        DrawableModule.start(self, dt, duration, configName)

        if (self.activeConf['stereo'] != 'both'):
            self.eye = 0 if self.activeConf['stereo'] == 'left' else 1;
        else:
            self.eye = -1
            
        # adjust parameters of the player to the config
        if self.activeConf['loop']:
            self.videoPlayer[self.activeConf['filename']].eos_action = media.Player.EOS_LOOP
        else:
            self.videoPlayer[self.activeConf['filename']].eos_action = media.Player.EOS_PAUSE 
        self.videoPlayer[self.activeConf['filename']].volume = float(self.activeConf['volume']) / 100.0
        # start playing from start
        self.videoPlayer[self.activeConf['filename']].seek(0.0)
        self.videoPlayer[self.activeConf['filename']].play()
        # rendering parameters
        self.x = self.activeConf['x']
        self.y = self.activeConf['y']
        self.depth = self.activeConf['depth']
        self.angle = self.activeConf['angle']
        self.alpha = self.activeConf['alpha']
        
        if self.activeConf['pause_on_start']:
            self.pause = True
        
    def stop(self, dt=0):
        """
        Interrupt play 
        """
        DrawableModule.stop(self, dt)
        self.videoPlayer[self.activeConf['filename']].pause()     
        
    def cleanup(self):
        DrawableModule.cleanup(self)
        for list in self.lists.values():
            glDeleteLists(list, 1)
        self.lists = {}
        self.videoPlayer = {}
        
        # UNregister keys for manual adjustment of position
        if self.initConf['keyboard_movable']:
            self.controller.unregisterKeyboardAction( 'LEFT UP RIGHT DOWN PAGEUP PAGEDOWN HOME END', self.handlekey )
        
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
