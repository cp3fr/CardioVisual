'''
Python wrapper for HALCA avatar library

@author: Nathan Evans (original XVR: Bernhard Spanlang)
@version: Jan 31, 2011
'''

from platform import system, architecture
from os import environ
from os.path import *
from ctypes import *
from ctypes.util import find_library

class Avatars():    
    lib = None          #HALCA DLL

    '''
    Config input should be a dictionary with keys:
        'dataDir'                --          data directory (string)
        'VA_TRANS'               --          bool
        'DQUAT_TRANSF'           --          bool
    '''
    def __init__(self, config):                
        #Load HALCA dll
        try:
            environ['PATH'] += ';' + abspath(join(dirname(abspath(__file__)), '..', 'lib'))
            if system() == "Windows":
                arch = architecture()[0]
                if(arch == "32bit"):
                    self.lib = cdll.LoadLibrary(find_library('HALCAWin32.dll'))     
                elif(arch == "64bit"):
                    self.lib = cdll.LoadLibrary(find_library('HALCAx64.dll'))
                else:
                    raise RuntimeError("Unsupported architecture: " + arch)    

            else:
                raise RuntimeError("HALCA library is supported only under Windows")    
        except Exception:
            raise RuntimeError("Failed to import HALCA DLL. Ensure it's in the system DLL search path.")

        print "Initializing HALCA with avatar library: " + config['dataDir']
        init = self.lib.initHALCA(c_char_p(config['dataDir']))
        if(init > 0):
            print "Successfully loaded HALCA with avatar library: " + config['dataDir']
        
        #Setup arg types
        self.setupArgTypes()
        
        self.lib.showBB(0);
        self.lib.showSkel(0);
        self.lib.showBody(1);
        
        #Setup shaders
        # 0... Vertex Arrays
        # 1... Transformation Matrices 4x4 16
        # 2... Rotation Matrix and tranlation 3x3+3=12
        # 3... Quaternion and translation 4+3=7
        # 4... exponential quaternion and translation 3+3=6
        # 6... dual quaternion 4+4=8
        if(config['VA_TRANS']):
            self.lib.setTransformType(0)
        
        if(config['DQUAT_TRANSF']):
            self.lib.setTransformType(6)
            logf = POINTER(c_char_p*1024)            #dquat.geom            #@todo: test if works with str ptr
            self.lib.loadShaders("dquat.vert","dquat.geom","dquat.frag",logf)
            print logf

    '''
    Setup function prototypes for python-suppoted type casting/checking 
    '''
    def setupArgTypes(self):
        self.lib.Idle.argtypes = [c_void_p]                                                                 #updates animations
        self.lib.Idle.restype = c_void_p                    
        self.lib.IdleOne.argtypes = [c_int]                                                                 #updates animation of character with AvatarID
        self.lib.IdleOne.restype = c_void_p                                                 
        self.lib.setLocalDir.argtypes = [c_char_p, c_char_p, c_char_p]
        self.lib.setLocalDir.restype = c_void_p                                             
        self.lib.loadShaders.argtypes = [c_char_p, c_char_p, c_char_p, c_char_p]                    #loads fragment geometry and vertex shader and returns shader linker log 
        self.lib.loadShaders.restype = c_int                                          
        self.lib.Draw.argtypes = [c_float]                                                                  #draws all avatars
        self.lib.Draw.restype = c_void_p                            
        self.lib.DrawOne.argtypes = [c_int]                                                                  #draw one avatar given avatarID
        self.lib.DrawOne.restype = c_void_p                            
        self.lib.DrawExtShader.argtypes = [c_void_p]                                                #draws all avatars with External shader
        self.lib.DrawExtShader.restype = c_void_p                            
        self.lib.DrawExtShaderOne.argtypes = [c_int]                                                #draws avatar with the given avatarID using the external shader
        self.lib.DrawExtShaderOne.restype = c_void_p                            
        self.lib.drawBoundsAndSkeleton.argtypes = [c_void_p]                                  #draws skeleton and bounding boxes of all avatars, useful when using external shader
        self.lib.drawBoundsAndSkeleton.restype = c_void_p                            
        self.lib.getProgramID.argtypes = [c_void_p]                                                  #gets the ID of the current shader program
        self.lib.getProgramID.restype = c_int                           
        self.lib.loadUniAndAttrIDs.argtypes = [c_int]                                                  #loads the required uniform and attribute ids of the specified shader program
        self.lib.loadUniAndAttrIDs.restype = c_void_p                           
        self.lib.setDT.argtypes = [c_float]                                                                  #set delta t for animations
        self.lib.setDT.restype = c_void_p                            
        self.lib.setAccumulativeRoot.argtypes = [c_int, c_int]                                      #set root node to accumulate animation changes
        self.lib.setAccumulativeRoot.restype = c_void_p                            
        self.lib.getAnimationDuration.argtypes = [c_int, c_int]                                     #1) AvatarID, 2) AnimationID; returns the duration of the specified animation in sec
        self.lib.getAnimationDuration.restype = c_float                     
        self.lib.getAnimationCount.argtypes = [c_int]                                                  #1) AvatarID, returns the number of animations that the avatar AvatarID has loaded.
        self.lib.getAnimationCount.restype = c_int                            
        self.lib.getAnimationNumFrames.argtypes = [c_int, c_int]
        self.lib.getAnimationNumFrames.restype = c_float
        self.lib.getAnimationFilename.argtypes = [c_int, c_int]                                    #1) AvatarID, 2) AnimationID, returns the filename of the animation specified by AvatarIDn and AnimationID
        self.lib.getAnimationFilename.restype = c_char_p                          
        self.lib.getAnimationName.argtypes = [c_int, c_int]                                         #1) AvatarID, 2) AnimationID, returns the name of the animation specified by AvatarIDn and AnimationID
        self.lib.getAnimationName.restype = c_char_p                          
        self.lib.getAnimationId.argtypes = [c_int, c_char_p]                                        #1) AvatarID, 2) AnimationID, returns the id of the animation specified by AvatarIDn and AnimationName
        self.lib.getAnimationId.restype = c_int                          
        self.lib.getAnimationTime.argtypes = [c_int, c_int]                                           #1) AvatarID, 2) AnimationID, returns the time at which point the specified animation is currently played
        self.lib.getAnimationTime.restype = c_float  
        self.lib.useTextureUnit.argtypes = [c_int]                                                         #specifies the texture Unit that the avatar rendering use for diffues and alpha textures specified in their materials
        self.lib.useTextureUnit.restype = c_void_p   
        self.lib.setDTOne.argtypes = [c_int, c_float]                                                    #1) AvatarId 2)DeltaT, sets deltaT for individual Avatar 
        self.lib.setDTOne.restype = c_void_p     
        self.lib.getDTOne.argtypes = [c_int]                                                                #1) AvatarId, returns currently set DeltaT for this Avatar 
        self.lib.getDTOne.restype = c_float  
        self.lib.ShutDown.argtypes = [c_void_p]                                                          # removes all characters and animations etc.
        self.lib.ShutDown.restype = c_void_p           
        self.lib.exeAct.argtypes = [c_int, c_int, c_float, c_float, c_float, c_int]                # AvatarID, AnimationID, inTime, outTime, weight, lock
        self.lib.exeAct.restype = c_void_p           
        self.lib.exeActAt.argtypes = [c_int, c_int, c_float, c_float, c_float, c_int, c_float]  # AvatarID, AnimationID, inTime, outTime, weight, lock, startTime
        self.lib.exeActAt.restype = c_void_p        
        self.lib.exeActPart.argtypes = [c_int, c_int, c_float, c_float, c_float, c_int, c_float, c_float]  #AvatarID, AnimationID, inTime, outTime, weight, lock, startTime
        self.lib.exeActPart.restype = c_void_p        
        self.lib.removeAct.argtypes = [c_int, c_int]                                                       #AvatarID, AnimationID
        self.lib.removeAct.restype = c_void_p 
        self.lib.isExecuting.argtypes = [c_int, c_int]                                                      #AvatarID, AnimationID
        self.lib.isExecuting.restype = c_int
        self.lib.setCycleAsync.argtypes = [c_int, c_int, c_float]                                     #sets a cycling animation's state to asychronous AvatarID,AnimationID, Delay
        self.lib.setCycleAsync.restype = c_void_p
        self.lib.blendCycle.argtypes = [c_int, c_int, c_float, c_float]                               #Blends in an animation with the parameters:AvatarID, AnimationID,Weight, Delay
        self.lib.blendCycle.restype = c_void_p
        self.lib.blendCycleN.argtypes = [c_int, c_int, c_float, c_float, c_int]                    #Blends in an animation with the parameters:AvatarID, AnimationID,Weight, Delay, number of cycles
        self.lib.blendCycleN.restype = c_void_p
        self.lib.clearCycle.argtypes = [c_int, c_int]                                                       #Removes an Animation from the currently bleded ones with the Parameters: AvatarID, AnimationID
        self.lib.clearCycle.restype = c_void_p 
        self.lib.isCycling.argtypes = [c_int, c_int]                                                         #Returns if the animation with parameres AvatarID, AnimationID is blended in at the moment
        self.lib.isCycling.restype = c_int
        self.lib.setMorph.argtypes = [c_int, c_int, c_float]                                             #sets the animation AnimationID of character AvatarID to morph value
        self.lib.setMorph.restype = c_int
        self.lib.incMorph.argtypes = [c_int, c_int, c_float]                                             #increases the animation AnimationID of character AvatarID by morph value
        self.lib.incMorph.restype = c_int
        self.lib.addMorph.argtypes = [c_int, c_int]                                                        #adds animationID of character AvatarID to Morphable animations.
        self.lib.addMorph.restype = c_int
        self.lib.removeMorph.argtypes = [c_int, c_int]                                                   # removes animationID of character AvatarID from morphable animations
        self.lib.removeMorph.restype = c_int
        self.lib.setModel.argtypes = [c_int]                                                                   # sets an external Cal3D Model to give control to an external application.
        self.lib.setModel.restype = c_int
        self.lib.setWireFrame.argtypes = [c_int, c_int]                                                  #AvatarID, 0/1, renders the character in wireframe. only possible with TransformType VertexArray at the moment
        self.lib.setWireFrame.restype = c_void_p 
        self.lib.setWireFrame.argtypes = [c_int]                                                           #AvatarID, 0/1, renders the character in wireframe. only possible with TransformType VertexArray at the moment
        self.lib.setWireFrame.restype = c_void_p 
        self.lib.showSkel.argtypes = [c_int]                                                                  #visualise all characters' skeletons
        self.lib.showSkel.restype = c_void_p
        self.lib.showBody.argtypes = [c_int]                                                                #visualise all characters' bodies
        self.lib.showBody.restype = c_void_p
        self.lib.showBB.argtypes = [c_int]                                                                   #visualise all characters' bounding boxes
        self.lib.showBB.restype = c_void_p
        self.lib.setRotation.argtypes = [c_int, c_int, POINTER(c_float*4)]                      #AvatarID, JointID, rotation as quaternion
        self.lib.setRotation.restype = c_void_p
        self.lib.setRotationMatrixAbs.argtypes = [c_int, c_int, POINTER(c_float*4)]        #AvatarID, JointID, rotation as quaternion
        self.lib.setRotationMatrixAbs.restype = c_void_p
        self.lib.setRotationAbs.argtypes = [c_int, c_int, POINTER(c_float*4)]                #AvatarID, JointID, rotation as quaternion, rotation is done absolute using parent bones inverse
        self.lib.setRotationAbs.restype = c_void_p
        self.lib.addRotationMatrix.argtypes = [c_int, c_int, POINTER(c_float*9)]            #AvatarID, JointID, rotation as 3x3 matrx, rotation is done taking multiplying with the current rotation
        self.lib.addRotationMatrix.restype = c_void_p
        self.lib.addRotationEuler.argtypes = [c_int, c_int, POINTER(c_float*3)]             #AvatarID, JointID, rotation as Euler angles, rotation is done taking multiplying with the current rotation
        self.lib.addRotationEuler.restype = c_void_p
        self.lib.addRotation.argtypes = [c_int, c_int, POINTER(c_float*4)]                     #AvatarID, JointID, rotation quaternion, rotation is done taking multiplying with the current rotation
        self.lib.addRotation.restype = c_void_p
        self.lib.addRotationAbs.argtypes = [c_int, c_int, POINTER(c_float*4)]               #AvatarID, JointID, rotation quaternion, rotation is done taking multiplying with the current rotation
        self.lib.addRotationAbs.restype = c_void_p
        self.lib.setRotationEuler.argtypes = [c_int, c_int, POINTER(c_float*3)]              #AvatarID, JointID, rotation as Euler
        self.lib.setRotationEuler.restype = c_void_p
        self.lib.setRotationEulerAbs.argtypes = [c_int, c_int, POINTER(c_float*3)]         #AvatarID, JointID, rotation as Euler, rotation is done absolute using parent bones inverse
        self.lib.setRotationEulerAbs.restype = c_void_p
        self.lib.getRotation.argtypes = [c_int, c_int, POINTER(c_float*4)]                      #AvatarID, JointID, relative rotation as quaternion using xyzw
        self.lib.getRotation.restype = c_void_p
        self.lib.getRotationAA.argtypes = [c_int, c_int, POINTER(c_float*3)]                  #AvatarID, JointID, relative rotation as angle axis
        self.lib.getRotationAA.restype = c_void_p
        self.lib.getRotationEuler.argtypes = [c_int, c_int, POINTER(c_float*4)]               #AvatarID, JointID, relative rotation as quaternion using xyzw
        self.lib.getRotationEuler.restype = c_void_p
        self.lib.getRotationAAAbs.argtypes = [c_int, c_int, POINTER(c_float*3)]             #AvatarID, JointID, absolute rotation as angle axis
        self.lib.getRotationAAAbs.restype = c_void_p
        self.lib.getRotationEulerAbs.argtypes = [c_int, c_int, POINTER(c_float*3)]          #AvatarID, JointID, absolute rotation as Euler angle
        self.lib.getRotationEulerAbs.restype = c_void_p
        self.lib.getRotationAbs.argtypes = [c_int, c_int, POINTER(c_float*4)]                 #AvatarID, JointID, absolute rotation as quaternion using xyzw
        self.lib.getRotationAbs.restype = c_void_p
        self.lib.getRotationMatrixAbs.argtypes = [c_int, c_int, POINTER(c_float*9)]         #AvatarID, JointID, absolute rotation as 3x3 rotation Matrix
        self.lib.getRotationMatrixAbs.restype = c_void_p
        self.lib.getBoneBB.argtypes = [c_int, c_int, POINTER(c_float*24)]                     #AvatarID, JointID, 24 vector containing positions of 8 corner points
        self.lib.getBoneBB.restype = c_void_p
        self.lib.updateBoneBB.argtypes = [c_int, c_int, POINTER(c_float*24)]                #AvatarID, JointID, updates the bounding box of the specified bone
        self.lib.updateBoneBB.restype = c_void_p
        self.lib.getBoneName.argtypes = [c_int, c_int]                                                  #AvatarID, JointID, string containing the name of the bone
        self.lib.getBoneName.restype = c_char_p
        self.lib.getBoneChildIds.argtypes = [c_int, c_int]                                               #AvatarID, JointID, string containing the ids of the bone children
        self.lib.getBoneChildIds.restype = c_char_p
        self.lib.getBoneParentId.argtypes = [c_int, c_int]                                               #AvatarID, JointID, int containing bone parentId
        self.lib.getBoneParentId.restype = c_int
        self.lib.isPointInside.argtypes = [c_int, POINTER(c_float*3)]                              #AvatarID, Vec3, returns Joint id of bone that has the position of vec3 inside. if no bone bounding box has it inside -1 is returned
        self.lib.isPointInside.restype = c_int
        self.lib.isPointInsideCyl.argtypes = [c_int, POINTER(c_float*3),c_float]               #AvatarID, Vec3, SphereRadius returns Joint id of bone that has the position of vec3 with radius SpherRadius inside. if no bone bounding cylinder has it inside -1 is returned
        self.lib.isPointInsideCyl.restype = c_int
        self.lib.getBoneBoundingCylinderRadius.argtypes = [c_int, c_int]                       #AvatarID, JointID, returns Returns radius of specified bone -1 if bone or avatarid is invalid.
        self.lib.getBoneBoundingCylinderRadius.restype = c_float
        self.lib.distanceToBoundingCylinder.argtypes = [c_int, c_int]                             #AvatarID, JointID, returns distance between specified bone and point.
        self.lib.distanceToBoundingCylinder.restype = c_float
        self.lib.setModelScale.argtypes = [c_int, POINTER(c_float*3)]                            #AvatarID, Vec3, changes the scale of the avatar.
        self.lib.setModelScale.restype = c_void_p
        self.lib.getModelScale.argtypes = [c_int]                                                           #AvatarID retrieves the current scale of the avatar.
        self.lib.getModelScale.restype =POINTER(c_float*3)
        self.lib.setAllBoneState.argtypes = [c_int, POINTER(c_float*3)]                          #AvatarID, Vec3, changes the scale of the avatar
        self.lib.setAllBoneState.restype = c_void_p
        self.lib.getAllBoneState.argtypes = [c_int, POINTER(c_float*3)]                          #AvatarID retrieves the current scale of the avatar.
        self.lib.getAllBoneState.restype = c_void_p
        self.lib.getRotationAAbs.argtypes = [c_int, c_int, POINTER(c_float*3)]                #AvatarID, JointID, bone space rotation as angle axis
        self.lib.getRotationAAbs.restype = c_void_p
        self.lib.lookAt.argtypes = [c_int, c_int, POINTER(c_float*3), POINTER(c_float*3)] #AvatarID, JointID, from Vec3, to Vec3
        self.lib.lookAt.restype = c_void_p
        self.lib.getBoneId.argtypes = [c_int, c_char_p]                                                  #AvatarID, substring of bone name, returns boneID
        self.lib.getBoneId.restype = c_int
        self.lib.getInverseParentRotation.argtypes = [c_int, c_int, POINTER(c_float*9)]    #AvatarID, boneId, returns 3x3 transposed matrix of absolute parent rotation
        self.lib.getInverseParentRotation.restype = c_void_p
        self.lib.setTranslation.argtypes = [c_int, c_int, POINTER(c_float*3)]                    #ttranslate bone: 1) avatarID, 2)bone ID, 3) float array xyz
        self.lib.setTranslation.restype = c_void_p
        self.lib.getTranslation.argtypes = [c_int, c_int, POINTER(c_float*3)]                    #gets the translation with the parameters: AvatarID, JointID, get relative translation Vec3
        self.lib.getTranslation.restype = c_void_p
        self.lib.getTranslationAbs.argtypes = [c_int, c_int, POINTER(c_float*3)]              #gets the translation with the parameters: AvatarID, JointID, get abs translation Vec3
        self.lib.getTranslationAbs.restype = c_void_p
        self.lib.getTranslationOGL.argtypes = [c_int, c_int, POINTER(c_float*3)]             #AvatarID, JointID, get relative translation Vec3 OpenGL space
        self.lib.getTranslationOGL.restype = c_void_p
        self.lib.getTranslationAbsOGL.argtypes = [c_int, c_int, POINTER(c_float*3)]        #AvatarID, JointID, get absolute translation Vec3 OpenGL space
        self.lib.getTranslationAbsOGL.restype = c_void_p
        self.lib.getNumBone.argtypes = [c_int]                                                              #Returns the number of bones if the Avatar with AvatarID
        self.lib.getNumBone.restype = c_int
        self.lib.numCharacters.argtypes = [c_void_p]                                                    #returns number of avatars loaded in library
        self.lib.numCharacters.restype = c_int
        self.lib.loadAnimation.argtypes = [c_int, c_char_p]                                            #loads an animation to AvatarID with the filename specified
        self.lib.loadAnimation.restype = c_int
        self.lib.setTransformType.argtypes = [c_int]                                                      #which type of transformations is sent to the GPU ? 0 Vertex Array, 1 Matrix, 2 rotmat&transmat, 3 Quaternion, encoded quaternion?
        self.lib.setTransformType.restype = c_void_p        
        self.lib.addCharacter.argtypes = [c_char_p, c_char_p]                                     #adds a new character;1) parameter dir, 2) cfg name
        self.lib.addCharacter.restype = c_int
        self.lib.exeMorph.argtypes = [c_int, c_int, c_float, c_float]                                 #Executes a morph animation AvatarID, MorphID,seconds,delay
        self.lib.exeMorph.restype = c_void_p
        self.lib.clearMorph.argtypes = [c_int, c_int, c_float]                                          #Removes a morph animation AvatarID, MorphID,delay
        self.lib.clearMorph.restype = c_void_p
        self.lib.loadEnvMap.argtypes = [c_char_p]                                                       #loads an environment map that can be used in shaders to render characters
        self.lib.loadEnvMap.restype = c_void_p        
        self.lib.DrawGrid.argtypes = [c_void_p]                                                            #draws a grid for debugging purpose.
        self.lib.DrawGrid.restype = c_void_p        
        self.lib.doIK.argtypes = [c_int, c_int, c_int, POINTER(c_float*3), c_float, c_int]   #Inverse Kinematics with parameters: AvatarID, startBoneId, endBoneId, targetPos, tolerance, iterations
        self.lib.doIK.restype = c_void_p
        self.lib.PointAt.argtypes = [c_int, c_int, POINTER(c_float*3)]                             #PointAt behaviour with the parameters: AvatarID, startBoneId, targetPos
        self.lib.PointAt.restype = c_void_p
        self.lib.ogreLookAt.argtypes = [c_int, c_int, POINTER(c_float*3), c_int]              #LookAt Behaviour with the paramteres: AvatarID, startBoneId, targetPos, opposite direction(0/1)
        self.lib.ogreLookAt.restype = c_void_p
        self.lib.setUpIK3.argtypes = [c_int, c_int, c_int, POINTER(c_float*3), c_float, c_int] #Setup Inverse Kinematics from Maya with the paramters: AvatarID, startBoneId, endBoneId, targetPos, tolerance, iterations
        self.lib.setUpIK3.restype = c_void_p
        self.lib.doIK3.argtypes = [c_int, c_int, c_int, POINTER(c_float*3), c_float, c_int]   #Setup Inverse Kinematics from Maya with the paramters: AvatarID, startBoneId, endBoneId, targetPos, tolerance, iterations
        self.lib.doIK3.restype = c_void_p
        self.lib.doIKCCD.argtypes = [c_int, c_int, c_int, POINTER(c_float*3), c_float, c_int]   #Inverse Kinematics  using ICCD with the paramters: AvatarID, startBoneId, endBoneId, targetPos, tolerance, iterations
        self.lib.doIKCCD.restype = c_void_p
        self.lib.lockBone.argtypes = [c_int, c_int]                                                           #AvatarID, JointID, locks the bone so that it can be edited manually
        self.lib.lockBone.restype = c_void_p
        self.lib.resetBone.argtypes = [c_int, c_int]                                                          #Removes all previous influence to the bone and resets it to the original transformation specified in the skeleton.
        self.lib.resetBone.restype = c_void_p
        self.lib.FileOpen.argtypes = [c_char_p]                                                              #open a file
        self.lib.FileOpen.restype = c_int
        self.lib.FileWrite.argtypes = [c_char_p]                                                              #open a file
        self.lib.FileWrite.restype = c_void_p
        self.lib.FileClose.argtypes = [c_void_p]                                                              #close a file
        self.lib.FileClose.restype = c_void_p
        self.lib.writeFrameAsJpeg.argtypes = [c_char_p, c_int]                                      # FIlename, imagequality, writes the current OpenGL framebuffer to a jpg image with given filename and quality
        self.lib.writeFrameAsJpeg.restype = c_void_p


    def cleanup(self):
        # clean up HALCA        
        if self.controller.gModuleList.has_key('avatarlib'):
            HALCA.ShutDown(None)
