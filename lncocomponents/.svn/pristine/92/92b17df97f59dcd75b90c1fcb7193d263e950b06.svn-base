
#
#Using pyMocap+pyHMD+pyLogger in the same file
#


#first we have to modify PYTHONPATH to include the sources tree
import sys
import os

#must know the OS delimiter... for window$$ & unix compatibility
ds = os.path.sep

sys.path.append('..'+ds+'..'+ds+'src'+ds+'tracker')
sys.path.append('..'+ds+'..'+ds+'src'+ds+'display')
sys.path.append('..'+ds+'..'+ds+'src'+ds+'logger')

#Now import everything


import numpy as np
import pyglet as pg

import pyLogger
import mocap
import render_tools
from pyLNCO import *

import mocap_tools as mct


clock = pg.clock

#some aliases
Logger = pyLogger.Logger
Mocap  = mocap.mocap

#creater a buffer for mocap positions
POS_buff = pyLogger.buffer(1000)
#skeleton matrix
C = np.zeros((0,0))

mc = Mocap(40.0/1000.0)

time = 0.0

#creates a logger that backups data every 40seconds to './data/backup'
latency = 40.0 #seconds
path = '.'+ds+'data'
description='Logging the whole world'
logger = Logger(latency,path,description)



#starts modules
#logger.start()
mc.open()
mc.start()


#Sending mocap data to the logger 1 time every 50 ms
#This should be avoided with the message passing system
def func(dt):
    dataX = mc.get_pos()
    dataV = mc.get_vel()
    dataA = mc.get_acc()

    logger.logme(dataX)
    logger.logme(dataV)
    logger.logme(dataA)

    POS_buff.update(dataX['data'].flatten())
    
clock.schedule_interval(func,50.0/1000.0)



#Plotting text given 2d screen coordinates

def plot_text(wx,wy, text):
    
    label = pg.text.Label(text, x=wx,y=wy, font_size=10,anchor_x='left', anchor_y='center')
    
    label.draw()
    





#Testing the calculation of a skeleton from mocap data
def update_skeleton(dt):

    global C

    print "Skeleton calculation started, this will take a while!"

    print "Mocap sensors distances statistics..."
    md, stdd = mct.dist_stats(np.array(POS_buff.data))
    print "Skeleton algorithm..."
    C = mct.skeleton2(md,stdd, 40)
    
#waits 30s to have data for skeleton calculation
#clock.schedule_once(update_skeleton,30.0)

#3d objects
room = objloader.OBJ('..'+ds+'..'+ds+'src'+ds+'display'+ds+'models'+ds+'maze3.obj')
sphere = pg.gl.glu.gluNewQuadric()



time = 0

#
#Extra scheduled functions, like the ontime() of XVR
#
def ontime(dt):
    global time
    time += dt
    
def onframe(w,h):

    
    
    #draw psychedelic room
    glCallList(room.gl_list)

    #Lets do some funny stuff with the MOCAP data
    dataX = mc.get_pos()
    dataV = mc.get_vel()
    dataA = mc.get_acc()

    N = dataX['data'].shape[1]

    #Draw markers
    
    
    for k in range(N):
        x = dataX['data'][0,k]
        y = -dataX['data'][1,k]
        z = dataX['data'][2,k]

        pg.gl.glTranslatef(-x,-y,-z)
        
        #pg.gl.glu.gluSphere(sphere, 0.05, 10, 10)

        pg.gl.glTranslatef(x,y,z)

        #This shows how to render text in 3d
        #coordinates!
        #First we collect the projection on the screen
        wx,wy,wz = render_tools.model_to_screen(-x,-y,-z)
        #second we define the orthonomal projection
        sc._set_2d(w,h)
        #now we can draw
        plot_text(wx,wy, str(k))
        #unset the orthonormal projection
        sc._unset_2d()


    #Draw skeleton

    if C.shape == (N,N) :
        
        for i in range(N-1):
            for j in range(i+1,N):

                if C[i,j] > 0.0 :
                    x1 = dataX['data'][0,i]
                    y1 = -dataX['data'][1,i]
                    z1 = dataX['data'][2,i]
                    x2 = dataX['data'][0,j]
                    y2 = -dataX['data'][1,j]
                    z2 = dataX['data'][2,j]

                    pg.graphics.draw(2, pg.gl.GL_LINES,
                                     ('v3f',(-x1,-y1,-z1,-x2,-y2,-z2)))                                           


        
    
# creates scene objects
sc = scene([ [0.0, -1.0, 0.0, 1.0], [0.0, 1.0, 0.0, 1.0] ], onframe) 
sc.screen = 'MONO' #can be: 'HMD', 'STEREO', 'MONO'


#
#Set-up a window, some event handlers
#

create_window(ontime, sc)  
    

#run!
pg.app.run()

clock.unschedule(update_skeleton)

#logger.stop()
mc.stop()
mc.close()
