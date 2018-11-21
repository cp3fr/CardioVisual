"""
Filters and tools for tracker data.

Implements a Kalman filter which data can be pumped through for smoothing 
measurements from trackers.

@author: danilo.rezende@epfl.ch
"""
import numpy as np
import math        
    
class KalmanFilter():
    """
    Kalman filter functions
    """
    def __init__(self, Ns, Nc, No):
        self.Ns = Ns #state dimension
        self.Nc = Nc #control dimension
        self.No = No #observation dimension
        self.X = np.zeros(Ns)           #state
        self.Y = np.zeros(No)           #observation
        self.H = np.zeros((No, Ns))     #observation matrix
        self.P = np.eye(Ns)             #covariance of state
        self.Q = np.eye(Ns)             #covariance of dynamics
        self.R = np.eye(No)             #covariance of observation
        self.B = np.zeros((Ns,Nc))      #control matrix
        self.U = np.zeros(Nc)           #control
        self.A = np.eye(Ns)             #Dynamics matrix
        self.K = np.zeros((Ns, No))     #Kalman Gain

    def loglike(self, Y):
        """
        Calculates the log-likelihood of an observation Y given current state
        """
        Z = Y - np.dot(self.H, self.X)
        C = np.dot(np.dot(self.H, self.P), self.H.T)+self.R
        return -0.5*np.dot(np.dot(Z, np.linalg.pinv(C)), Z)-0.5*np.log(np.linalg.det(2.0*np.pi*C))
        
    def predict(self):
        #state of the filter
        self.X = np.dot(self.A, self.X) + np.dot(self.B, self.U)
        #covariance matrix
        self.P = np.dot(np.dot(self.A, self.P), self.A.T) + self.Q

    def update(self):
        #inovation
        self.V = self.Y - np.dot(self.H, self.X)
        #measurement prediction covariance
        self.S = np.dot(np.dot(self.H, self.P), self.H.T)+self.R
               
        #filter gain
        self.K = np.dot(np.linalg.inv(self.S),np.dot(self.H, self.P) )
        self.X += np.dot(self.V,self.K )
        self.P += - np.dot(self.K.T,np.dot(self.S,self.K)) 
        


class KalmanTracking():
    """
    Application of the Kalman Filter class to position, velocity and
    acceleration tracking when only position is available
    """
    def __init__(self,dim, sigmaD, sigmaO, dt):
        self.dim=dim
        #initializes a Kalman filter without control part
        self.KF = KalmanFilter(3*dim,1,dim)

        #Setting the observation covariances
        self.KF.R = np.eye(dim)*(sigmaO**2.0)
              
        for i in np.arange(self.KF.Ns):
            for j in np.arange(self.KF.Ns):
                #Observation matrix: the only thing we measure is position,
                #velocity and acceleration must be infered from this
                if (i<dim) & (i==j):
                    self.KF.H[i,j] = 1.0
            ##The dynamics matrix, actual definition of speed and
            ##acceleration comes here
            if (i<dim) :
                self.KF.A[i,dim+i] = dt
                self.KF.A[i,2*dim+i] = (dt**2.0)/2.0
                self.KF.A[dim+i,2*dim+i] = dt
                #Setting the dynamics covariances
                self.KF.Q[i,i] = dt*(sigmaD[0]**2.0)
                self.KF.Q[dim+i,dim+i] = dt*(sigmaD[1]**2.0)
                self.KF.Q[2*dim+i,2*dim+i] = dt*(sigmaD[2]**2.0)

        #position, velocity and acceleration vectors
        self.X = np.zeros(dim)
        self.V = np.zeros(dim)
        self.A = np.zeros(dim)

    def set_pos(self,X):
        self.KF.X[0:self.dim] = X.copy()
        self.X = X.copy()

    def predict(self):
        self.KF.predict()
        self.X = self.KF.X[0:self.dim].copy()
        self.V = self.KF.X[self.dim:(2*self.dim)].copy()
        self.A = self.KF.X[(2*self.dim):(3*self.dim)].copy()

    def observe(self, Xo):
        self.KF.Y = Xo.copy()
        self.KF.update()
        self.X = self.KF.X[0:self.dim].copy()
        self.V = self.KF.X[self.dim:(2*self.dim)].copy()
        self.A = self.KF.X[(2*self.dim):(3*self.dim)].copy()

    def sample(self):
        """
        To use the predictor as a generative model
        """
        X = np.random.multivariate_normal(self.KF.X, self.KF.P)
        self.X = X[0:self.dim].copy()
        self.V = X[self.dim:(2*self.dim)].copy()
        self.A = self.KF.X[(2*self.dim):(3*self.dim)].copy()



class KalmanTrackingXV():
    """
    Application of the Kalman Filter class to position, velocity and
    acceleration tracking when position AND velocity are available
    """
    def __init__(self,dim, sigmaD, sigmaO, dt):
        self.dim=dim
        #initializes a Kalman filter without control part
        self.KF = KalmanFilter(3*dim,1,2*dim)
        #Setting the observation covariances
        self.KF.R = np.eye(2*dim)*(sigmaO**2.0)
  
        for i in np.arange(self.KF.Ns):
            for j in np.arange(self.KF.Ns):
                if (i<(dim*2)) & (j==i):
                    self.KF.H[i,j] = 1.0
            ##The dynamics matrix, actual definition of speed and
            ##acceleration comes here
            if (i<dim) :
                self.KF.A[i,dim+i] = dt
                self.KF.A[i,2*dim+i] = (dt**2.0)/2.0
                self.KF.A[dim+i,2*dim+i] = dt
                #Setting the dynamics covariances
                self.KF.Q[i,i] = dt*(sigmaD[0]**2.0)
                self.KF.Q[dim+i,dim+i] = dt*(sigmaD[1]**2.0)
                self.KF.Q[2*dim+i,2*dim+i] = dt*(sigmaD[2]**2.0)

        #position, velocity and acceleration vectors
        self.X = np.zeros(dim)
        self.V = np.zeros(dim)
        self.A = np.zeros(dim)

        #Particle filter instance
        self.KPF = KalmanParticleFilter(self.KF.A, self.KF.H, self.KF.Q,self.KF.R,100)

    def set_pos(self,X):
        self.KF.X[0:self.dim] = X.copy()
        self.X = X.copy()

    def set_vel(self,V):
        self.KF.X[self.dim:(2*self.dim)] = V.copy()
        self.V = V.copy()

    def predict(self):
        self.KF.predict()
        self.X = self.KF.X[0:self.dim].copy()
        self.V = self.KF.X[self.dim:(2*self.dim)].copy()
        self.A = self.KF.X[(2*self.dim):(3*self.dim)].copy()

    def observe(self, Xo, Vo):
        self.KF.Y = np.zeros(self.KF.No)
        self.KF.Y[0:self.dim] = Xo.copy()
        self.KF.Y[self.dim:(2*self.dim)] = Vo.copy()
        self.KF.update()

        self.X = self.KF.X[0:self.dim].copy()
        self.V = self.KF.X[self.dim:(2*self.dim)].copy()
        self.A = self.KF.X[(2*self.dim):(3*self.dim)].copy()


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


def rigid(v1, v0):
    """
    Extract the rigid transformations between two sets of vectors
    MSE is minimized according to the Kabsch algorithm
    
    v1 and v0 must have shapes (3,N), where N>=3
    """
    v0 = np.array(v0, dtype=np.float64, copy=False)[:3]
    v1 = np.array(v1, dtype=np.float64, copy=False)[:3]

    if v0.shape != v1.shape or v0.shape[1] < 3:
        raise ValueError("vector sets are of wrong shape or type")

    # move centroids to origin
    t0 = np.mean(v0, axis=1)
    t1 = np.mean(v1, axis=1)
    v0 = v0 - t0.reshape(3, 1)
    v1 = v1 - t1.reshape(3, 1)

    # Singular Value Decomposition of covariance matrix
    u, s, vh = np.linalg.svd(np.dot(v1, v0.T))
    # rotation matrix from SVD orthonormal bases
    R = np.dot(u, vh)
    if np.linalg.det(R) < 0.0:
        # R does not constitute right handed system
        R -= np.outer(u[:, 2], vh[2, :]*2.0)
        s[-1] *= -1.0

    # homogeneous transformation matrix
    M = np.identity(4)
    M[:3, :3] = R
    # translation
    M[:3, 3] = t1
    T = np.identity(4)
    T[:3, 3] = -t0
    M = np.dot(M, T)

    #Affine matrix, Rotation matrix and translation vector
    return (M, R, t1 - t0)
    # return (M, R, t1 - np.dot(R, t0))


class RigidTrack():
    """
    Given a set of markers and a reference, calculates the best estimate of the 
    rigid transformation:
    v1 = rotation.v0 + translation
    Also, contains a method that mimics a camera transformation in opengl
    """
    def __init__(self, markers, markers_ref = 0):

        #define which sub-set of the markers are to be rigidly-tracked
        self.markers = markers
        self.markers_ref = markers_ref

        self.v0 = np.zeros((3,len(markers)))
        self.v1 = np.zeros((3,len(markers)))

        self.Aff = np.zeros((4,4))
        self.R = np.eye(3)
        self.T = np.zeros(3)

        self.O = np.zeros(3)

    def set_origin(self, mocap_pos):
        self.O = np.mean(mocap_pos[:,self.markers_ref],axis=1)

    def set_reference(self,mocap_pos):
        self.v0 = (mocap_pos[:,self.markers].copy().T - self.O ).T

    def set_current_pos(self,mocap_pos):
        self.v1 = (mocap_pos[:,self.markers].copy().T - self.O ).T
        
    def set_current(self,mocap_pos):
        self.set_current_pos(mocap_pos)
        self.Aff,self.R, self.T = rigid(self.v1, self.v0)

