from pyglet.gl import GLfloat, GLint
import numpy as np
import math        

def vecf(*args):
    return (GLfloat * len(args))(*args)
    
def vec3f(l):
    return (GLfloat * 3)(l[0], l[1], l[2])

def vec4f(l):
    return (GLfloat * 4)(l[0], l[1], l[2], l[3])

def vec2f(l):
    return (GLfloat * 2)(l[0], l[1])

def veci(*args):
    return (GLint * len(args))(*args)
    
    
def rot(angle, u):
    """
    Return rotation matrix around axis defined by angle and direction.
    """    
    s = np.sin(angle)
    c = np.cos(angle)
    u = unitVector(u)
    r = np.eye(3)*c
    
    # Rodrigues formula
    r += np.outer(u, u) * (1.0 - c)
    r += s*np.array((( 0.0 ,-u[2],  u[1]),
                   ( u[2], 0.0 , -u[0]),
                   (-u[1], u[0],  0.0)),
                     dtype=np.float64)
    return r


def rot_(theta):
    """
    Full rotation matrix Rzyx
    """
    ux = np.array([1.0,0.0,0.0])
    uy = np.array([0.0,1.0,0.0])
    uz = np.array([0.0,0.0,1.0])
    r = np.dot(rot(theta[2],uz), np.dot(rot(theta[1],uy), rot(theta[0],ux)))
    return r

def _rot(matrix):

    i = 0
    j = 1
    k = 2
    M = np.array(matrix, dtype=np.float64, copy=False)[:3, :3]
    cy = math.sqrt(M[i, i]*M[i, i] + M[j, i]*M[j, i])
    if cy > np.finfo(float).eps * 4.0:
        ax = math.atan2( M[k, j],  M[k, k])
        ay = math.atan2(-M[k, i],  cy)
        az = math.atan2( M[j, i],  M[i, i])
    else:
        ax = math.atan2(-M[j, k],  M[j, j])
        ay = math.atan2(-M[k, i],  cy)
        az = 0.0
    return ax, ay, az


def dRot_a(angle, u):
    """
    Derivative of the rotation matrix with respect to the angle
    """
    s = np.sin(angle)
    c = np.cos(angle)
    u = unitVector(u) # normalize vector

    dR = np.eye(3)*(-s)
    dR += np.outer(u, u) * (s)
    dR += c*np.array((( 0.0 ,-u[2],  u[1]),
                   ( u[2], 0.0 , -u[0]),
                   (-u[1], u[0],  0.0)),
                     dtype=np.float64)
    return dR


def dRot_u(angle, u):
    """
    Derivative of the rotation matrix with respect to u
    """   
    s = np.sin(angle)
    c = np.cos(angle)
    u = unitVector(u)

    def f(j):
        du = np.zeros(3)
        dP = np.zeros((3,3))
        dR = np.zeros((3,3))
        du[j] = 1.0
        dP[j,:] = u.copy()
        dP[:,j] = u.copy()
    
        dR += dP * (1.0 - c)
        dR += s*np.array((( 0.0 ,-du[2],  du[1]),
                          ( du[2], 0.0 , -du[0]),
                          (-du[1], du[0],  0.0)),
                         dtype=np.float64)
        return dR
        
    return f(0),f(1),f(2)


def dRot_a_(theta):
    """
    gradient of the rotation matrix with respect to theta
    """
    ux = np.array([1.0,0.0,0.0])
    uy = np.array([0.0,1.0,0.0])
    uz = np.array([0.0,0.0,1.0])
    
    r1 = np.dot(dRot_a(theta[2],uz), np.dot(rot(theta[1],uy), rot(theta[0],ux)))
    r2 = np.dot(rot(theta[2],uz), np.dot(dRot_a(theta[1],uy), rot(theta[0],ux)))
    r3 = np.dot(rot(theta[2],uz), np.dot(rot(theta[1],uy), dRot_a(theta[0],ux)))
    return r1, r2, r3


def unitVector(x):
    """
    Normalise the vectore
    """
    n = np.sqrt(np.sum(x**2.0))
    if n != 0:
        return x/n
    else:
        return x
