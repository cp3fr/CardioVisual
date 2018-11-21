"""

IMPORTANT:
This should be fixed and once it's working integrated in the trackerTools
- Toby

"""



"""
Tools to process MOCAP data such as methods for representing skeletons with KDL

@author: danilo.rezende@epfl.ch
"""
import numpy as np
import PyKDL as kdl


def distanceMatrix(mocap_pos):
    """
    Returns the sensor distance matrix, useful for automatic skeleton discovery
    """
    Ns = mocap_pos.shape[1]
    dist = np.zeros((Ns,Ns))
    for i in range(Ns-1):
        for j in range(i+1,Ns):
            dist[i,j] = np.sqrt( np.sum(  (mocap_pos[:,i] - mocap_pos[:,j])**2.0   )   )
            dist[j,i] = dist[i,j]
    return dist


def distanceStats(pos):
    """
    Calculates mean and variance of distance matrix given a preprocessed 
    position MOCAP matrix
    """
    k = 0
    Ne = pos.shape[0]
    Ns = pos.shape[1]/3
    hist_dist = np.zeros((Ne,Ns**2.0))
    for pos in pos:
        mocap_pos = pos.reshape((3,Ns))
        hist_dist[k,:] = distanceMatrix(mocap_pos).flatten().copy()
        k += 1
    return (np.mean(hist_dist,0), np.std(hist_dist,0))

