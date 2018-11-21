#tests

import pyglet
from tracker.ReactorModule import ModuleMain

dt = 50.0/1000.0
k = 0
time = 0
hist = []
mocap = ModuleMain(None, initConfig = {'logToCSV': False}, 
                   runConfig = {'kalmanFilter': True})
mocap.start()

def func(dtr):
    global k, dt, time, mocap, hist
    dataX = mocap.getPositions()
    dataV = mocap.getVelocities()
    dataA = mocap.getAccelerations()
    
    k += 1
    time += dtr
    print(time,'s','\n lag: ',(dtr-dt)*1000.0,'ms', '\n Accelerations: ', dataA)
    
    hist.append({'t': time, 'data': dataX})

    if time > 20:
        mocap.stop()
        mocap.cleanup()
        pyglet.clock.unschedule(func)
        pyglet.app.exit()
    

pyglet.clock.schedule_interval(func,dt)

pyglet.app.run()


