'''
Library of functions to deal with Quaternions

@author: Nathan Evans  (adapted/ported from Bernhard Spanlang)
@version: 19 October 2010
'''
import array
import numpy as np

_EPSILON = 0.0001

#Gets the norm of a quaterion
def getQuaternionNorm(quat):
    return np.sqrt(quat[0]*quat[0] + 
                     quat[1]*quat[1] + 
                     quat[2]*quat[2] + 
                     quat[3]*quat[3])

# Gets the unit quaternion from quat
def normalizeQuaternion(quat):
    qnorm = getQuaternionNorm(quat) 
    if qnorm == 0:   
        qnorm = 1       #fix divide by zero if zero length vector 
    res = [quat[0]/qnorm, quat[1]/qnorm, quat[2]/qnorm, quat[3]/qnorm]

    for i in range(len(res)):
        if(abs(res[i]) < _EPSILON):
            res[i] = 0.0
            
    return res

def conjugateQuaternion(quat):
    conj = [-quat[0], -quat[1], -quat[2], quat[3]]
    return conj

'''compose 2 quaternion rotations. first, q1 and then q2. returns q2*q1'''
def composeQuaternions(q1,q2):
    s1 = q1[3]
    s2 = q2[3]
    
    v1 = np.array(q1[0:3])
    v2 = np.array(q2[0:3])
    
    s12 = s2*s1 - np.dot(v1,v2)
    v12 = np.add(s1*v2,s2*v1)
    v12 = np.add(v12,np.cross(v2,v1))
    
    return [v12[0], v12[1], v12[2], s12]

''' Jim Multiplication
     An optimization can also be made by rearranging to
        w = w1w2 - x1x2 - y1y2 - z1z2
        x = w1x2 + x1w2 + y1z2 - z1y2
        y = w1y2 + y1w2 + z1x2 - x1z2
        z = w1z2 + z1w2 + x1y2 - y1x2 

     Bernie's one
      w = qw * q.w - qx * q.x - qy * q.y - qz * q.z; OK
      x = qw * q.x + qx * q.w + qy * q.z - qz * q.y; OK
      y = qw * q.y - qx * q.z + qy * q.w + qz * q.x; OK
      z = qw * q.z + qx * q.y - qy * q.x + qz * q.w; OK

'''
def MultiplyQuaternions(quat1, quat2):
    result = [0,0,0,0]
    result[3] = quat1[3]*quat2[3] - quat1[0]*quat2[0] - quat1[1]*quat2[1] - quat1[2]*quat2[2]
    result[0] = quat1[3]*quat2[0] + quat1[0]*quat2[3] + quat1[1]*quat2[2] - quat1[2]*quat2[1]
    result[1] = quat1[3]*quat2[1] + quat1[1]*quat2[3] + quat1[2]*quat2[0] - quat1[0]*quat2[2]
    result[2] = quat1[3]*quat2[2] + quat1[2]*quat2[3] + quat1[0]*quat2[1] - quat1[1]*quat2[0]

    return result

''' How do I convert a rotation axis and angle to a quaternion?
     
     Given a rotation axis and angle, the following
     algorithm may be used to generate a quaternion:

        vector_normalize(axis);
        sin_a = sin( angle / 2 );
        cos_a = cos( angle / 2 );
        X    = axis -> x * sin_a;
        Y    = axis -> y * sin_a;
        Z    = axis -> z * sin_a;
        W    = cos_a;
    
      It is necessary to normalise the quaternion in case any values are 
      very close to zero.


    Compute the rotation quaternion given one angle in radians and one vector '''
def createQuaternionAxisAngle(vec,angle):
    s = np.cos(angle/2.0)
    u = np.array(vec)
    v = np.sin(angle/2.0) * u
    #normalizeQuat([v[0], v[1], v[2], s])
    return normalizeQuaternion([v[0], v[1], v[2], s]) #note: was without normalize

'''
 Axis and angle from Quaternion
    How do I convert a quaternion to a rotation axis and angle?

      A quaternion can be converted back to a rotation axis and angle
      using the following algorithm:
 
        quaternion_normalise( |X,Y,Z,W| );
        cos_a = W;
        angle = acos( cos_a ) * 2;
        sin_a = sqrt( 1.0 - cos_a * cos_a );
        if ( fabs( sin_a ) < 0.0005 ) sin_a = 1;
        axis -> x = X / sin_a;
        axis -> y = Y / sin_a;
        axis -> z = Z / sin_a; '''
def AxisAngleFromQuaternion(quat):
    normQuat = normalizeQuaternion(quat);
    cos_a = normQuat[3]
    angle = np.acos(cos_a)*2.0
    sin_a = np.sqrt( 1.0 - (cos_a*cos_a))
    if( np.fabs(sin_a) < 0.0005): 
        sin_a = 1.0
    
    x = normQuat[0] / sin_a;
    y = normQuat[1] / sin_a;
    z = normQuat[2] / sin_a;

    return [x,y,z,angle]


'''
def AxisAngleMinusPiPiFromQuat( quat ):
    normQuat = normalizeQuat(quat)
    cos_a = normQuat[3]
    angle = np.acos(cos_a)*2.0
    
    while(angle > np.pi)
        angle -= 2*np.pi
    
    while(angle < -np.pi)
        angle += 2*np.pi
    
    sin_a = np.sqrt( 1.0 - (cos_a*cos_a))
    if( np.fabs(sin_a) < 0.0005):
        sin_a = 1.0
    
    x = normQuat[0] / sin_a
    y = normQuat[1] / sin_a
    z = normQuat[2] / sin_a
    
    return [x,y,z,angle]
}
'''


''' Takes a 3D point and rotates it by the quaternion quat '''
def rotatePointByQuaternion(point,quat):
    unitQuat = normalizeQuaternion(quat)
    conjQuat = [-unitQuat[0], -unitQuat[1], -unitQuat[2], unitQuat[3]]
    quatPoint = [point[0], point[1], point[2], 1]

    result = composeQuaternions(unitQuat, quatPoint)
    result = composeQuaternions(result, conjQuat)

    return result


'''
// Rotates a vector by a rotation
    How do I use quaternions to rotate a vector?

      A rather elegant way to rotate a vector using a quaternion directly
      is the following (qr being the rotation quaternion):
                           -1
           v' = qr * v * qr

  This can easily be realised and is most likely faster then the transformation
  using a rotation matrix. '''
def RotateVectorByQuaternion(vec,quat):
    quaternizedVec = [vec[0],vec[1],vec[2],0]
    conj = conjugateQuaternion(quat)
    result = MultiplyQuaternions(quat,quaternizedVec)
    result = MultiplyQuaternions(result,conj)
    
    return result


''' Transform a given point rotating it by 3 angles '''
def rotatePointByAngles( point, ax, ay, az ):
    quatX = createQuaternionAxisAngle( [1.0, 0.0, 0.0], ax )
    quatY = createQuaternionAxisAngle( [0.0, 1.0, 0.0], ay )
    quatZ = createQuaternionAxisAngle( [0.0, 0.0, 1.0], az )

    finalQuaternion = composeQuaternions( quatX, quatY)
    finalQuaternion = composeQuaternions( finalQuaternion, quatZ)

    return rotatePointByQuaternion( point, finalQuaternion )

''' From Ogre3D
    const Vector3& fallbackAxis = Vector3::ZERO) 
    - Based on Stan Melax's article in Game Programming Gems
    '''
def getRotationTo(vecTo, vecDest):
    q = [0,0,0,0]
    fromVec = np.array(norm(vecTo))          # Copy, since cannot modify local
    to = np.array(norm(vecDest))
    d = np.dot(fromVec,to)
    
    #If dot == 1, vectors are the same
    if(d >= 1.0):
        return [0,0,0,1]  #Identity Quaternion

    #if dot == 0
    
    if (d < (1e-6 - 1.0)):
        #Generate an axis
        xAxis = np.array([1,0,0])
        yAxis = np.array([0,1,0])
        axis = np.cross(xAxis,vecTo)
        if(np.modf(axis) < _EPSILON):      #pick another if colinear
            axis = np.cross(yAxis,vecTo)
        axis = norm(axis)
        q = createQuaternionAxisAngle(axis,np.pi)
    else:
        s = np.sqrt( (1+d)*2 )
        invs = 1/s

        c = np.cross(fromVec,to)
                
        q[0] = c[0] * invs
        q[1] = c[1] * invs
        q[2] = c[2] * invs
        q[3] = s * 0.5
        q = normalizeQuaternion(q)
        
    return q


def norm(vec):
    len = np.sqrt(vec[0]*vec[0] + vec[1]*vec[1] + vec[2]*vec[2])
    return [vec[0]/len, vec[1]/len, vec[2]/len]

def modulus(vec):
    return np.sqrt(vec[0]*vec[0] + vec[1]*vec[1] + vec[2]*vec[2])

#Helper functions
def cvecf(args):
    return (c_float * len(args))(*args)

def cveci(args):
    
    return (c_int * len(args))(*args)