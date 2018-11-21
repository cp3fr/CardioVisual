"""
@author: Tobias Leugger
@since: Spring 2010

@attention: Adapted from parts of the PsychoPy library
@copyright: 2009, Jonathan Peirce, Tobias Leugger
@license: Distributed under the terms of the GNU General Public License (GPL).
"""
from expbuilder.app.errors import showWarning

class Param:
    """
    Defines parameters for Experiment Components
    """
    def __init__(self, val, valType, allowedVals=[], hint="", hasStandard=False):
        """
        @param val: the value for this parameter
        @type val: any
        @param valType: the type of this parameter ('int', 'float', 'bool', 'str', 'code'). 'code' can be used
        for complex types such as tuples, dicts or even classes
        @type valType: str
        @param allowedVals: possible vals for this param (e.g. units param can only be 'norm','pix',...)
        @type allowedVals: list of str
        @param hint: description of this parameter for the user
        @type hint: string
        @param hasStandard: whether this param should have a checkbox to specify whether it is the 
        same a some standard or not
        @type hasStandard bool
        """
        self.val = val
        self.valType = valType
        self.hint = hint
        self.allowedVals = allowedVals
        self.hasStandard = hasStandard
        self.likeStandard = hasStandard # If it has a standard, default it to use it

    def __deepcopy__(self, memo):
        # recursion test
        not_there = []
        existing = memo.get(self, not_there)
        if existing is not not_there:
            return existing
        dup = Param(self.val, self.valType, self.allowedVals, self.hint, self.hasStandard)
        return dup
        
    def setVal(self, val):
        if self.valType == 'bool':
            if isinstance(val, bool):
                self.val = val
            elif val.lower() == 'true':
                self.val = True
            else:
                self.val = False
        elif self.valType == 'float':
            try:
                self.val = float(val)
            except:
                showWarning('"%s" is not a valid float, value stays "%.2f".' % (val, self.val))
        elif self.valType == 'int':
            try:
                self.val = int(val)
            except:
                showWarning('"%s" is not a valid int, value stays "%d".' % (val, self.val))
        else:
            self.val = val
            
    def updateFromCtrl(self, ctrl):
        """
        Updates this parameters with the values from the _ParamCtrls object passed
        """
        self.setVal(ctrl.getValue())
        if self.hasStandard:
            self.likeStandard = ctrl.likeStandardCtrl.GetValue()



def getParamFromDesc(desc, value):
    """
    Returns a new param created from the param description and the inital value.
    Description is a 3-tuple or 4-tuple of name of the param, type and  
    a description for the user. An optional 4th part is a list of allowed
    values if the param should be a choice box
    """
    allowedVals = []
    if len(desc) > 3:
        allowedVals = desc[3]
    return Param(value, valType=desc[1], hint=desc[2], allowedVals=allowedVals)
        
