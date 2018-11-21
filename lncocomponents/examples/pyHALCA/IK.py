'''
Full body inverse kinematics

@author: Nathan Evans  (adapted/ported from Bernhard Spanlang)
@version 15 Feb 2011
'''

from quaternion import *
import numpy as np
from ctypes import *


class IK():

    def __init__(self,aID,lib):
        self.avatarID = aID           # Storing interesting ids: avatar and bones
        self.HALCA = lib              # ref to HALCA instance 
        
        self.OGL = True
        self.OGLQuat = createQuaternionAxisAngle([1,0,0],np.pi/2.0)
        
        self.bodyPos = {}           #Body Part label -> Position (3 vector) dictionary
        self.boneIDs = {}           #bone label -> ID dictionary
        
        #Arm Constants
        self.ArmLength = 0
        self.RElbowAddAngle = 0.0               # Angles for elbows additional rotations
        self.LElbowAddAngle = 0.0
        
        #Upper body constants
        self.SpineLength = 0.0
        self.UpperBodyIK = False                 #target for UP IK
        
        #Leg constants
        self.LegLength = 0

        self._setupArmIK()
        self._setupUpperBodyIK()
        self._setupLowerBodyIK()
        

        
    def _setupArmIK(self):
        """
            Setup arm inverse kinematics
        """
        # Declare positions/quaternions
        self.bodyPos['LArmShoulderPos'] = cvecf([0,0,0])
        self.bodyPos['LArmElbowPos'] = cvecf([0,0,0])
        self.bodyPos['LArmHandPos'] = cvecf([0,0,0])

        self.bodyPos['RArmShoulderPos'] = cvecf([0,0,0])
        self.bodyPos['RArmElbowPos'] = cvecf([0,0,0])
        self.bodyPos['RArmHandPos'] = cvecf([0,0,0])

        self.bodyPos['RArmTarget'] = cvecf([0,0,0])
        self.bodyPos['LArmTarget'] = cvecf([0,0,0])
        self.bodyPos['RArmPrevTarget'] = cvecf([0,0,0])
        self.bodyPos['LArmPrevTarget'] = cvecf([0,0,0])
        self.bodyPos['RElbowTargetVec'] = cvecf([0,0,0])          
        self.bodyPos['LElbowTargetVec'] = cvecf([0,0,0])                
                        
        #Qauaternions
        self.bodyPos['RArmQuat'] = cvecf([0,0,0,0])
        self.bodyPos['LArmQuat'] = cvecf([0,0,0,0])
        self.bodyPos['RShoulderRotAbs'] = cvecf([0,0,0,0])
        self.bodyPos['LShoulderRotAbs'] = cvecf([0,0,0,0])
        
        self.bodyPos['RShoulderQuat'] = cvecf([0,0,0,0])
        self.bodyPos['RElbowQuat'] = cvecf([0,0,0,0])
        self.bodyPos['LShoulderQuat'] = cvecf([0,0,0,0])
        self.bodyPos['LElbowQuat'] = cvecf([0,0,0,0])

        
        #Map bone labels -> ids
        self.boneIDs['AvatarBipID'] = self.HALCA.getBoneId(self.avatarID,"Bip")
        self.boneIDs['AvatarHeadID'] = self.HALCA.getBoneId(self.avatarID,"Head")
        self.boneIDs['AvatarHeadNubID'] = self.HALCA.getBoneId(self.avatarID,"HeadNub")
        self.boneIDs['AvatarLUpperArmID'] = self.HALCA.getBoneId(self.avatarID,"L UpperArm")
        self.boneIDs['AvatarLForeArmID'] = self.HALCA.getBoneId(self.avatarID,"L Forearm")
        self.boneIDs['AvatarLHandID'] = self.HALCA.getBoneId(self.avatarID,"L Hand")
        self.boneIDs['AvatarRUpperArmID'] = self.HALCA.getBoneId(self.avatarID,"R UpperArm")
        self.boneIDs['AvatarRForeArmID'] = self.HALCA.getBoneId(self.avatarID,"R Forearm")
        self.boneIDs['AvatarRHandID'] = self.HALCA.getBoneId(self.avatarID,"R Hand")
        
        #Reset bones to T pose
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarHeadID'])
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarHeadNubID'])
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarRUpperArmID'])
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarRForeArmID'])
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarRHandID'])

        # Compute the head to headNub vector that will represent
        # the vector around which the shoulder bone will be turned
        self.bodyPos['AvatarHeadPos'] = cvecf([0,0,0])
        self.bodyPos['AvatarHeadNubPos'] = cvecf([0,0,0])
        self.bodyPos['shouldersUpVec'] = cvecf([0,0,0])
        
        self.HALCA.getTranslationAbs(self.avatarID, self.boneIDs['AvatarHeadID'],byref(self.bodyPos['AvatarHeadPos']))
        self.HALCA.getTranslationAbs(self.avatarID, self.boneIDs['AvatarHeadNubID'],byref(self.bodyPos['AvatarHeadNubPos']))
        self.bodyPos['shouldersUpVec'] = norm(np.subtract(self.bodyPos['AvatarHeadNubPos'],self.bodyPos['AvatarHeadPos']))
    
        # Compute the length of the arm (which is constant)
        self.bodyPos['RArmHandPos'] = cvecf([0,0,0])
        self.bodyPos['RArmShoulderPos'] = cvecf([0,0,0])
        self.bodyPos['RArmElbowPos'] = cvecf([0,0,0])

        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarRHandID'],byref(self.bodyPos['RArmHandPos']))
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarRUpperArmID'],byref(self.bodyPos['RArmShoulderPos']))
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarRForeArmID'],byref(self.bodyPos['RArmElbowPos']))

        # Computing vectors
        RElbowHandVec = np.subtract(self.bodyPos['RArmHandPos'],self.bodyPos['RArmElbowPos'])
        RShoulderElbowVec = np.subtract(self.bodyPos['RArmElbowPos'],self.bodyPos['RArmShoulderPos'])

        # Arm length (is computed only once because static)
        self.ArmLength = modulus(RShoulderElbowVec) + modulus(RElbowHandVec)
        

    def _setupUpperBodyIK(self):
        """
            Setup upper body inverse kinematics
        """

        # Declare positions/quaternions
        self.bodyPos['Spine0Pos'] = cvecf([0,0,0])
        self.bodyPos['Spine1Pos'] = cvecf([0,0,0])
        self.bodyPos['Spine2Pos'] = cvecf([0,0,0])
        self.bodyPos['Spine3Pos'] = cvecf([0,0,0])
        self.bodyPos['HeadTarget'] = cvecf([0,0,0])
                        
        #Qauaternions
        self.bodyPos['SpineQuat'] = cvecf([0,0,0,0])
        self.bodyPos['Spine1RotAbs'] = cvecf([0,0,0,0])        
        self.bodyPos['Spine2RotAbs'] = cvecf([0,0,0,0])
        self.bodyPos['Spine3RotAbs'] = cvecf([0,0,0,0])
        
        #Map bone labels -> ids
        self.boneIDs['AvatarSpine0ID'] = self.HALCA.getBoneId(self.avatarID,"Spine")
        self.boneIDs['AvatarSpine1ID'] = self.HALCA.getBoneId(self.avatarID,"Spine1")
        self.boneIDs['AvatarSpine2ID'] = self.HALCA.getBoneId(self.avatarID,"Spine2")
        self.boneIDs['AvatarSpine3ID'] = self.HALCA.getBoneId(self.avatarID,"Spine3")
        
        #Reset bones to T pose
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarSpine0ID'])
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarSpine1ID'])
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarSpine2ID'])
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarSpine3ID'])

        # Compute length of spine (which is constant)
        self.HALCA.getTranslationAbs(self.avatarID, self.boneIDs['AvatarSpine0ID'],byref(self.bodyPos['Spine0Pos']))
        self.HALCA.getTranslationAbs(self.avatarID, self.boneIDs['AvatarSpine1ID'],byref(self.bodyPos['Spine1Pos']))
        self.HALCA.getTranslationAbs(self.avatarID, self.boneIDs['AvatarSpine2ID'],byref(self.bodyPos['Spine2Pos']))
        self.HALCA.getTranslationAbs(self.avatarID, self.boneIDs['AvatarSpine3ID'],byref(self.bodyPos['Spine3Pos']))

        OrigSpineDir = np.subtract(self.bodyPos['Spine3Pos'],self.bodyPos['Spine0Pos'])
        self.SpineLength = modulus(OrigSpineDir)
        
        # Default to no Head target
        UpperBodyIK = False


    def _setupLowerBodyIK(self):
        """
            Setup lower body (legs) inverse kinematics
        """
        
        # Declare positions/quaternions
#        self.bodyPos['RThighTargetVec'] = cvecf([0,0,0])
#        self.bodyPos['LThighTargetVec'] = cvecf([0,0,0])
#        self.bodyPos['RCalfFootVec'] = cvecf([0,0,0])
#        self.bodyPos['LCalfFootVec'] = cvecf([0,0,0])
#        self.bodyPos['RThighCalfVec'] = cvecf([0,0,0])
#        self.bodyPos['LThighCalfVec'] = cvecf([0,0,0])

        self.bodyPos['LLegThighPos'] = cvecf([0,0,0])
        self.bodyPos['LLegCalfPos'] = cvecf([0,0,0])
        self.bodyPos['LLegFootPos'] = cvecf([0,0,0])
        self.bodyPos['LLegToePos'] = cvecf([0,0,0])
        self.bodyPos['LLegToeNubPos'] = cvecf([0,0,0])
        
        self.bodyPos['RLegThighPos'] = cvecf([0,0,0])
        self.bodyPos['RLegCalfPos'] = cvecf([0,0,0])
        self.bodyPos['RLegFootPos'] = cvecf([0,0,0])
        self.bodyPos['RLegToePos'] = cvecf([0,0,0])
        self.bodyPos['RLegToeNubPos'] = cvecf([0,0,0])
            
        #Qauaternions
        self.bodyPos['RLegQuat'] = cvecf([0,0,0,0])
        self.bodyPos['LLegQuat'] = cvecf([0,0,0,0])
        self.bodyPos['RThighRotAbs'] = cvecf([0,0,0,0])
        self.bodyPos['LThighRotAbs'] = cvecf([0,0,0,0])
        self.bodyPos['RThighQuat'] = cvecf([0,0,0,0])
        self.bodyPos['RCalfQuat'] = cvecf([0,0,0,0])
        self.bodyPos['LThighQuat'] = cvecf([0,0,0,0])
        self.bodyPos['LCalfQuat'] = cvecf([0,0,0,0])

        
        #Map bone labels -> ids
        self.boneIDs['AvatarLThighID'] = self.HALCA.getBoneId(self.avatarID,"L Thigh")
        self.boneIDs['AvatarLCalfID'] = self.HALCA.getBoneId(self.avatarID,"L Calf")
        self.boneIDs['AvatarLFootID'] = self.HALCA.getBoneId(self.avatarID,"L Foot")
        self.boneIDs['AvatarLToeID'] = self.HALCA.getBoneId(self.avatarID,"L Toe0")
        self.boneIDs['AvatarLToeNubID'] = self.HALCA.getBoneId(self.avatarID,"L Toe0Nub")

        self.boneIDs['AvatarRThighID'] = self.HALCA.getBoneId(self.avatarID,"R Thigh")
        self.boneIDs['AvatarRCalfID'] = self.HALCA.getBoneId(self.avatarID,"R Calf")
        self.boneIDs['AvatarRFootID'] = self.HALCA.getBoneId(self.avatarID,"R Foot")
        self.boneIDs['AvatarRToeID'] = self.HALCA.getBoneId(self.avatarID,"R Toe0")
        self.boneIDs['AvatarRToeNubID'] = self.HALCA.getBoneId(self.avatarID,"R Toe0Nub")
                            
        # Resetting bones to T pose
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarRThighID'])
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarRCalfID'])
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarRFootID'])

        # Computing the length of the leg (which is constant across legs)                                                
        self.HALCA.getTranslationAbs(self.avatarID, self.boneIDs['AvatarRFootID'],byref(self.bodyPos['RLegFootPos']))
        self.HALCA.getTranslationAbs(self.avatarID, self.boneIDs['AvatarRThighID'],byref(self.bodyPos['RLegThighPos']))
        self.HALCA.getTranslationAbs(self.avatarID, self.boneIDs['AvatarRCalfID'],byref(self.bodyPos['RLegCalfPos']))
                
        RCalfFootVec = np.subtract(self.bodyPos['RLegFootPos'],self.bodyPos['RLegCalfPos'])
        RThighCalfVec = np.subtract(self.bodyPos['RLegCalfPos'],self.bodyPos['RLegThighPos'])
        
        self.LegLength = modulus(RThighCalfVec) + modulus(RCalfFootVec)


    def doIK(self,aIK,bIK,lIK):
        '''
        Peform inverse kinematics.
        
        Inputs:
            bool aIK             # do arms IK
            bool bIK             # do body IK
            bool lIK             # do legs IK        
        '''
        # Rotation if OGL avatar
        if not self.OGL:
            self.HALCA.addRotationAbs(self.avatarID,self.boneIDs['AvatarBipID'],self.OGLQuat)
        
        # Arms
        if(aIK):
            self._doLArmIK()
            self._doRArmIK()
             
        # Upper/Mid Body
        if(bIK):
            self._doUpperBodyIK()
       
        # Legs
        if(lIK):
            self._doRLegIK()
            self._doLLegIK() 


    def _doRArmIK(self):
        #Resetting bones to T pose
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarRUpperArmID'])
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarRForeArmID'])

        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarRHandID'],byref(self.bodyPos['RArmHandPos']))
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarRUpperArmID'],byref(self.bodyPos['RArmShoulderPos']))
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarRForeArmID'],byref(self.bodyPos['RArmElbowPos']))

        # Computing vectors
        origRArmDir = np.subtract(self.bodyPos['RArmHandPos'], self.bodyPos['RArmShoulderPos'])
        RShoulderTargetVec = np.subtract(self.bodyPos['RArmTarget'], self.bodyPos['RArmShoulderPos'])
        RElbowHandVec = np.subtract(self.bodyPos['RArmHandPos'], self.bodyPos['RArmElbowPos'])
        RShoulderElbowVec = np.subtract(self.bodyPos['RArmElbowPos'], self.bodyPos['RArmShoulderPos'])
        
        # Distance from shoulder to target
        RDistance = modulus(RShoulderTargetVec)
            
        # Angles and rotations computation        
        # Quaternion between original Arm direction and shoulder to target vector
        # i.e RArmQuat rotates the arm so that it points towards the target
        self.bodyPos['RArmQuat'] = getRotationTo(origRArmDir,RShoulderTargetVec)
        self.bodyPos['RArmQuat'] = normalizeQuaternion(self.bodyPos['RArmQuat'])

        # Getting current rotations
        self.HALCA.getRotationAbs(self.avatarID, self.boneIDs['AvatarRUpperArmID'], byref(self.bodyPos['RShoulderRotAbs']))
    
        # If the distance to the target is smaller than the length if the arm then we need to bend
        if( RDistance < self.ArmLength ): ## <= ??
            # Computing the angle between shoulder and elbow 
            # for a point within reach of the arm
            RShoulderElbowLength = modulus(RShoulderElbowVec)
            RElbowHandLength = modulus(RElbowHandVec)
    
            # According to the function computeAngleFromTriangle (see above)
            # the distance c has to be rElbowHandLength because we want to compute the angle 
            # for the shoulder (i.e. between rDistance and rShoulderElbowLength)
            shoulderAngle = self._computeAngleFromTriangle(RDistance,RShoulderElbowLength,RElbowHandLength)
                    
            # This quaternion is for the rotation of the shoulder 
            # when the target is within reach distance
            self.bodyPos['RShoulderQuat'] = createQuaternionAxisAngle(self.bodyPos['shouldersUpVec'],shoulderAngle) 
            self.bodyPos['RShoulderQuat'] = normalizeQuaternion(self.bodyPos['RShoulderQuat'])
            self.bodyPos['RShoulderQuat'] = conjugateQuaternion(self.bodyPos['RShoulderQuat'])
        
            # What we need to do is to apply the quaternion that orientates the arm towards the target
            self.bodyPos['RArmQuat'] = normalizeQuaternion(self.bodyPos['RArmQuat'])
            self.bodyPos['RArmQuat'] = conjugateQuaternion(self.bodyPos['RArmQuat'])
            self.bodyPos['RArmQuat'] = composeQuaternions(self.bodyPos['RArmQuat'],self.bodyPos['RShoulderRotAbs'])            
            self.bodyPos['RArmQuat'] = composeQuaternions(self.bodyPos['RArmQuat'],self.bodyPos['RShoulderQuat']) 
            self.bodyPos['RArmQuat'] = normalizeQuaternion(self.bodyPos['RArmQuat'])
            
            self.HALCA.setRotationAbs(self.avatarID,self.boneIDs['AvatarRUpperArmID'],byref(cvecf(self.bodyPos['RArmQuat'])))
            
            # We have just rotated the shoulder => Now we need to bend the elbow so that it points to the TARGET        
            # Retrieving the current elbow rotation quaternion
            elbowCurRot = cvecf([0,0,0,1])
            self.HALCA.getRotationAbs(self.avatarID,self.boneIDs['AvatarRForeArmID'], byref(elbowCurRot))
            
            # We need to get the "new" positions of elbow and hand since we just have rotated the shoulder
            elbowPos = cvecf([0,0,0])
            self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarRForeArmID'], byref(elbowPos))
            handpos = cvecf([0,0,0])
            self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarRHandID'], byref(handpos))
            
            elbowHandCurVec = np.subtract(handpos,elbowPos)                      # the "new" elbow to hand vector
            elbowTargetCurVec = np.subtract(self.bodyPos['RArmTarget'],elbowPos) # the "new" elbow to target vector (since the arm has been rotated)
            
            # Computing the elbow quaternion : rotation from current vector to desired one
            elbowRotQuat = getRotationTo(elbowHandCurVec,elbowTargetCurVec)
            
            # Elbow Rotation Test
            addQuat = self._additionalRightElbowRotation()
            addQuat2 = addQuat
            elbowRotQuat = composeQuaternions(elbowRotQuat,addQuat)
            
            # conjugate the quaternion and normalizing it
            elbowRotQuat = conjugateQuaternion(elbowRotQuat)
            elbowRotQuat = normalizeQuaternion(elbowRotQuat)
            
            # Finally we combined it with the current elbow rotation
            self.bodyPos['RElbowQuat'] = composeQuaternions(elbowRotQuat,elbowCurRot)
            self.bodyPos['RElbowQuat'] = normalizeQuaternion(self.bodyPos['RElbowQuat'])
            
            self.HALCA.setRotationAbs(self.avatarID,self.boneIDs['AvatarRForeArmID'],byref(cvecf(self.bodyPos['RElbowQuat'])))
            
            ######
            # WRIST
            # Test to combine it with the wrist now
            # Retrieving the current wrist rotation quaternion
#            wristCurRot = cvecf([0,0,0,1])
#            self.HALCA.getRotationAbs(self.avatarID,self.boneIDs['AvatarRHandID'], byref(wristCurRot))
#            wristQuat = addQuat2
#            #wristQuat.w*=3;
#            
#            # conjugate the quaternion and normalizing it
#            wristQuat = conjugateQuaternion(wristQuat)
#            wristQuat = normalizeQuaternion(wristQuat)
#            
#            # Finally we combined it with the current elbow rotation
#            wristQuat = composeQuaternions(wristQuat,wristCurRot)
#            wristQuat = normalizeQuaternion(wristQuat)
#            
#            self.HALCA.setRotationAbs(self.avatarID,self.boneIDs['AvatarRHandID'],byref(cvecf(wristQuat)))

        else:
            self.bodyPos['RArmQuat'] = normalizeQuaternion(self.bodyPos['RArmQuat'])
            self.bodyPos['RArmQuat'] = conjugateQuaternion(self.bodyPos['RArmQuat'])            
            self.bodyPos['RArmQuat'] = composeQuaternions(self.bodyPos['RArmQuat'],self.bodyPos['RShoulderRotAbs'])
            self.bodyPos['RArmQuat'] = normalizeQuaternion(self.bodyPos['RArmQuat'])
            
            self.HALCA.setRotationAbs(self.avatarID,self.boneIDs['AvatarRUpperArmID'],byref(cvecf(self.bodyPos['RArmQuat'])))

                    
            #####
            # Extras
            # Elbow Rotation Test
#            elbowCurRot = cvecf([0,0,0,1])
#            self.HALCA.getRotationAbs(self.avatarID,self.boneIDs['AvatarRForeArmID'], byref(elbowCurRot))
#
#            # Additional rotation
#            addQuat = self._additionalRightElbowRotation()
#            wristQuat = addQuat
#            # conjugate the quaternion and normalizing it
#            addQuat = conjugateQuaternion(addQuat)
#            addQuat = normalizeQuaternion(addQuat)
#            
#            # Finally we combined it with the current elbow rotation
#            addQuat = composeQuaternions(addQuat,elbowCurRot)
#            addQuat = normalizeQuaternion(addQuat)
#            
#            self.HALCA.setRotationAbs(self.avatarID,self.boneIDs['AvatarRForeArmID'],byref(cvecf(addQuat)))
#            
#            # Test to combine it with the wrist now
#            # Retrieving the current wrist rotation quaternion
#            wristCurRot = cvecf([0,0,0,1])
#            self.HALCA.getRotationAbs(self.avatarID,self.boneIDs['AvatarRHandID'], byref(wristCurRot))
#            #wristQuat.w*=3;
#            
#            # conjugate the quaternion and normalizing it
#            wristQuat = conjugateQuaternion(wristQuat)
#            wristQuat = normalizeQuaternion(wristQuat)
#            
#            # Finally we combined it with the current elbow rotation
#            wristQuat = composeQuaternions(wristQuat,wristCurRot)
#            wristQuat = normalizeQuaternion(wristQuat)
#            
#            self.HALCA.setRotationAbs(self.avatarID,self.boneIDs['AvatarRHandID'],byref(cvecf(wristQuat)))
        
    
    def _doLArmIK(self):            
        # Resetting bones to T pose
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarLUpperArmID'])
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarLForeArmID'])
    
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarLHandID'],byref(self.bodyPos['LArmHandPos']))
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarLUpperArmID'],byref(self.bodyPos['LArmShoulderPos']))
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarLForeArmID'],byref(self.bodyPos['LArmElbowPos']))
        
        # Computing vectors
        origLArmDir = np.subtract(self.bodyPos['LArmHandPos'], self.bodyPos['LArmShoulderPos'])
        LShoulderTargetVec = np.subtract(self.bodyPos['LArmTarget'], self.bodyPos['LArmShoulderPos'])
        LElbowHandVec = np.subtract(self.bodyPos['LArmHandPos'], self.bodyPos['LArmElbowPos'])
        LShoulderElbowVec = np.subtract(self.bodyPos['LArmElbowPos'], self.bodyPos['LArmShoulderPos'])
        
        # Distance from shoulder to target
        LDistance = modulus(LShoulderTargetVec)
                
        # Angles and rotations computation        
        # Quaternion between original Arm direction and shoulder to target vector
        # i.e LArmQuat rotates the arm so that it points towards the target
        self.bodyPos['LArmQuat'] = getRotationTo(origLArmDir,LShoulderTargetVec)
        self.bodyPos['LArmQuat'] = normalizeQuaternion(self.bodyPos['LArmQuat'])
        
        # Getting current rotations
        self.HALCA.getRotationAbs(self.avatarID, self.boneIDs['AvatarLUpperArmID'], byref(self.bodyPos['LShoulderRotAbs']))
    
    
        # If the distance to the target is smaller than the length if the arm then we need to bend
        if( LDistance < self.ArmLength ): # <= ??        
            # Computing the angle between shoulder and elbow 
            # for a point within reach of the arm
            LShoulderElbowLength = modulus(LShoulderElbowVec)
            LElbowHandLength = modulus(LElbowHandVec)    
            
            # According to the function computeAngleFromTriangle (see above)
            # the distance c has to be LElbowHandLength because we want to compute the angle 
            # for the shoulder (i.e. between LDistance and LShoulderElbowLength)
            shoulderAngle = self._computeAngleFromTriangle(LDistance,LShoulderElbowLength,LElbowHandLength)
            
            # This quaternion is for the rotation of the shoulder 
            # when the target is within reach distance
            self.bodyPos['LShoulderQuat'] = createQuaternionAxisAngle(self.bodyPos['shouldersUpVec'],shoulderAngle) 
            self.bodyPos['LShoulderQuat'] = normalizeQuaternion(self.bodyPos['LShoulderQuat'])
            self.bodyPos['LShoulderQuat'] = conjugateQuaternion(self.bodyPos['LShoulderQuat'])
                    
            # What we need to do is to apply the quaternion that orientates the arm towards the target
            self.bodyPos['LArmQuat'] = normalizeQuaternion(self.bodyPos['LArmQuat'])
            self.bodyPos['LArmQuat'] = conjugateQuaternion(self.bodyPos['LArmQuat'])
            self.bodyPos['LArmQuat'] = composeQuaternions(self.bodyPos['LArmQuat'],self.bodyPos['LShoulderRotAbs'])            
            self.bodyPos['LArmQuat'] = composeQuaternions(self.bodyPos['LArmQuat'],self.bodyPos['LShoulderQuat']) 
            self.bodyPos['LArmQuat'] = normalizeQuaternion(self.bodyPos['LArmQuat'])
                        
            self.HALCA.setRotationAbs(self.avatarID,self.boneIDs['AvatarLUpperArmID'],byref(cvecf(self.bodyPos['LArmQuat'])))
            
            # We have just rotated the shoulder => Now we need to bend the elbow so that it points to the TARGET        
            # Retrieving the current elbow rotation quaternion
            elbowCurRot = cvecf([0,0,0,1])
            self.HALCA.getRotationAbs(self.avatarID,self.boneIDs['AvatarLForeArmID'], byref(elbowCurRot))
                        
            # We need to get the "new" positions of elbow and hand since we just have rotated the shoulder
            elbowPos = cvecf([0,0,0])
            self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarLForeArmID'], byref(elbowPos))
            handpos = cvecf([0,0,0])
            self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarLHandID'], byref(handpos))
            
            # computing the "new" elbow to hand vector
            # computing the "new" elbow to target vector (since the arm has been rotated)
            elbowHandCurVec = np.subtract(handpos,elbowPos)                      # the "new" elbow to hand vector
            elbowTargetCurVec = np.subtract(self.bodyPos['LArmTarget'],elbowPos) # the "new" elbow to target vector (since the arm has been rotated)
            
            # Computing the elbow quaternion : rotation from current vector to desired one
            elbowRotQuat = getRotationTo(elbowHandCurVec,elbowTargetCurVec)
           

            #### Additional constraints
            ##  Elbow Rotation Test
            #addQuat = self._additionalLeftElbowRotation()
            #elbowRotQuat = composeQuaternions(elbowRotQuat,addQuat)
            
            # conjugate the quaternion and normalizing it
            elbowRotQuat = conjugateQuaternion(elbowRotQuat)
            elbowRotQuat = normalizeQuaternion(elbowRotQuat)
            
            # Finally we combined it with the current elbow rotation
            self.bodyPos['LElbowQuat'] = composeQuaternions(elbowRotQuat,elbowCurRot)
            self.bodyPos['LElbowQuat'] = normalizeQuaternion(self.bodyPos['LElbowQuat'])
            
            self.HALCA.setRotationAbs(self.avatarID,self.boneIDs['AvatarLForeArmID'],byref(cvecf(self.bodyPos['LElbowQuat'])))
                    
        else:            
            # No arm bend
            self.bodyPos['LArmQuat'] = normalizeQuaternion(self.bodyPos['LArmQuat'])            
            self.bodyPos['LArmQuat'] = conjugateQuaternion(self.bodyPos['LArmQuat'])            
            self.bodyPos['LArmQuat'] = composeQuaternions(self.bodyPos['LArmQuat'],self.bodyPos['LShoulderRotAbs'])
            self.bodyPos['LArmQuat'] = normalizeQuaternion(self.bodyPos['LArmQuat'])
            
            self.HALCA.setRotationAbs(self.avatarID,self.boneIDs['AvatarLUpperArmID'],byref(cvecf(self.bodyPos['LArmQuat'])))

        
    def _doUpperBodyIK(self):
        # Resetting bones to T pose
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarSpine0ID'])
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarSpine1ID'])
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarSpine2ID'])
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarSpine3ID'])
        
        # Retrieving positions
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarSpine0ID'],byref(self.bodyPos['Spine0Pos']))
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarSpine1ID'],byref(self.bodyPos['Spine1Pos']))
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarSpine2ID'],byref(self.bodyPos['Spine2Pos']))
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarSpine3ID'],byref(self.bodyPos['Spine3Pos']))
    
        FakeHead = cvecf([0,0,0])
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarHeadID'],byref(FakeHead))
        
        # Computing vectors
        OrigSpineDir = np.subtract(self.bodyPos['Spine3Pos'],self.bodyPos['Spine0Pos'])
        self.SpineLength = modulus(OrigSpineDir)         # Distance from shoulder to target       
        OrigSpineDir = norm(OrigSpineDir)
        
        # Target Computation
        if(self.UpperBodyIK):
            SpineTargetDir = np.subtract(self.bodyPos['HeadTarget'],self.bodyPos['Spine0Pos'])
        else:
            SpineTargetDir = np.subtract(FakeHead,self.bodyPos['Spine0Pos'])
        
        SpineTargetDir = norm(SpineTargetDir)
        
        # Quaternion between original Arm direction and shoulder to target vector
        # i.e RArmQuat rotates the arm so that it points towards the target
        self.bodyPos['SpineQuat'] = getRotationTo(OrigSpineDir,SpineTargetDir)
        self.bodyPos['SpineQuat'] = np.divide(self.bodyPos['SpineQuat'],3.0)         # Spread the quaternion on the 3 Spine bones
        self.bodyPos['SpineQuat'] = normalizeQuaternion(self.bodyPos['SpineQuat'])
        self.bodyPos['SpineQuat'] = conjugateQuaternion(self.bodyPos['SpineQuat'])
        
        # Getting current rotations
        self.HALCA.getRotationAbs(self.avatarID,self.boneIDs['AvatarSpine1ID'], byref(self.bodyPos['Spine1RotAbs']))
        self.HALCA.getRotationAbs(self.avatarID,self.boneIDs['AvatarSpine2ID'], byref(self.bodyPos['Spine2RotAbs']))
        self.HALCA.getRotationAbs(self.avatarID,self.boneIDs['AvatarSpine3ID'], byref(self.bodyPos['Spine3RotAbs']))
    

        # Compose
        spine1FinalQuat = composeQuaternions(self.bodyPos['SpineQuat'],self.bodyPos['Spine1RotAbs'])
        spine1FinalQuat = normalizeQuaternion(spine1FinalQuat)
        spine2FinalQuat = composeQuaternions(self.bodyPos['SpineQuat'],self.bodyPos['Spine2RotAbs'])
        spine2FinalQuat = normalizeQuaternion(spine2FinalQuat)
        spine3FinalQuat = composeQuaternions(self.bodyPos['SpineQuat'],self.bodyPos['Spine3RotAbs'])
        spine3FinalQuat = normalizeQuaternion(spine3FinalQuat)
    
        # Set new rotations
        self.HALCA.setRotationAbs(self.avatarID,self.boneIDs['AvatarSpine1ID'],byref(cvecf(spine1FinalQuat)))
        self.HALCA.setRotationAbs(self.avatarID,self.boneIDs['AvatarSpine2ID'],byref(cvecf(spine2FinalQuat)))
        self.HALCA.setRotationAbs(self.avatarID,self.boneIDs['AvatarSpine3ID'],byref(cvecf(spine3FinalQuat)))
    
    
    
    def _doRLegIK(self):
        # Resetting bones to T pose
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarRThighID'])
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarRCalfID'])
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarRFootID'])
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarRToeID'])
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarRToeNubID'])
        
        # Retrieving positions
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarRFootID'],byref(self.bodyPos['RLegFootPos']))
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarRThighID'],byref(self.bodyPos['RLegThighPos']))        
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarRCalfID'],byref(self.bodyPos['RLegCalfPos']))
    
        # Foot orientation
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarRToeID'],byref(self.bodyPos['RLegToePos']))
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarRToeNubID'],byref(self.bodyPos['RLegToeNubPos']))
    
        # Computing vectors
        origRLegDir = np.subtract(self.bodyPos['RLegFootPos'],self.bodyPos['RLegThighPos'])
        RThighTargetVec = np.subtract(self.bodyPos['RLegTarget'],self.bodyPos['RLegThighPos'])
        RCalfFootVec = np.subtract(self.bodyPos['RLegFootPos'],self.bodyPos['RLegCalfPos'])
        RThighCalfVec = np.subtract(self.bodyPos['RLegCalfPos'],self.bodyPos['RLegThighPos'])
        
        # Distance from thigh to target
        RDistance = modulus(RThighTargetVec)
            
        # Angles and rotations computation        
        # Quaternion between original Arm direction and shoulder to target vector
        # i.e RArmQuat rotates the arm so that it points towards the target
        self.bodyPos['RLegQuat'] = getRotationTo(origRLegDir,RThighTargetVec)
        self.bodyPos['RLegQuat'] = normalizeQuaternion(self.bodyPos['RLegQuat'])
        
        # Getting current rotations
        self.HALCA.getRotationAbs(self.avatarID, self.boneIDs['AvatarRThighID'], byref(self.bodyPos['RThighRotAbs']))

        # If the distance to the target is smaller than the length if the arm then we need to bend
        if( RDistance < self.LegLength ): # <= ??
            # Computing the angle between shoulder and elbow for a point within reach of the arm
            RThighCalfLength = modulus(RThighCalfVec)
            RCalfFootLength = modulus(RCalfFootVec)
    
            # According to the function computeAngleFromTriangle (see above)
            # the distance c has to be RThighCalfLength because we want to compute the angle 
            # for the shoulder (i.e. between rDistance and RThighCalfLength)
            thighAngle = self._computeAngleFromTriangle(RDistance,RThighCalfLength,RCalfFootLength)
                    
            # This quaternion is for the rotation of the thigh when the target is within reach distance
            self.bodyPos['RThighQuat'] = createQuaternionAxisAngle(self.bodyPos['shouldersUpVec'],thighAngle)
            self.bodyPos['RThighQuat'] = normalizeQuaternion(self.bodyPos['RThighQuat'])
            self.bodyPos['RThighQuat'] = conjugateQuaternion(self.bodyPos['RThighQuat'])
        
            # What we need to do is to apply the quaternion that orientates the leg towards the target
            self.bodyPos['RLegQuat'] = normalizeQuaternion(self.bodyPos['RLegQuat'])
            self.bodyPos['RLegQuat'] = conjugateQuaternion(self.bodyPos['RLegQuat'])
            self.bodyPos['RLegQuat'] = composeQuaternions(self.bodyPos['RLegQuat'],self.bodyPos['RThighRotAbs'])
            self.bodyPos['RLegQuat'] = composeQuaternions(self.bodyPos['RLegQuat'],self.bodyPos['RThighQuat'])
            self.bodyPos['RLegQuat'] = normalizeQuaternion(self.bodyPos['RLegQuat'])
            
            self.HALCA.setRotationAbs(self.avatarID,self.boneIDs['AvatarRThighID'],byref(cvecf(self.bodyPos['RLegQuat'])))
            
            # We have just rotated the thigh => Now we need to
            # bend the calf so that it points to the TARGET
            calfCurRot = [0,0,0,1]
            calfPos = [0,0,0]
            footpos = [0,0,0]
            self.HALCA.getRotationAbs(self.avatarID,self.boneIDs['AvatarRCalfID'], byref(cvecf(calfCurRot)))
            self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarRCalfID'],byref(cvecf(calfPos)))
            self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarRCalfID'], byref(cvecf(footpos)))

            # computing the "new" calf to foot vector
            calfFootCurVec = np.subtract(footpos,calfPos)
            calfTargetCurVec = np.subtract(self.bodyPos['RLegTarget'],calfPos)
            
            calfRotQuat = getRotationTo(calfFootCurVec,calfTargetCurVec)         
            calfRotQuat = conjugateQuaternion(calfRotQuat)
            calfRotQuat = normalizeQuaternion(calfRotQuat)            
            
            self.bodyPos['RCalfQuat'] = composeQuaternions(calfRotQuat,calfCurRot)
            self.bodyPos['RCalfQuat'] = normalizeQuaternion(self.bodyPos['RCalfQuat'])
            
            self.HALCA.setRotationAbs(self.avatarID,self.boneIDs['AvatarRCalfID'],byref(cvecf(self.bodyPos['RCalfQuat'])))
        
        else:
            self.bodyPos['RLegQuat'] = normalizeQuaternion(self.bodyPos['RLegQuat'])
            self.bodyPos['RLegQuat'] = conjugateQuaternion(self.bodyPos['RLegQuat'])            
            self.bodyPos['RLegQuat'] = composeQuaternions(self.bodyPos['RLegQuat'],self.bodyPos['RThighRotAbs'])
            self.bodyPos['RLegQuat'] = normalizeQuaternion(self.bodyPos['RLegQuat'])
            
            self.HALCA.setRotationAbs(self.avatarID,self.boneIDs['AvatarRThighID'],byref(cvecf(self.bodyPos['RLegQuat'])))
        
        
        # Aligning foot to Z plane
        toeNubPos = [0,0,0]
        toePos = [0,0,0]
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarRToeNubID'],byref(cvecf(toeNubPos)))
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarRToeID'],byref(cvecf(toePos)))
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarRFootID'],byref(cvecf(self.bodyPos['RLegFootPos'])))

        footToeVec = norm(np.subtract(toeNubPos,toePos)) #RLegFootPos);
        footTarVec = norm(np.subtract(self.bodyPos['RLegToeNubPos'],self.bodyPos['RLegToePos']))   #[0,0,1];#Norm(RLegTarget - RLegFootPos);#
        footQuat = getRotationTo(footToeVec,footTarVec)
        
        # conjugate the quaternion and normalize it
        footQuat = conjugateQuaternion(footQuat)
        footQuat = normalizeQuaternion(footQuat)
        
        # Getting current rotations
        curRFootQuat = cvecf([0,0,0,0])
        self.HALCA.getRotationAbs(self.avatarID,self.boneIDs['AvatarRFootID'], byref(curRFootQuat))
    
        # Finally we combined it with the current elbow rotation
        footQuat = composeQuaternions(footQuat,curRFootQuat)
        footQuat = normalizeQuaternion(footQuat)
        self.HALCA.setRotationAbs(self.avatarID,self.boneIDs['AvatarRFootID'],byref(cvecf(footQuat)))

    
    
    def _doLLegIK(self):
        # Resetting bones to T pose
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarLThighID'])
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarLCalfID'])
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarLFootID'])
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarLToeID'])
        self.HALCA.resetBone(self.avatarID,self.boneIDs['AvatarLToeNubID'])
    
        # Retrieving positions
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarLFootID'],byref(self.bodyPos['LLegFootPos']))
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarLThighID'],byref(self.bodyPos['LLegThighPos']))        
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarLCalfID'],byref(self.bodyPos['LLegCalfPos']))
    
        # Foot orientation
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarLToeID'],byref(self.bodyPos['LLegToePos']))
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarLToeNubID'],byref(self.bodyPos['LLegToeNubPos']))
    
    
        # Computing vectors
        origLLegDir = np.subtract(self.bodyPos['LLegFootPos'],self.bodyPos['LLegThighPos'])
        LThighTargetVec = np.subtract(self.bodyPos['LLegTarget'],self.bodyPos['LLegThighPos'])
        LCalfFootVec = np.subtract(self.bodyPos['LLegFootPos'],self.bodyPos['LLegCalfPos'])
        LThighCalfVec = np.subtract(self.bodyPos['LLegCalfPos'],self.bodyPos['LLegThighPos'])
                
        # Distance from thigh to target
        LDistance = modulus(LThighTargetVec)
            
        # Angles and rotations computation        
        # Quaternion between original Arm direction and shoulder to target vector
        # i.e RArmQuat rotates the arm so that it points towards the target
        self.bodyPos['LLegQuat'] = getRotationTo(origLLegDir,LThighTargetVec)
        self.bodyPos['LLegQuat'] = normalizeQuaternion(self.bodyPos['LLegQuat'])
        
        # Getting current rotations
        self.HALCA.getRotationAbs(self.avatarID, self.boneIDs['AvatarLThighID'], byref(self.bodyPos['LThighRotAbs']))
                
        # If the distance to the target is smaller than the length if the arm then we need to bend
        if( LDistance < self.LegLength ): # <= ??
            # Computing the angle between shoulder and elbow for a point within reach of the arm
            LThighCalfLength = modulus(LThighCalfVec)
            LCalfFootLength = modulus(LCalfFootVec)
    
            # According to the function computeAngleFromTriangle (see above)
            # the distance c has to be RThighCalfLength because we want to compute the angle 
            # for the shoulder (i.e. between rDistance and RThighCalfLength)
            thighAngle = self._computeAngleFromTriangle(LDistance,LThighCalfLength,LCalfFootLength)
                    
            # This quaternion is for the rotation of the thigh when the target is within reach distance
            self.bodyPos['LThighQuat'] = createQuaternionAxisAngle(self.bodyPos['shouldersUpVec'],thighAngle)
            self.bodyPos['LThighQuat'] = normalizeQuaternion(self.bodyPos['LThighQuat'])
            self.bodyPos['LThighQuat'] = conjugateQuaternion(self.bodyPos['LThighQuat'])

            # What we need to do is to apply the quaternion that orientates the leg towards the target
            self.bodyPos['LLegQuat'] = normalizeQuaternion(self.bodyPos['LLegQuat'])
            self.bodyPos['LLegQuat'] = conjugateQuaternion(self.bodyPos['LLegQuat'])
            self.bodyPos['LLegQuat'] = composeQuaternions(self.bodyPos['LLegQuat'],self.bodyPos['LThighRotAbs'])
            self.bodyPos['LLegQuat'] = composeQuaternions(self.bodyPos['LLegQuat'],self.bodyPos['LThighQuat'])
            self.bodyPos['LLegQuat'] = normalizeQuaternion(self.bodyPos['LLegQuat'])
            
            self.HALCA.setRotationAbs(self.avatarID,self.boneIDs['AvatarLThighID'],byref(cvecf(self.bodyPos['LLegQuat'])))
 
            # We have just rotated the thigh => Now we need to
            # bend the calf so that it points to the TARGET
            calfCurRot = [0,0,0,1]
            calfPos = [0,0,0]
            footpos = [0,0,0]
            self.HALCA.getRotationAbs(self.avatarID,self.boneIDs['AvatarLCalfID'], byref(cvecf(calfCurRot)))
            self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarLCalfID'],byref(cvecf(calfPos)))
            self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarLCalfID'], byref(cvecf(footpos)))

            # computing the "new" calf to foot vector
            calfFootCurVec = np.subtract(footpos,calfPos)
            calfTargetCurVec = np.subtract(self.bodyPos['LLegTarget'],calfPos)
            
            calfRotQuat = getRotationTo(calfFootCurVec,calfTargetCurVec)         
            calfRotQuat = conjugateQuaternion(calfRotQuat)
            calfRotQuat = normalizeQuaternion(calfRotQuat)            
            
            self.bodyPos['LCalfQuat'] = composeQuaternions(calfRotQuat,calfCurRot)
            self.bodyPos['LCalfQuat'] = normalizeQuaternion(self.bodyPos['LCalfQuat'])
            
            self.HALCA.setRotationAbs(self.avatarID,self.boneIDs['AvatarLCalfID'],byref(cvecf(self.bodyPos['LCalfQuat'])))
        
        else:
            self.bodyPos['LLegQuat'] = normalizeQuaternion(self.bodyPos['LLegQuat'])
            self.bodyPos['LLegQuat'] = conjugateQuaternion(self.bodyPos['LLegQuat'])            
            self.bodyPos['LLegQuat'] = composeQuaternions(self.bodyPos['LLegQuat'],self.bodyPos['LThighRotAbs'])
            self.bodyPos['LLegQuat'] = normalizeQuaternion(self.bodyPos['LLegQuat'])
            
            self.HALCA.setRotationAbs(self.avatarID,self.boneIDs['AvatarLThighID'],byref(cvecf(self.bodyPos['LLegQuat'])))        
                            

        # Aligning foot to Z plane
        toeNubPos = [0,0,0]
        toePos = [0,0,0]
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarLToeNubID'],byref(cvecf(toeNubPos)))
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarLToeID'],byref(cvecf(toePos)))
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarLFootID'],byref(cvecf(self.bodyPos['LLegFootPos'])))

        footToeVec = norm(np.subtract(toeNubPos,toePos)) #RLegFootPos);
        footTarVec = norm(np.subtract(self.bodyPos['LLegToeNubPos'],self.bodyPos['LLegToePos']))   #[0,0,1];#Norm(RLegTarget - RLegFootPos);#
        footQuat = getRotationTo(footToeVec,footTarVec)
        
        # conjugate the quaternion and normalize it
        footQuat = conjugateQuaternion(footQuat)
        footQuat = normalizeQuaternion(footQuat)
        
        # Getting current rotations
        curLFootQuat = cvecf([0,0,0,0])
        self.HALCA.getRotationAbs(self.avatarID,self.boneIDs['AvatarLFootID'], byref(curLFootQuat))
    
        # Finally we combined it with the current elbow rotation
        footQuat = composeQuaternions(footQuat,curLFootQuat)
        footQuat = normalizeQuaternion(footQuat)
        self.HALCA.setRotationAbs(self.avatarID,self.boneIDs['AvatarLFootID'],byref(cvecf(footQuat)))    
        
    
    def incrRightElbowAngle(self,angle):
        self.RElbowAddAngle += angle
        if(self.RElbowAddAngle>(np.pi)):
            self.RElbowAddAngle =(np.pi)
        if(self.RElbowAddAngle<(-np.pi)):
            self.RElbowAddAngle = -np.pi
    
    def incrLeftElbowAngle(self,angle):
        self.LElbowAddAngle += angle
        if(self.LElbowAddAngle>(np.pi/2.0)):
            self.LElbowAddAngle = np.pi/2.0
        if(self.LElbowAddAngle<(-PI/2.0)):
            self.LElbowAddAngle=-PI/2.0


    def _additionalRightElbowRotation(self):
        if(self.RElbowAddAngle == 0.0):
            return [0,0,0,1]
    
        # Rotate the elbow so that its local UP is pointing up (meaning shoulder UP)
        pos = cvecf([0,0,0])
        self.HALCA.getTranslationAbs(self.avatarID,self.boneIDs['AvatarRForeArmID'],byref(pos))
        self.bodyPos['RElbowTargetVec'] = norm(np.subtract(self.bodyPos['RArmTarget'],pos))
        elbowQuat = createQuaternionAxisAngle(self.bodyPos['RElbowTargetVec'],self.RElbowAddAngle/2.0); 
        # /4.0 because rotation is divided between elbow (1/4) and wrist (3/4)
        
        # Normalize the quaternion
        elbowQuat = normalizeQuaternion(elbowQuat)
        
        return elbowQuat
      
    def _additionalLeftElbowRotation(self):
        if(self.LElbowAddAngle == 0.0):
            return [0,0,0,1]
            
        # Rotate the elbow so that its local UP is pointing up (meaning shoulder UP)
        elbowX = [0,0,0]
        elbowY = [0,0,0]
        elbowZ = [0,0,0]
        elbowMat = cvecf(0,0,0,0,0,0,0,0,0)
        # Getting the rotation Matrix of the elbow
        self.HALCA.getRotationMatrixAbs(self.avatarID,self.boneIDs['AvatarLForeArmID'],byref(elbowMat))
        # Getting XYZ axes
        elbowX[0] = elbowMat[0]
        elbowX[1] = elbowMat[3]
        elbowX[2] = elbowMat[6]
        elbowY[0] = elbowMat[1]
        elbowY[1] = elbowMat[4]
        elbowY[2] = elbowMat[7]
        elbowZ[0] = elbowMat[2]
        elbowZ[1] = elbowMat[5]
        elbowZ[2] = elbowMat[8]
            
        elbowQuat = createQuaternionAxisAngle(elbowZ,self.LElbowAddAngle)
        elbowQuat = normalizeQuaternion(elbowQuat)
        
        return elbowQuat


    # Constraints
 
    def _alignLeftElbowUp(self):
        # Rotate the elbow so that its local UP is pointing up (meaning shoulder UP)
        elbowX = [0,0,0]
        elbowY = [0,0,0]
        elbowZ = [0,0,0]
        elbowMat = cvecf(0,0,0,0,0,0,0,0,0)
        # Getting the rotation Matrix of the elbow
        self.HALCA.getRotationMatrixAbs(self.avatarID,self.boneIDs['AvatarLForeArmID'],byref(elbowMat))
        # Getting XYZ axes
        elbowX[0] = elbowMat[0]
        elbowX[1] = elbowMat[3]
        elbowX[2] = elbowMat[6]
        elbowY[0] = elbowMat[1]
        elbowY[1] = elbowMat[4]
        elbowY[2] = elbowMat[7]
        elbowZ[0] = elbowMat[2]
        elbowZ[1] = elbowMat[5]
        elbowZ[2] = elbowMat[8]
                
        self.bodyPos['LElbowTargetVec'] = norm(np.subtract(self.bodyPos['LArmTarget'],self.bodyPos['LArmElbowPos']))
        elbowQuat = getRotationTo(elbowY,self.bodyPos['shouldersUpVec'])
        elbowQuat = conjugateQuaternion(elbowQuat)
        elbowQuat = normalizeQuaternion(elbowQuat)
        
        # Getting current rotations
        curLElbowQuat = cvecf([0,0,0,0])
        self.HALCA.getRotationAbs(self.avatarID,self.boneIDs['AvatarLForeArmID'], byref(curLElbowQuat))
    
        # Finally we combined it with the current elbow rotation
        elbowQuat = composeQuaternions(elbowQuat,curLElbowQuat);
        elbowQuat = normalizeQuaternion(elbowQuat)
            
        self.HALCA.setRotationAbs(self.avatarID,self.boneIDs['AvatarLForeArmID'],elbowQuat)


    def _alignRightElbowUp(self):
        # Rotate the elbow so that its local UP is pointing up (meaning shoulder UP)
        elbowX = [0,0,0]
        elbowY = [0,0,0]
        elbowZ = [0,0,0]
        elbowMat = cvecf(0,0,0,0,0,0,0,0,0)
        # Getting the rotation Matrix of the elbow
        self.HALCA.getRotationMatrixAbs(self.avatarID,self.boneIDs['AvatarRHandID'],byref(elbowMat))
        # Getting XYZ axes
        elbowX[0] = elbowMat[0]
        elbowX[1] = elbowMat[3]
        elbowX[2] = elbowMat[6]
        elbowY[0] = elbowMat[1]
        elbowY[1] = elbowMat[4]
        elbowY[2] = elbowMat[7]
        elbowZ[0] = elbowMat[2]
        elbowZ[1] = elbowMat[5]
        elbowZ[2] = elbowMat[8]
                
        self.bodyPos['RElbowTargetVec'] = np.subract(self.bodyPos['RElbowTargetVec'],self.bodyPos['RArmElbowPos'])
        
        elbowQuat = createQuaternionAxisAngle(elbowX,np.pi/2.0)
        elbowQuat = conjugateQuaternion(elbowQuat)
        elbowQuat = normalizeQuaternion(elbowQuat)
        
        # Getting current rotations
        curRElbowQuat = cvecf([0,0,0,0])
        self.HALCA.getRotationAbs(self.avatarID,self.boneIDs['AvatarRHandID'], byref(curRElbowQuat))
    
        # Finally we combined it with the current elbow rotation
        elbowQuat = composeQuaternions(elbowQuat,curRElbowQuat)
        elbowQuat = normalizeQuaternion(elbowQuat)
            
        self.HALCA.setRotationAbs(self.avatarID,self.boneIDs['AvatarRHandID'],elbowQuat)





    # OGL parameter

    def setOGL(self,value):
        self.OGL = value
    
    def setRightArmTarget(self,pos):
        self.bodyPos['RArmTarget'] = pos

    def setRightArmPos(self,pos):
        self.bodyPos['RArmTarget'] = pos

    def setLeftArmTarget(self,pos):
        self.bodyPos['LArmTarget'] = pos

    def setLeftArmPos(self,pos):
        self.bodyPos['LArmTarget'] = pos
        
    def useHeadTarget(self,boolValue):
        self.UpperBodyIK = boolValue    

    def setHeadTarget(self,pos):
        self.bodyPos['HeadTarget'] = pos
        self.UpperBodyIK = True
    
    def setHeadPos(self,pos):
        self.bodyPos['HeadTarget'] = pos
        self.UpperBodyIK = True
        
    def setRightLegTarget(self,pos):
        self.bodyPos['RLegTarget'] = pos
    
    def setRightLegPos(self,pos):
        self.bodyPos['RLegTarget'] = pos

    def setLeftLegTarget(self,pos):
        self.bodyPos['LLegTarget'] = pos
    
    def setLeftLegPos(self,pos):
        self.bodyPos['LLegTarget'] = pos
            
    def _computeAngleFromTriangle(self,a,b,c):
        ''' 
        Triangle angle computation
           The triangle ABC is defined by a,b,c the lengths of its sides.
           c is the side opposite of the angle "alpha" we want to compute
           and a and b are the sides that form the angle "alpha".
           We have c^2 = a^2 + b^2 - 2ab*cos("alpha")
           so alpha = arccos( (a^2+b^2-c^2)/ (2ab) )
         
           Beware: order IS important!
             cf. http:#en.wikipedia.org/wiki/Law_of_cosines

            /*
            # This is law of sines
            var p             = (a+b+c)/2.0; # Heron's formula
            var S            = sqrt( p*(p-a)*(p-b)*(p-c) );
            var fixedPart    = a*b*c/(2*S);
            
            var alpha2        = - asin(a/fixedPart); # Shoulderangle
            outputln("Sines: ",alpha2);*/
        '''            
        cosineLaw = (a*a+b*b-c*c)/(2*a*b)
        if(cosineLaw > 1.0):
            cosineLaw = 1.0
        if(cosineLaw < -1.0):
            cosineLaw = -1.0
        alpha = np.arccos( cosineLaw )

        return alpha


#Helper functions
def cvecf(args):
    return (c_float * len(args))(*args)

def cveci(args):
    return (c_int * len(args))(*args)
