"""
Generates fake mocap data and saves into a file
"""

import csv
from numpy import *
from numpy.random import *


freq = 30   #update in hz
time = 60   #amt of data in seconds
numSensors = 30
dim = 3
csvLogger = csv.writer(open('c:\out.csv','w'))

#generate smooth trajectories from zero
prevData = -0.01*ones((dim,numSensors))
for t in range(time*freq):    
    newData = zeros((dim,numSensors))
    
    for s in range(numSensors):
        if (t % 2) == 0:
            newData[:,s] = prevData[:,s] + 0.2*ones(dim)*rand(dim)   #increase rand xyz in cms
        else:
            newData[:,s] = prevData[:,s] - 0.2*ones(dim)*rand(dim)   #decrease update rand xyz in cms
        prevData[:,s] = newData[:,s]
    
    # write out
    tline = [0.0256]  #fake time
    sdata = newData.transpose().tolist()
    tline.extend([coord for sensor in sdata for coord in sensor])
    csvLogger.writerow(tline)


