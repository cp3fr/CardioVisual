'''
Created on Mar 18, 2010

@author: tobias
'''

class SceneElement():
    """
    An element in the virtual scene
    """
    def __init__(self, x = 0, y = 0, z = 0):
        self.x, self.y, self.z = x, y, z