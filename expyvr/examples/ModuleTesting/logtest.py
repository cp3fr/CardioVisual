
## testing pyLogger

import numpy as np
import pyglet as pg
import logger.mainlogger as pyLogger

Logger = pyLogger.Logger

time = 0.0

logger = Logger(30.0, './data','Logger Tests')

logger.start()

clock = pg.clock


#
# Two scheduled processes can log at different rates!
#

#This simulates mocap data
def f1(dt):

    name = 'mocap'
    X = np.random.randn(90)

    logger.logMe({'name': name, 'data': X})

#some other stuff    
def f2(dt):

    name = 'stuff'
    X = np.random.randn(50,50)

    logger.logMe({'name': name, 'data': X})

def f3(dt):
    global time
    time += dt

    #stopping after 2min
    if time >= 120.0:
        clock.unschedule(f1)
        clock.unschedule(f2)
        clock.unschedule(f3)
        logger.stop()
        pg.app.exit()


        
clock.schedule_interval(f1, 33.0/1000.0)
#clock.schedule_interval(f2, 50.0/1000.0)
clock.schedule(f3)

pg.app.run()
