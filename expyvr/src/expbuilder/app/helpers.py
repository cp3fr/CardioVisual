"""
Various small helper functions for the ExpyVR experiment builder GUI

@author: Tobias Leugger
@since: Spring 2011
"""

import sys


def getCompleteOrder(params, order):
    """
    Takes a dictionary 'params' and a list 'order' and returns a list that
    contains all the keys from 'params'. The order of the keys is defined as
    follows:
        - First all the elements in 'order' in the order given
        - All the remaining keys sorted alphabetically
    """
    completeOrder = []
    remaining = sorted(params.keys())
    
    # Loop through the params with a prescribed order
    for fieldName in order:
        completeOrder.append(fieldName)
        remaining.remove(fieldName)
    
    # Add any params that weren't specified in the order
    completeOrder.extend(remaining)
    
    return completeOrder
    

def getExpFileWildcard():
    wildcard = "ExpyVR experiments (*.exp.xml)|*.exp.xml|Any file (*.*)|*"
    if sys.platform != 'darwin':
        wildcard += ".*"
    return wildcard


def getInstFileWildcard():
    wildcard = "ExpyVR instances (*.inst.xml)|*.inst.xml|Any file (*.*)|*"
    if sys.platform != 'darwin':
        wildcard += ".*"
    return wildcard


