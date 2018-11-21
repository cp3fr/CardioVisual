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
# updated autumn 2012: 
#           Joan Llobera joan.llobera@epfl.ch
# Web site : http://lnco.epfl.ch/expyvr
#===============================================================================

'''
billboardImage.py
@author: bruno, Tobias 
@since: Autumn 2010

'''
import os
import numpy as np
from pyglet.gl import *
from pyglet import image

#import display
from abstract.AbstractClasses import DrawableModule
from controller import getPathFromString


class ModuleMain(DrawableModule):
    """
    A simple module to display Images on a 3D billboard
    """
    defaultInitConf = {
        'name': 'billboardImage',
        'keyboard_movable': False
    }
    
    defaultRunConf = {
        'filename': 'image_file_name.png',
        'mask': '',
        'flip': False,
        'aspectratio': 1.0,
        'scale': 1.0,
        'depth': 1.5,
        'stereo': 'both',
        'x': 0.0,
        'y': 0.0,
        'angle': 0.0,
        'alpha': 1.0,
        'hsplit_image': False,
        'pause_on_start': False,
        'face_camera': False,
        'rotationX' : 0.0,
        'rotationY' : 0.0,
    }
            
    confDescription = [
        ('name', 'str', "Module displaying an image on a 3D billboard"),
        ('keyboard_movable', 'bool', "Use keyboard arrows to move the object"),
        ('filename', 'str', "Full path and filename of the image to display."),
        ('mask', 'str', "Full path and filename of the image to use as transparency mask."),
        ('scale', 'float', "Scale factor (in 3D) *"),
        ('aspectratio', 'float', "Aspect ratio correction (1.0 by default)"),
        ('x', 'float', "Horizontal position (in 3D) *"),  
        ('y', 'float', "Vertical position (in 3D) *"),  
        ('depth', 'float', "Depth position (distance from screen to the image in 3D) *"),  
        ('angle', 'float', "Angle of rotation in degree *"),  
        ('alpha', 'float', "Opacity factor [0 1] = (1.0-transparency) *"),  
        ('flip', 'bool', "Flip horizontally (mirror)"),
        ('stereo', 'str', "If stereo, to which eye should this image be sent to", ['both', 'left', 'right']),
        ('hsplit_image', 'bool', "The image is stereoscopic, with horizontal split [Left|Right]"),
        ('pause_on_start', 'bool', "Pause the simulation when starting"),
        ('face_camera', 'bool', "Should it always be facing the camera?"),
        ('rotationX', 'float', "Angle of rotation in degree *"),
        ('rotationY', 'float', "Angle of rotation in degree *"),
    ]
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableModule.__init__(self, controller, initConfig, runConfigs)
        
        self.pictures = {}
        self.textures = {}
        self.lists = {}
        self.masks = {}
        self.eye = -1
        self.pause = False
        
        self.angle = 0.0
        self.x = 0.0
        self.y = 0.0
        self.depth = 1.0
        self.scale = 1.0
        self.alpha = 1.0
        
        self.rotationX = 0.0
        self.rotationY = 0.0
        
        # load all the images we're going to display
        for conf in self.runConfs.values():
            imageName = conf['filename']
            if imageName not in self.pictures:
                self.pictures[imageName] = image.load(getPathFromString(imageName))
            
        # and create a display list for each configuration
        for confName, conf in self.runConfs.items():
            pic = self.pictures[conf['filename']]
            self.textures[conf['filename']] = pic.get_texture()
            textcoord = list(self.textures[conf['filename']].tex_coords)
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
                    self.masks[confName] = image.load(getPathFromString(conf['mask'])).get_texture()
                    vl = pyglet.graphics.vertex_list(4, ('v2f', (-1, -1, 1, -1, 1, 1, -1, 1)), ('t3f', tuple(textcoord)), ('m3f', self.masks[confName].tex_coords))
                    glActiveTexture(GL_TEXTURE1)
                    glClientActiveTexture(GL_TEXTURE1)
                    glBindTexture(GL_TEXTURE_2D, self.masks[confName].id)
                    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_COMBINE)
                    glTexEnvi(GL_TEXTURE_ENV, GL_COMBINE_RGB, GL_MODULATE)
                    glTexEnvi(GL_TEXTURE_ENV, GL_COMBINE_ALPHA, GL_MODULATE)
                    # glTexEnvi(GL_TEXTURE_ENV, GL_SOURCE0_ALPHA, GL_PREVIOUS);
                    # glTexEnvi(GL_TEXTURE_ENV, GL_SOURCE1_ALPHA, GL_TEXTURE);
                else:
                    vl = pyglet.graphics.vertex_list(4, ('v2f', (-1, -1, 1, -1, 1, 1, -1, 1)), ('t3f', tuple(textcoord)) )
    
                # Compile a display list
                self.lists[confName + side] = glGenLists(1)
                glNewList(self.lists[confName + side], GL_COMPILE)
                glShadeModel(GL_FLAT)
                glEnable(GL_BLEND)
                glBlendEquation(GL_FUNC_ADD)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)# transparency based on Source Alpha Value
                glPushMatrix()
                glScalef( float(pic.width) / float(pic.height), conf['aspectratio'] , 1.0)
                if conf['flip']:
                    glScalef(-1.0, 1.0, 1.0)
                if self.masks.has_key( confName ):
                    glActiveTexture(GL_TEXTURE1)
                    glEnable(self.masks[confName].target)
                    glBindTexture(self.masks[confName].target, self.masks[confName].id)
                    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_COMBINE)
                    glTexEnvi(GL_TEXTURE_ENV, GL_COMBINE_RGB, GL_MODULATE)
                    glTexEnvi(GL_TEXTURE_ENV, GL_COMBINE_ALPHA, GL_REPLACE)
                glActiveTexture(GL_TEXTURE0)
                glEnable(self.textures[conf['filename']].target)
                glBindTexture(self.textures[conf['filename']].target, self.textures[conf['filename']].id)
                vl.draw(GL_QUADS)         
                glPopMatrix()
                glEndList()
            
        # register keys for manual adjustment of position
        if (self.initConf['keyboard_movable'] ):
            self.displacement = 0.1
            self.controller.registerKeyboardAction( 'LEFT UP RIGHT DOWN PAGEUP PAGEDOWN HOME END NUM_1 NUM_2 NUM_3 NUM_4 NUM_5 NUM_6', self.handlekey )

    def draw(self, window_width, window_height, eye=-1):
        DrawableModule.draw(self, window_width, window_height, eye)
        # shall we display it ?
        if ( eye < 0 or self.eye < 0 or self.eye == eye ):
            glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_TEXTURE_BIT)
            glEnable(GL_DEPTH_TEST)

            
            
            glTranslatef(self.x, self.y, - self.depth)
            glColor4f(1.0, 1.0, 1.0, self.alpha)

            if self.activeConf['face_camera']:
                self.facecam()
            glRotatef(self.rotationX, 1,0,0)
            glRotatef(self.rotationY, 0,1,0)
            glRotatef(self.angle, 0,0,1)
            glScalef(self.scale, self.scale , 1.0)
            # choose side if horizontal split image if required
            side = ''
            if self.activeConf['hsplit_image']:
                side = '_left' if eye==0 else '_right'
            
            # draw billboard
            glCallList(self.lists[self.activeConfName + side]) 
            # revert state
            if self.activeConf['face_camera']:
                if True:
                    glPushMatrix()
                    glPointSize(40); glColor4f(0.0, 1.0,0.0,0.0);
                    glBegin(GL_POINTS); glVertex3f(self.currentpos[0], self.currentpos[1],self.currentpos[2]); glEnd();
                    #print 'currentpos'
                    #print self.currentpos
                    #glColor4f(1.0, 0.0,0.0,0.0);
                    #glBegin(GL_LINES)
                    #glVertex3f(self.currentpos[0], self.currentpos[1],self.currentpos[2])
                    #glVertex3f(self.up[0],self.up[1],self.up[2])
                    #glEnd()
                    glPopMatrix()
                #for the previously poped
                glPopMatrix()
            
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
           
        if self.activeConf['pause_on_start']:
            self.pause = True
            
        self.angle = self.activeConf['angle']
        self.x = self.activeConf['x']
        self.y = self.activeConf['y']
        self.depth = self.activeConf['depth']
        self.scale = self.activeConf['scale']
        self.alpha = self.activeConf['alpha']
        #self.aspectratio = self.activeConf['aspectratio']
        
        
        self.rotationX = self.activeConf['rotationX'] 
        self.rotationY = self.activeConf['rotationY'] 
    def cleanup(self):
        DrawableModule.cleanup(self)
        for list in self.lists.values():
            glDeleteLists(list, 1)
        self.lists = {}
        self.pictures = {}    
        
        # UNregister keys for manual adjustment of position
        if self.initConf['keyboard_movable']:    
            self.controller.unregisterKeyboardAction( 'LEFT UP RIGHT DOWN PAGEUP PAGEDOWN HOME END NUM_1 NUM_2 NUM_3 NUM_4 NUM_5 NUM_6', self.handlekey )
            
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
        elif keypressed == 'NUM_4':
            self.rotationX += self.displacement
        elif keypressed == 'NUM_1':
            self.rotationX -= self.displacement           
        elif keypressed == 'NUM_5':
            self.rotationY += self.displacement
        elif keypressed == 'NUM_2':
            self.rotationY -= self.displacement
        elif keypressed == 'NUM_6':
            self.angle += self.displacement
        elif keypressed == 'NUM_3':
            self.angle -= self.displacement
        print self.getName(), 'pos:  ', self.x, self.y, self.depth,
        print  '  movement step:  ',self.displacement, '  z angle:  ', self.angle
        print 'rot X and Y: ', self.rotationX, self.rotationY

    def replaceCurrentImage(self, filename):
        
        tex = self.textures[self.activeConf['filename']]
        glEnable(tex.target)
        glBindTexture(tex.target, tex.id)
                
        # load picture
        img = image.load(getPathFromString(filename))
            
        # replace current texture
        img.blit_to_texture(tex.target, tex.level, 0, 0, 0)
        
    def facecam(self): #adapted from http://nehe.gamedev.net/article/billboarding_how_to/18011/
        #IT NEEDS FURTHER DEBUGGING
        self.camPos = self.controller.gDisplay.renderers[0].cam.Q
        self.camUp = self.controller.gDisplay.renderers[0].cam.up
        
        self.currentpos = np.array([self.x, self.y, -self.depth])
        self.look = self.camPos -self.currentpos
        self.look= self.look /np.linalg.norm(self.look) #normalized vector
        self.right = np.cross(self.camUp/np.linalg.norm(self.camUp),self.look)
        #print 'self.right is:'
        #print self.right
        self.up = np.cross(self.look,self.right/np.linalg.norm(self.right)) 
        temp= np.array([self.right[0], self.right[1], self.right[2],0,
                self.up[0], self.up[1], self.up[2],0,
                self.look[0], self.look[1], self.look[2],0,
                self.currentpos[0], self.currentpos[1], self.currentpos[2],1])
        self.lookAt = temp.transpose()
        #self.lookAt = temp
        glPushMatrix()
        self.modelview = (GLfloat * self.lookAt.size)(*self.lookAt)
        glMultMatrixf(self.modelview)
        #glGetFloatv(GL_MODELVIEW_MATRIX , self.modelview)
        
        #not do this: glLoadMatrixf(self.modelview)