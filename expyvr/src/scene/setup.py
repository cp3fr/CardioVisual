'''
Created on Mar 18, 2010

@author: tobias
'''

import scene

class Setup():
    """
    Class that helps setting up the virtual scene.
    
    Cycles through the elements to be able to adjust
    their position
    """
    
    def __init__(self):
        self.__elements = []
        self.__currentIndex = 0
    
    def addElement(self, element):
        # TODO: check that element has x, y, z
        if isinstance(element, scene.SceneElement):
            self.__elements.append(element)
        else:
            raise TypeError, "Element must be of type scene.SceneElement"
    
    def currentElement(self):
        numElements = len(self.__elements)
        if numElements > 0:
            return self.__elements[self.__currentIndex]
        return None
    
    def nextElement(self):
        numElements = len(self.__elements)
        if numElements > 0:
            self.__currentIndex += 1
            if self.__currentIndex >= numElements:
                self.__currentIndex = 0
            return self.__elements[self.__currentIndex]
        return None