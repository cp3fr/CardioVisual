#import libraries
import numpy as np
import math as math
from planar import Affine
from planar import Vec2
from CircularBuffer import CircularBuffer

#TurtleController: Input-output mapping between control command and turtle movement using desired control strategy       
class TurtleController(object):

    #initial object settings
    def __init__(self, controlType, startPos, goalPos, angDev, buffSize, maxDist):
        #constants
        self.startPos = [startPos[0] / 100.0, startPos[1] / 100.0]
        self.goalPos = [goalPos[0] / 100.0, goalPos[1] / 100.0]
        self.angDev = angDev 
        self.maxDist = maxDist
        self.defaultPos = self.startPos
        self.controlType = controlType
        #buffer for position filtering, fill up with start position
        self.bufferDefaultStartPos = [CircularBuffer(buffSize), CircularBuffer(buffSize)] 
        for i in range(buffSize):
            self.bufferDefaultStartPos[0].addVal(self.startPos[0])
            self.bufferDefaultStartPos[1].addVal(self.startPos[1])
        #initialize update variables variables
        self.reset()
        
        
    #reset update variables
    def reset(self):
        self.bufferCurrPos = self.bufferDefaultStartPos #filled with start position
        self.currPos = self.defaultPos #undistorted
        self.desPos  = self.defaultPos #distorted
        self.outVals= self.defaultPos #distorted
        self.nextPos = self.defaultPos #distorted
        self.outRot = self.computeRotation(self.goalPos,self.startPos)
        self.freeze = True
        self.inVals = [1.0, 1.0]
        
        
    #unfreeze the module
    def unfreeze(self):
        self.freeze = False
        
        
    #input command
    def set(self, val):
        self.inVals = val
        
        
    #output position
    def getPos(self):
        return self.currPos
        
        
    #output rotation
    def getRot(self):
        return self.computeRotation(self.goalPos,self.currPos)
        
        
    #compute the distortion field
    def computeDistortion(self,pos,angle):
        #compute angular deviation of the distorted output location
        pivot = Vec2(pos[0], pos[1])
        return Affine.rotation(angle, pivot)
        
        
    # update function
    def update(self):
        #by default the module is frozen, updated variables are not updated
        if not self.freeze:
        
            if self.controlType == "directionControllerNearRange":
                self.directionControllerNearRange() 
                
            elif self.controlType == "positionControllerNearRange":
                self.positionControllerNearRange() 
                
            elif self.controlType == "positionController":
                self.positionController() 
                
            else:
                self.defaultController()
                
    
    #distance to start
    def getDistStart(self):
        return self.computeDistance(self.currPos,self.startPos)
    
    
    #distance to goal
    def getDistGoal(self):
        return self.computeDistance(self.currPos,self.goalPos)
            
            
    #get current offset of input from start 
    def getDistCommandStart(self):
        return self.computeDistance(self.startPos,self.inVals)
    
    def directionControllerNearRange(self):
        #scaling factor:proportional to the relative distance travelled between start and goal
        scalingFactor = self.computeDistance(self.currPos,self.goalPos) / self.computeDistance(self.startPos,self.goalPos)
        #apply scaling to desired angle
        desAngle = self.angDev * scalingFactor
        #distortion matrix: a rotation around the current position
        distortion = self.computeDistortion(self.currPos,desAngle)
        #desired position: distortion applied to the input command
        desPos =  distortion * self.inVals
        #compute difference between desired and current position
        delta = [desPos[0]-self.currPos[0], desPos[1]-self.currPos[1]]
        #distance between desired and current pos
        distDelta = self.computeDistance(delta,[0.0, 0.0])
        #fix the maximum speed at which turtle travels by..
        #..if non-zero input command
        if distDelta > 0.03:
            #set fixed distance for step input
            fixDistance = 0.1
            #compute a scaling factor 
            sf = fixDistance / distDelta
            #apply scaling factor will result in a fixed distance to travel
            delta = [delta[0] * sf, delta[1] * sf]
        #limit the maximall accepted distance of input command in 0-1 screen coordinates by..
        #.. if beyond the maximum distance
        if distDelta > 0.2:
            #set step command to zero
            delta = [0.0, 0.0]
        #compute next position
        nextPos = [self.currPos[0]+delta[0],self.currPos[1]+delta[1]]
        #set hard limits at the screen boundary
        for i in range(len(nextPos)):
            if nextPos[i]<0.05:
                nextPos[i] = 0.05
            elif nextPos[i]>0.95:
                nextPos[i] = 0.95
        #update current position buffer
        self.updateCurrentPositionBuffer(nextPos)
        
        
    #position controller near range: 
    def positionControllerNearRange(self):
        #distortion matrix: a fixed rotation around the start position
        distortion = self.computeDistortion(self.startPos,self.angDev)
        #desired position: distortion applied to the input command
        desPos =  distortion * self.inVals
        #distance desired position to current position
        desDist = self.computeDistance(desPos,self.currPos)
        #next position command: based on decision made in the remapPos function, including a maximum range criteria
        nextPos = self.remapPos(desPos, self.currPos, desDist, self.maxDist)
        #set hard limits at the screen boundary
        for i in range(len(nextPos)):
            if nextPos[i]<0.05:
                nextPos[i] = 0.05
            elif nextPos[i]>0.95:
                nextPos[i] = 0.95
        #update current position buffer
        self.updateCurrentPositionBuffer(nextPos)
        
        
    #position controller: 
    def positionController(self):
        #distortion matrix: a fixed rotation around the start position
        distortion = self.computeDistortion(self.startPos,self.angDev)
        #desired position: distortion applied to the input command
        desPos =  distortion * self.inVals
        nextPos = [desPos[0], desPos[1]]
        #set hard limits at the screen boundary
        for i in range(len(nextPos)):
            if nextPos[i]<0.05:
                nextPos[i] = 0.05
            elif nextPos[i]>0.95:
                nextPos[i] = 0.95
        #update current position buffer
        self.updateCurrentPositionBuffer(nextPos)
        
        
    #default controller just used the input command to update the buffer current position
    def defaultController(self,inVals):
        nextPos = inVals
        #set hard limits at the screen boundary
        for i in range(len(nextPos)):
            if nextPos[i]<0.05:
                nextPos[i] = 0.05
            elif nextPos[i]>0.95:
                nextPos[i] = 0.95
        self.updateCurrentPositionBuffer(nextPos)
        
        
    #remap desired position to a position closer to the turtle, if desired further than maximum distance
    def remapPos(self,pdes,pcurr,ddes,dmax):
        #if desired distance lower or equal max distance
        if ddes <= dmax:
            #adjusted position equals desired position
            padj = pdes
        #if desired distance larger than max distance
        else:
            #determine distance equivalent to the mirror of the distance to max distance in order to get the same effect on the position update
            dadj = dmax-((ddes-dmax)/2.0)
            #set a zero low cutoff (that is: if the desired distance even further away, just pretend the adjusted position is the current position
            if dadj < 0:
                dadj = 0
            #ratio between adjusted distance and max distance used for weighting (a value between 0 and 1)
            ratio = dadj/dmax
            #ratio = dmax/ddes
            #position difference between desired and current
            pdiff = [pdes[0]-pcurr[0], pdes[1]-pcurr[1]]
            #weighted position difference (by the ratio)
            pdiffWeighted = [pdiff[0]*ratio, pdiff[1]*ratio]
            #compute adjusted position as the sum of current position and the weighted position difference
            padj=[pdiffWeighted[0]+pcurr[0],pdiffWeighted[1]+pcurr[1]]
        #return the adjuste position     
        return padj
    
    
    #update buffer by adding a new position command, then update the current position as the average across the buffer (filtering)
    def updateCurrentPositionBuffer(self,pos):
        #add next position to the buffer (acts as filter)
        self.bufferCurrPos[0].addVal(pos[0])
        self.bufferCurrPos[1].addVal(pos[1])
        #current position: updated as the average across the buffer
        self.currPos[0] = self.bufferCurrPos[0].getAverage()
        self.currPos[1] = self.bufferCurrPos[1].getAverage()
        
        
    #compute distance between two positions
    def computeDistance(self,p1,p2):
        #compute the difference vector
        delta = [p1[0] - p2[0], p1[1] - p2[1]]
        #pythagoras to return the vector length
        return math.sqrt(delta[0]**2 + delta[1]**2)
    
    
    #convert a 2d vector to unit vector (length of one)
    def unit_vector(self, vector):
        return vector / np.linalg.norm(vector)
    
    
    #compute turtle current rotation
    def computeRotation(self,posTarget,posCurr):
        #difference vector from current position to the tartet position
        diffVec = [posTarget[0] - posCurr[0], posTarget[1] - posCurr[1]]
        #upright direction vector
        upVec = (0.0, 1.0)
        #return the angle between difference and upright vectors
        return self.angle_between(diffVec, upVec)
        
        
    # compute the angle in degrees [0-180] between two vectors, negative for lefthand rotation and positive for rightzhand rotation of vector_1 with respect to vector_2
    def angle_between(self, v1, v2):
        #convert to unit vectors (same legnth)
        v1_u = self.unit_vector(v1)
        v2_u = self.unit_vector(v2)
        #compute angle in radians
        rad = np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))   
        #compute angle in degrees
        deg = math.degrees(rad)
        #check direction of rotatation
        if v1_u[0] - v2_u[0] > 0.0:
            deg = -deg
        #ouput
        return deg
        
        