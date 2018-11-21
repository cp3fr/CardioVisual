"""
@author: Tobias Leugger
@since: Spring 2010

@attention: Adapted from parts of the PsychoPy library
@copyright: 2009, Jonathan Peirce, Tobias Leugger
@license: Distributed under the terms of the GNU General Public License (GPL).
"""

from copy import copy
import random
import csv, re
from param import Param
from errors import showWarning
from controller import getPathFromString

class _BaseLoop:
    """
    Base loop class that all other loop classes extend from. Provides accessors
    to some values that are needed for all loops.
    """
    def __init__(self, exp, name):
        """
        @param name: name of the loop e.g. trials
        @type name: string
        @param loopType:
        @type loopType: string ('fix', 'random')
        """
        self.exp = exp
        self.hasLoopVar = False     # Whether this loop has a variable that can influence in which condition we are
        self.generateAll = False    # Whether all possible combinations should be generated for this loop when generating many instances
        self.order = ['name']       # Order of the params
        self.params = {}
        self.params['name'] = Param(name, valType='str', 
            hint="Name of this loop")

    def getType(self):
        return self.__class__.__name__
        
    def getShortType(self):
        return self.getType()[:-4].lower()
    
    def getName(self):
        return self.params['name'].val
    
    def getLoopVarValues(self):
        return []
    
    def getNumReps(self):
        return 1
    
    def _getListFromInput(self, input):
        """
        Splits the input at commas and sanitises the values.
        """
        return input.replace(' ', '').replace('-', '_').split(',')



class _BaseLoopWithReps(_BaseLoop):
    """
    Base loop class with a parameter to enter the number of times to repeat the
    loop.
    """
    def __init__(self, exp, name, nReps):
        _BaseLoop.__init__(self, exp, name)
        self.order.append('nReps')
        self.params['nReps'] = Param(int(nReps), valType='int', 
            hint="Number of times the loop is followed")
        
    def getNumReps(self):
        return self.params['nReps'].val



class _BaseLoopWithSet(_BaseLoopWithReps):
    """
    Base loop class with a parameter to specify a set of loop variables.
    """
    def __init__(self, exp, name, nReps, set, setHint):
        _BaseLoopWithReps.__init__(self, exp, name, nReps)
        self.hasLoopVar = True
        self.order.append('set')
        self.params['set'] = Param(set, valType='str', hint=setHint)
    
    def getLoopVarValues(self):
        return list(set(self._getListFromInput(self.params['set'].val)))
    


class FixLoop(_BaseLoopWithReps):
    """
    A loop that doesn't have loop vars and simply loops a certain number of 
    times.
    """
    def __init__(self, exp, name='loop', nReps=5):
        _BaseLoopWithReps.__init__(self, exp, name, nReps)
    


class RandomLoop(_BaseLoopWithSet):
    """
    A loop that randomly selects a loop var from a set of values (sampling with
    replacement).
    """
    def __init__(self, exp, name='randomise', nReps=5, set="l, r"):
        _BaseLoopWithSet.__init__(self, exp, name, nReps, set,
            "Set to sample randomly")
            
    def getSet(self):
        set = self._getListFromInput(self.params['set'].val)
        return [set[random.randrange((len(set)))] for i in range(self.getNumReps())]



class ShuffleLoop(_BaseLoopWithSet):
    """
    A loop that shuffles a set of loop var values (sampling without 
    replacement).
    """
    def __init__(self, exp, name='shuffle', nReps=5, set="l, l, r, r, r"):
        _BaseLoopWithSet.__init__(self, exp, name, nReps, set,
            "Set to shuffle randomly")
        self.generateAll = True
            
    def getSet(self):
        nReps = self.getNumReps()
        originalSet = self._getListFromInput(self.params['set'].val)

        # We need a total of nReps repetitions, make sure the set is long enough
        set = copy(originalSet)
        while len(set) < nReps:
            set.extend(copy(originalSet))
        # shuffle it
        random.shuffle(set)
        # take a sub-part of it, warning the user that we are loosing the balance of conditions
        if len(set) != nReps:
            showWarning('Shuffle loop "%s" number of repetitions (%i) is not divisible by length of set (%i). The experimental conditions might not be balanced.' % (self.getName(), nReps, len(originalSet)))
            set = set[:nReps]
        return set



class FactorialLoop(_BaseLoopWithReps):
    """
    A loop that is used for factorial experiment design. There are two sets, and
    the loop vars of this loop correspond to all the combinations of the first 
    set with the second set. All the combinations are then shuffled.
    """
    def __init__(self, exp, name='factorial loop', firstSet="left, right", secondSet="sync, async", nReps=-1):
        _BaseLoopWithReps.__init__(self, exp, name, nReps)
        self.hasLoopVar = True
        self.generateAll = True
        self.order.extend(['firstSet', 'secondSet'])
        self.params['firstSet'] = Param(firstSet, valType='str',
            hint="First set of variables for the factorial loop")
        self.params['secondSet'] = Param(secondSet, valType='str',
            hint="Second set of variables for the factorial loop")
    
    def _calculateTotalSet(self):
        first = self._getListFromInput(self.params['firstSet'].val)
        second = self._getListFromInput(self.params['secondSet'].val)
        totalSet = []
        for val1 in first:
            for val2 in second:
                totalSet.append(val1 + '-' + val2)
        return totalSet
    
    def getSet(self):
        nReps = self.getNumReps()
        originalSet = self._calculateTotalSet()       
        # We need a total of nReps repetitions, make sure the set is long enough
        totalSet = copy(originalSet)
        while len(totalSet) < nReps:
            totalSet.extend(copy(originalSet))
        # shuffle it
        random.shuffle(totalSet)
        if len(totalSet) != nReps : 
            # take a subset of totalSet
            totalSet = totalSet[:nReps]
            showWarning('Factorial loop "%s" number of repetitions (%i) is not a multiple of the factorial combination set (%i). The experimental conditions might not be balanced.' % (self.getName(), nReps, len(originalSet)))

        return totalSet

    def getLoopVarValues(self):
        var = self._calculateTotalSet()
        if self.getNumReps() < 0 :
            self.params['nReps'].setVal(len(var))
        return list(set(var))

class CSVFileLoop(_BaseLoop):
    """
    A loop that is reading conditions from a Comas Separated Values file
    """
    def __init__(self, exp, name='CSV file loop', filename="$EXPDIR$/file.csv", linemax=100):
        _BaseLoop.__init__(self, exp, name)
        self.hasLoopVar = True
        self.generateAll = True
        self.arraySet = ['default']  # loop var values : all tabs
        self.totalSet = ['default']  # executed set 
        self.linemax = linemax
        
        self.params['filename'] = Param(filename, valType='str',
            hint="Name of the Comas Separated Values file where to read conditions from.")
        self.params['linemax'] = Param(linemax, valType='int', hint='Number of lines to use for execution (all lines are used for creating the tab conditions).')
    
    def _readSetFromFile(self):    
        self.linemax = self.params['linemax'].val
        try:
            fn =  self._getListFromInput(str(self.params['filename'].val) )[0] 
            # print 'READING FILE', getPathFromString(fn)
            f = open( getPathFromString( fn ) )
            csvread = csv.reader(f)
            self.arraySet = []
            self.totalSet = []
            line = 0
            for r in csvread:
                if len(r) < 1:
                    continue
                string = ''
                for i in r:
                    i = re.sub(r'\s', '', str(i) )
                    string += i + '-'
                string = string[:-1]
                if self.arraySet.count(string) < 1:
                    self.arraySet.append(string)
                    
                if line < self.linemax: 
                    self.totalSet.append(string)
                    
                line += 1
                
        except IOError:
            showWarning( 'Could not open file %s.\n\nThe filename given was: %s.'%(getPathFromString(fn), str(fn)) )
            self.arraySet = ['default']
            self.totalSet = ['default']
        else:
            f.close()
            
        self.arraySet.sort()
    
    def getNumReps(self):
        self._readSetFromFile()
        return  min(len(self.totalSet), self.linemax)
    
    def getSet(self):
        self._readSetFromFile()
        return self.totalSet

    def getLoopVarValues(self):
        self._readSetFromFile()
        return list(self.arraySet)


