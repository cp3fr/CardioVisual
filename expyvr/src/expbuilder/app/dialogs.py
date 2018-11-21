"""
@author: Tobias Leugger
@since: Spring 2010

@attention: Adapted from parts of the PsychoPy library
@copyright: 2009, Jonathan Peirce, Tobias Leugger
@license: Distributed under the terms of the GNU General Public License (GPL).
"""

import wx
from wx.lib import flatnotebook, scrolledpanel
from copy import copy
import math

import loops, experiment, helpers
from param import Param
from errors import showError

class _BaseParamsDlg(wx.Dialog):
    def __init__(self, frame, title, params, order, nameObject=None, doNameCheck=True,  
            helpUrl=None, pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT|wx.TAB_TRAVERSAL):
        wx.Dialog.__init__(self, frame, -1, title, pos, size, style)
        self.frame = frame
        self.params = params
        self.order = order
        self.doNameCheck = doNameCheck
        self.nameObject = nameObject
        self.helpUrl = helpUrl
        self.exp = frame.exp
        self.app = frame.app
        self.dpi = self.app.dpi
        self.paramCtrls = {}
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.ctrlSizer = wx.GridBagSizer()
        self.currRow = 0
        self.nameOKlabel = None
        self.hasSetParams = False
        self.hasNotebookParams = False
        self.paramSetNotebooks = []
        self.dialogWidth = self.dpi * 4.0
        self._buttonDisabledReasons = {}   # a dict of reasons why some buttons are disabled
        
#        self.ctrlSizer.SetFlexibleDirection(wx.HORIZONTAL)
#        self.ctrlSizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_ALL)
        self.ctrlSizer.AddGrowableCol(1)
        
        if self.doNameCheck:
            self.nameOKlabel = wx.StaticText(self, -1, '', size=(self.dialogWidth, 25), style=wx.ALIGN_RIGHT)
            self.nameOKlabel.SetForegroundColour(wx.RED)
            
        # add buttons for OK and Cancel
        self.buttons = wx.StdDialogButtonSizer()
        
        # help button if we know the url
        if self.helpUrl != None:
            helpBtn = wx.Button(self, wx.ID_HELP)
            helpBtn.SetHelpText("Get help about this component")
            helpBtn.Bind(wx.EVT_BUTTON, self.onHelp)
            self.addButton(helpBtn)
        
        self.OKbtn = wx.Button(self, wx.ID_OK, "OK")
        self.OKbtn.SetDefault()
        self.addButton(self.OKbtn)
        
        cancelBtn = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.addButton(cancelBtn)

        # Add all the controls for all the params
        order = helpers.getCompleteOrder(self.params, self.order)
        for fieldName in order:
            self.addParam(fieldName)
            
    def addParamNotebook(self, setHandlers):
        """
        Adds a new notebook to the list of notebooks constructed
        with the passed set handlers.
        @return: The newly created notebook 
        """
        newNoteBook = _ParamsNotebook(self, setHandlers, self.dialogWidth)
        self.paramSetNotebooks.append(newNoteBook)
        self.hasNotebookParams = True
        return newNoteBook
            
    def enableParamSets(self, setHandlers, label='', activeSet=None):
        """
        Enables the support for multiple sets of parameters. Only 
        one set of params can be edited at any time and you can switch between the 
        sets with a choice box that is added automatically.
        All the controls for the passed set handlers will be created. Further sets
        can be added or removed with the addParamSet and removeParamSet functions
        @param setHandlers A dictionary of handlers that have params
        @param label Label that will be used for the set choice box
        @param activeSet The set that will be selected
        choice box to switch between the different sets
        """
        # initialise all the required variables
        self.hasSetParams = True
        self.setHandlers = {}
        self.setLabel = label
        self.currentSet = activeSet
        self.setParams = {}
        self.setOrder = {}
        self.setParamCtrls = {}
        self.setCtrlSizer = {}
        self.allSetCtrlSizer = wx.BoxSizer(wx.VERTICAL)
        
        # create the selection box to switch between the sets
        self.params[self.setLabel] = Param(self.currentSet, valType='str', allowedVals=sorted(setHandlers.keys()))
        self.addParam(self.setLabel)
        self.Bind(wx.EVT_CHOICE, self.onSetChanged, self.paramCtrls[self.setLabel].valueCtrl)
        
        # Add all the param sets
        for setName, setHandler in setHandlers.iteritems():
            self.addParamSet(setHandler, setName)
        self.changeSet(self.currentSet)
                 
                 
    def addParamSet(self, setHandler, setName):
        """
        Adds all the controls for the given param set with the given set name.
        Also ads the set name to the choice of sets in the choice box if it's
        not already there.
        """
        self.setHandlers[setName] = setHandler
        self.setParams[setName] = setHandler.params
        self.setOrder[setName] = setHandler.order
        self.setParamCtrls[setName] = {}
        # add the sizer and add it to the sizer for all param sets
        self.setCtrlSizer[setName] = wx.BoxSizer(wx.VERTICAL)
        self.allSetCtrlSizer.Add(self.setCtrlSizer[setName], flag=wx.EXPAND)
        
        # Add all the controls for all the params of this set
        order = helpers.getCompleteOrder(self.setParams[setName], self.setOrder[setName])
        for fieldName in order:
            self._addParamToSet(fieldName, setName)
            
        # Add the name to the choice box to be able to select this set 
        # if it's needed not already there
        if self.paramCtrls[self.setLabel].valueCtrl.FindString(setName) == wx.NOT_FOUND:
            self.paramCtrls[self.setLabel].valueCtrl.Append(setName)
            
    def _addParamToSet(self, fieldName, setName):
        """
        Adds the controls for one param with the given field name
        in the given set of params
        """
        ctrls = _ParamCtrls(dlg=self, parent=self, label=fieldName, param=self.setParams[setName][fieldName])
        self.setParamCtrls[setName][fieldName] = ctrls
        if self.doNameCheck and fieldName == 'name':
            ctrls.valueCtrl.Bind(wx.EVT_TEXT, self.checkName)
        container = wx.BoxSizer(wx.HORIZONTAL)
        
        # BHBN
        container.Add(ctrls.nameCtrl, proportion=0, flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.LEFT, border=5)
        container.Add(ctrls.valueCtrl, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL, border=2)
        self.setCtrlSizer[setName].Add(container, flag=wx.EXPAND)
        
    def removeParamSet(self, setName):
        """
        Removes the param set with the specified name. Cleanes up all
        the controls created and removes the set name from the choice box so
        you can't select this param set anymore. 
        """
        if setName not in self.setHandlers:
            return
        # hide all set ctrls
        for param in self.setParamCtrls[setName].itervalues():
            param.nameCtrl.Hide()
            param.valueCtrl.Hide()
        # remove all the objects
        del(self.setHandlers[setName])
        del(self.setParams[setName])
        del(self.setOrder[setName])
        del(self.setParamCtrls[setName])
        self.allSetCtrlSizer.Remove(self.setCtrlSizer[setName])
        del(self.setCtrlSizer[setName])
        self.paramCtrls[self.setLabel].valueCtrl.Delete(self.paramCtrls[self.setLabel].valueCtrl.FindString(setName))
        
    def addButton(self, button):
        """
        Adds the passed button to the buttons at the bottom of the dialog
        """
        # TODO: (minor) make that buttons are added on the left not on the right
        self.buttons.Add(button, 0, wx.ALL, border=3)
    
    def addParam(self, fieldName):
        ctrls = _ParamCtrls(dlg=self, parent=self, label=fieldName, param=self.params[fieldName])
        self.paramCtrls[fieldName] = ctrls
        if self.doNameCheck and fieldName == 'name':
            ctrls.valueCtrl.Bind(wx.EVT_TEXT, self.checkName)
                        
        self.ctrlSizer.Add(ctrls.nameCtrl, (self.currRow, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, border=10)
        self.ctrlSizer.Add(ctrls.valueCtrl, (self.currRow, 1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, border=2)
        self.currRow += 1
        
    def addInfo(self, fieldName, fieldText):
        ctrls = _InfoCtrls(dlg=self, parent=self, label=fieldName, text=fieldText)
        
        self.ctrlSizer.Add(ctrls.nameCtrl, (self.currRow, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, border=10)
        self.ctrlSizer.Add(ctrls.valueCtrl, (self.currRow, 1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, border=2)
        self.currRow += 1
        
    def addSeparator(self):
        self.ctrlSizer.Add(wx.StaticLine(self), (self.currRow, 0), flag=wx.GROW|wx.TOP, border=15)
        self.ctrlSizer.Add(wx.StaticLine(self), (self.currRow, 1), flag=wx.GROW|wx.TOP, border=15)
        self.currRow += 1
        
    def removeParam(self, fieldName):
        # remove the ctrl from the dict of controls
        ctrls = self.paramCtrls.pop(fieldName)
        
        # hide all fields and remove them from the sizer
        ctrls.nameCtrl.Hide()
        ctrls.valueCtrl.Hide()
        self.ctrlSizer.Remove(ctrls.nameCtrl)
        self.ctrlSizer.Remove(ctrls.valueCtrl)
        
        # decrease the current row
        self.currRow -= 1
                
    def enableParam(self, fieldName, enabled=True):
        ctrls = self.paramCtrls[fieldName]
        
        # hide all fields and remove them from the sizer
        ctrls.nameCtrl.Enable(enabled)
        ctrls.valueCtrl.Enable(enabled)
        
        
    def _addAllToMainsizer(self):
        """
        Adds all the elements to the main sizer. Is called in the show() method 
        and can be overwritten in children if new elements have to be added or 
        the order has to be changed 
        """
        # put it all together
        if len(self.paramCtrls) > 0:
            self.mainSizer.Add(self.ctrlSizer, flag=wx.EXPAND|wx.TOP, border=5)
        if self.hasSetParams:
            self.mainSizer.Add(self.allSetCtrlSizer, flag=wx.EXPAND|wx.TOP, border=5)
        if self.hasNotebookParams:
            for notebook in self.paramSetNotebooks:
                self.mainSizer.Add(notebook, proportion=1, flag=wx.EXPAND|wx.TOP, border=5)
        if self.nameOKlabel:
            self.mainSizer.Add(self.nameOKlabel, flag=wx.ALL, border=5)
        self.mainSizer.Add(self.buttons, flag=wx.ALIGN_RIGHT)

    def show(self):
        """
        Puts all the elements together and shows dialog

        This method returns wx.ID_OK (as from ShowModal), but also
        sets self.OK to be True or False
        """
        # put it all together
        self.checkName()
        self._addAllToMainsizer()
        self.SetSizerAndFit(self.mainSizer)
        self.Center()

        # do show and process return
        retVal = self.ShowModal()
        self.OK = (retVal == wx.ID_OK)
        return wx.ID_OK
    
    def changeSet(self, setName=None):
        if setName == None and len(self.setHandlers) > 0:
            # If no new set was given, take a random one
            setName = self.setHandlers.keys()[0]
        if setName != None:
            # make sure the right value is set in the set changer
            self.paramCtrls[self.setLabel].setValue(setName)
            # hide all set ctrls
            for ctrls in self.setParamCtrls.itervalues():
                for param in ctrls.itervalues():
                    param.nameCtrl.Hide()
                    param.valueCtrl.Hide()
            self.currentSet = setName
            if self.nameObject in self.setHandlers:
                # if the last name object was a set handler, set it to the new one
                self.nameObject = self.setHandlers[setName]
            # then show ctrls of this set
            for param in self.setParamCtrls[setName].itervalues():
                param.nameCtrl.Show()
                param.valueCtrl.Show()
        
        self.checkName()
        self.mainSizer.Layout()
        self.Fit()
        self.Refresh()

    def getParams(self):
        """
        retrieves data from any fields in self.paramCtrls
        (populated during the __init__ function)

        The new data from the dlg get inserted back into the original params
        used in __init__ and are also returned from this method.
        """
        # get data from input fields
        for fieldName in self.params.keys():
            param = self.params[fieldName]
            ctrls = self.paramCtrls[fieldName] # the various dlg ctrls for this param
            param.updateFromCtrl(ctrls)
    
        # get data from notebook input fields
        if self.hasNotebookParams:
            for notebook in self.paramSetNotebooks:
                notebook.getParams()
    
        # get data from input fields
        if self.hasSetParams:
            for setName, setHandler in self.setHandlers.iteritems():
                for fieldName, param in setHandler.params.iteritems():
                    param.updateFromCtrl(self.setParamCtrls[setName][fieldName])
    
        return self.params
    
    def disableButton(self, button, reason):
        """
        Disables the given button with the given reason
        """
        if button not in self._buttonDisabledReasons:
            self._buttonDisabledReasons[button] = set()
        self._buttonDisabledReasons[button].add(reason)
        button.Disable()
    
    def enableButton(self, button, reason):
        """
        Removes the given reason to keep the given button disabled
        and enables the button if no more reasons are left
        """
        if button not in self._buttonDisabledReasons:
            self._buttonDisabledReasons[button] = set()
        if reason in self._buttonDisabledReasons[button]:
            self._buttonDisabledReasons[button].remove(reason)
        if len(self._buttonDisabledReasons[button]) == 0:
            button.Enable()
    
    def checkName(self, event=None):
        if not self.doNameCheck:
            return  # Only check the name if specified
        
        if event:
            newName = event.GetString()
        elif self.hasSetParams and 'name' in self.setParamCtrls[self.currentSet]:
            newName = self.setParamCtrls[self.currentSet]['name'].getValue()
        elif hasattr(self, 'paramCtrls'):
            newName = self.paramCtrls['name'].getValue()

        if newName == '':
            self.nameOKlabel.SetLabel("Missing name")
            self.OKbtn.Disable()
        elif newName.lower() == 'name':
            self.nameOKlabel.SetLabel("'name' is reserved")
            self.OKbtn.Disable()
        else:
            used = self.frame.exp.getUsedName(newName)
            if used != None and used != self.nameObject:
                # Disallow this name if it's not the name of the nameObject itself
                self.nameOKlabel.SetLabel("Name '%s' is already used by a %s" %(newName, used.getType()))
                self.OKbtn.Disable()
            else:
                self.nameOKlabel.SetLabel("")
                self.OKbtn.Enable()
                
    def onSetChanged(self, evt):
        newSet = evt.GetString()
        if newSet != self.currentSet:
            self.changeSet(newSet)

    def onHelp(self, event=None):
        self.app.followLink(url=self.helpUrl)



class _ParamsNotebook(flatnotebook.FlatNotebook):
    """
    A notebook (tab pane) that allows to access multiple sets of params easily
    """
    def __init__(self, parentDlg, paramSets, width):
        flatnotebook.FlatNotebook.__init__(self, parentDlg, agwStyle=flatnotebook.FNB_NO_X_BUTTON)
        self.width = width

        # initialise all the required variables
        self.parentDlg = parentDlg
        self.paramSets = {}
        self.paramSetCtrls = {}

        # Add all the param sets sorted alphabetically
        keys = sorted(paramSets.keys())
        for key in keys:
            self.addParamSet(paramSets[key], key, select=False)
                        
    def addParamSet(self, paramSet, setName, select=True):
        self.paramSets[setName] = paramSet
        # TODO: (code quality) put these calulations somewhere else
        height = self.parentDlg.dpi * min(len(paramSet.params), 7) / 3
        setCtrlPanel = scrolledpanel.ScrolledPanel(self.parentDlg, -1, size=(self.width, height))
        setCtrlPanel.setName = setName
        self.paramSetCtrls[setName] = {}
        setCtrlSizer = wx.BoxSizer(wx.VERTICAL)
    
        # TODO: (code quality) put this in its own method
        # loop through the params with a prescribed order and through the others
        fields = copy(paramSet.order) 
        fields.extend([field for field in paramSet.params.keys() if field not in fields]) # add the fields that are not already there
        for fieldName in fields:
            ctrls = _ParamCtrls(dlg=self.parentDlg, parent=setCtrlPanel, label=fieldName, param=paramSet.params[fieldName])
            self.paramSetCtrls[setName][fieldName] = ctrls
            if fieldName == 'name':
                ctrls.valueCtrl.Bind(wx.EVT_TEXT, self.onNameChange)
            container = wx.BoxSizer(wx.HORIZONTAL)
            container.Add(ctrls.nameCtrl, proportion=0, flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, border=10)
            container.Add(ctrls.valueCtrl, proportion=1, flag=wx.EXPAND|wx.ALL, border=2)
            if ctrls.likeStandardCtrl:
                container.Add(ctrls.likeStandardCtrl, flag=wx.ALIGN_CENTER_VERTICAL)
            setCtrlSizer.Add(container, flag=wx.EXPAND|wx.ALL, border=2)
        # size the panel and setup scrolling
        setCtrlPanel.SetSizer(setCtrlSizer)
        setCtrlPanel.SetAutoLayout(1)
        setCtrlPanel.SetupScrolling()
        self.AddPage(setCtrlPanel, setName, select)
        
    def removeCurrentSet(self):
        pageNum = self.GetSelection()
        setName = self.getCurrentSetName()
        del(self.paramSets[setName])
        del(self.paramSetCtrls[setName])
        self.DeletePage(pageNum)
        
    def getParams(self):   
        # get data from input fields
        for setName, paramSet in self.paramSets.iteritems():
            for fieldName, param in paramSet.params.iteritems():
                param.updateFromCtrl(self.paramSetCtrls[setName][fieldName])
                
    def getCurrentSetName(self):
        return self.GetPage(self.GetSelection()).setName
                
    def onNameChange(self, evt):
        pageNum = self.GetSelection()
        page = self.GetPage(pageNum)
        self.RemovePage(pageNum)
        self.InsertPage(pageNum, page, evt.GetString(), select=True)
        if self.parentDlg.doNameCheck:
            self.parentDlg.checkName(evt)



class _Ctrls:
    """
    An abstract class for a text plus an input control. Provides access methods
    to the input controls that might be of different types (choice, text, checkbox)
    """
    def __init__(self, dlg, parent):
        self.dlg = dlg
        self.parent = parent
        self.dpi = self.dlg.dpi
        self.valueCtrlSize = wx.Size(self.dpi*1.5, -1)
        self.nameCtrlSize = wx.Size(self.dpi*1.5, self.dpi/3)
        self.likeStandardCtrlSize = wx.Size(self.dpi*1.2, -1)
        self.nameCtrl = self.valueCtrl = self.likeStandardCtrl = None
        
    def _getCtrlValue(self, ctrl):
        """
        Different types of control have different methods for retrieving value.
        This function checks them all and returns the value or None.
        """
        if ctrl == None:
            return None
        elif hasattr(ctrl, 'GetValue'): # e.g. TextCtrl
            return ctrl.GetValue()
        elif hasattr(ctrl, 'GetStringSelection'): # for wx.Choice
            return ctrl.GetStringSelection()
        elif hasattr(ctrl, 'GetLabel'): # for wx.StaticText
            return ctrl.GetLabel()
        else:
            print "failed to retrieve the value for %s" %(ctrl)
            return None
            
    def _setCtrlValue(self, ctrl, newVal):
        """
        Set the current value form the control (whatever type of ctrl it
        is, e.g. checkbox.SetValue, textctrl.SetStringSelection)
        """
        if ctrl == None:
            return
        elif hasattr(ctrl, 'SetValue'): # e.g. TextCtrl
            ctrl.SetValue(newVal)
        elif hasattr(ctrl, 'SetStringSelection'): # for wx.Choice
            ctrl.SetStringSelection(newVal)
        elif hasattr(ctrl, 'SetLabel'): # for wx.StaticText
            ctrl.SetLabel(newVal)
        else:
            print "failed to set the value for %s" %(ctrl)
            
    def getValue(self):
        """
        Get the current value of the value ctrl
        """
        return self._getCtrlValue(self.valueCtrl)
    
    def setValue(self, newVal):
        """
        Set the current value of the value ctrl
        """
        return self._setCtrlValue(self.valueCtrl, newVal)


class _InfoCtrls(_Ctrls):
    def __init__(self, dlg, parent, label, text):
        _Ctrls.__init__(self, dlg, parent)
        self.nameCtrl = wx.StaticText(self.parent, -1, label, size=self.nameCtrlSize, style=wx.ALIGN_RIGHT)  
        f = self.nameCtrl.GetFont()
        f.SetWeight(wx.BOLD)
        self.nameCtrl.SetFont(f)           
        self.valueCtrl = wx.StaticText(self.parent, -1, text, size=self.nameCtrlSize.Scale(1, text.count('\n')), style=wx.ALIGN_LEFT) 
        f = self.valueCtrl.GetFont()
        f.SetStyle(wx.ITALIC)
        self.valueCtrl.SetFont(f)      
        
class _ParamCtrls(_Ctrls):
    def __init__(self, dlg, parent, label, param):
        """
        Create a set of ctrls for a particular Component Parameter, to be
        used in Component Properties dialogs. These need to be positioned
        by the calling dlg.
        e.g.:
            param = experiment.Param(val='boo')
            ctrls = _ParamCtrls(dlg=self, parent=self, label=fieldName, param=param)
            self.paramCtrls[fieldName] = ctrls    # keep track of them in the dlg
            self.sizer.Add(ctrls.nameCtrl, (self.currRow, 0), (1,1), wx.ALIGN_RIGHT)
            self.sizer.Add(ctrls.valueCtrl, (self.currRow, 1))
        """
        _Ctrls.__init__(self, dlg, parent)
        
        # param has the fields: val, allowedVals=[], hint=""
        self.param = param
        self.nameCtrl = wx.StaticText(self.parent, -1, label, size=self.nameCtrlSize, style=wx.ALIGN_RIGHT)
        
        # BHBN; set the parameter in bold font to show that it is scriptable (when hint ends with a '*')
        if param.hint.endswith('*'):
            f = self.nameCtrl.GetFont()
            f.SetWeight(wx.BOLD)
            self.nameCtrl.SetFont(f)
                         
        if label == 'text':
            # for text input we need a bigger (multiline) box
            self.valueCtrl = wx.TextCtrl(self.parent, -1, str(param.val),
                style=wx.TE_MULTILINE, size=self.valueCtrlSize)
        elif param.valType == 'bool':
            # only True or False - use a checkbox
            self.valueCtrl = wx.CheckBox(self.parent, size=self.valueCtrlSize)
            self.valueCtrl.SetValue(param.val)
        elif len(param.allowedVals) >= 1:
            # there are limitted options - use a Choice control
            self.valueCtrl = wx.Choice(self.parent, choices=param.allowedVals, size=self.valueCtrlSize)
            self.valueCtrl.SetStringSelection(unicode(param.val))
        else:
            # create the full set of ctrls
            self.valueCtrl = wx.TextCtrl(self.parent, -1, str(param.val), size=self.valueCtrlSize)
        # define the tool tip
        self.valueCtrl.SetToolTipString(param.hint.rstrip('*'))
        
        if param.hasStandard:
            self.likeStandardCtrl = wx.CheckBox(self.parent, size=self.likeStandardCtrlSize, label='as in standard')
            self.likeStandardCtrl.Bind(wx.EVT_CHECKBOX, self.onLikeStandardChange)
            self.likeStandardCtrl.SetValue(param.likeStandard)
            if param.likeStandard:
                self.valueCtrl.Disable()
                
    def onLikeStandardChange(self, evt):
        if evt.Checked():
            self.valueCtrl.Disable()
        else:
            self.valueCtrl.Enable()



class _PositionCtrls(_Ctrls):
    def __init__(self, dlg, parent, label, positions):
        """
        Create a set of ctrls to set the position of an element within the flow
        """
        _Ctrls.__init__(self, dlg, parent)

        self.nameCtrl = wx.StaticText(self.parent, -1, label, size=self.nameCtrlSize, style=wx.ALIGN_RIGHT)

        # position choices
        positionStrings = [str(n) for n in range(len(positions))] # convert possible points to strings
        self.valueCtrl = wx.Choice(parent=self.parent, id=-1, choices=positionStrings, size=self.valueCtrlSize)



class DlgLoopProperties(_BaseParamsDlg):
    def __init__(self, frame, possPoints, title="Loop properties", loop=None,
            helpUrl=None, pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT|wx.RESIZE_BORDER):
        _BaseParamsDlg.__init__(self, frame, title, {}, [],
                                helpUrl=helpUrl, pos=pos, size=size, style=style)

        # create instances of all loop types
        setHandlers = {
            'fix': loops.FixLoop(exp=self.exp),
            'random': loops.RandomLoop(exp=self.exp),
            'shuffle': loops.ShuffleLoop(exp=self.exp),
            'factorial': loops.FactorialLoop(exp=self.exp),
            'file': loops.CSVFileLoop(exp=self.exp)
        }
        currentSet = 'fix'
        currentStart, currentEnd = 0, 1
        if loop != None:
            # Overwrite the relevant loop with the specified one
            currentSet = loop.getShortType()
            setHandlers[currentSet] = loop
            currentStart, currentEnd = self.exp.flow.getLoopPosition(loop)
        
        # set the different sets of params
        self.enableParamSets(setHandlers, label='type', activeSet=currentSet)
        # set the name object to be the current set handler
        self.nameObject = self.setHandlers[self.currentSet]
        
        # position choices
        self.paramCtrls['positionStart'] = _PositionCtrls(dlg=self, parent=self, label='position start', positions=possPoints)
        self.ctrlSizer.Add(self.paramCtrls['positionStart'].nameCtrl, (self.currRow, 0), flag=wx.ALIGN_LEFT|wx.RIGHT|wx.LEFT, border=5)
        self.ctrlSizer.Add(self.paramCtrls['positionStart'].valueCtrl, (self.currRow, 1), flag=wx.EXPAND|wx.ALL, border=2)
        self.currRow += 1
        self.paramCtrls['positionStart'].setValue(str(currentStart))
        
        self.paramCtrls['positionEnd'] = _PositionCtrls(dlg=self, parent=self, label='position end', positions=possPoints)
        self.ctrlSizer.Add(self.paramCtrls['positionEnd'].nameCtrl, (self.currRow, 0), flag=wx.ALIGN_LEFT|wx.RIGHT|wx.LEFT, border=5)
        self.ctrlSizer.Add(self.paramCtrls['positionEnd'].valueCtrl, (self.currRow, 1), flag=wx.EXPAND|wx.ALL, border=2)
        self.currRow += 1
        self.paramCtrls['positionEnd'].setValue(str(currentEnd))
        
        self.paramCtrls['positionStart'].valueCtrl.Bind(wx.EVT_CHOICE, self.onPositionChanged)
        self.paramCtrls['positionEnd'].valueCtrl.Bind(wx.EVT_CHOICE, self.onPositionChanged)

        # show dialog and get the data
        self.show()
        if self.OK:
            self.getParams()
        
    def onPositionChanged(self, evt=None):
        pass
        # TODO: (normal) implement this funtion to display error msg and make sure flows do not misbehave (not all flows can be linearised with this function)
        # disable ok button when the positions selected don't make sense 
#        if self.positionCtrlsStart.getValue() >= self.positionCtrlsEnd.getValue():
#            #self.nameOKlabel.SetLabel("Name '%s' is already used by a %s" %(newName, used.getType()))
#            self.OKbtn.Disable()
#        else:
#            #self.nameOKlabel.SetLabel("")
#            self.OKbtn.Enable()

    def getPositions(self):
        return (self.paramCtrls['positionStart'].getValue(), self.paramCtrls['positionEnd'].getValue())



class DlgIsiProperties(_BaseParamsDlg):
    def __init__(self, frame, possPoints, title="ISI properties", isiHandler=None,
            helpUrl=None, pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT|wx.RESIZE_BORDER):        
        # set the isi handler
        if isiHandler != None:
            self.isiHandler = isiHandler
            currentPos = str(frame.exp.flow.index(self.isiHandler))
        else:
            self.isiHandler = experiment.Isi(exp=frame.exp, name='isi')
            currentPos = str(len(frame.exp.flow))
        
        _BaseParamsDlg.__init__(self, frame, title, self.isiHandler.params, self.isiHandler.order, 
                                nameObject=self.isiHandler, helpUrl=helpUrl, pos=pos, size=size, style=style)
      
        # position choices
        self.paramCtrls['position'] = _PositionCtrls(dlg=self, parent=self, label='position', positions=possPoints)
        self.ctrlSizer.Add(self.paramCtrls['position'].nameCtrl, (self.currRow, 0), flag=wx.ALIGN_LEFT|wx.RIGHT|wx.LEFT, border=5)
        self.ctrlSizer.Add(self.paramCtrls['position'].valueCtrl, (self.currRow, 1), flag=wx.EXPAND|wx.ALL, border=2)
        self.currRow += 1
        self.paramCtrls['position'].setValue(currentPos)

        # show dialog and get the data
        self.show()
        if self.OK:
            self.getParams()
        
    def getPosition(self):
        return self.paramCtrls['position'].getValue()
    


class DlgComponentProperties(_BaseParamsDlg):
    def __init__(self, frame, title, component,
            helpUrl=None, pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT|wx.RESIZE_BORDER):
        _BaseParamsDlg.__init__(self, frame, title, component.params, component.order, nameObject=component, 
                                helpUrl=helpUrl, pos=pos, size=size, style=style)
        self.component = component
        self.configsNotebook = None
        self.dialogWidth += self.dpi # make dialog a bit wider because we have the 'as in standard' checkboxes
        
        # BHBN Add list of info text provided in the conf Decription
        hasInfo = False
        for item in component._moduleMain.confDescription:
            if item[1] == 'info':
                if not hasInfo:
                    self.addSeparator()
                    hasInfo = True
                self.addInfo(item[0], item[2])
        
        # Add the param controls for the different configs
        setHandlers = self.component.configs
        self.configsNotebook = self.addParamNotebook(setHandlers)
        self.configsNotebook.paramSetCtrls['standard']['name'].valueCtrl.Disable()
        
        # Add the remove and add config buttons
        addConfigBtn = wx.Button(self, wx.ID_ADD, "Add Config")
        addConfigBtn.Bind(wx.EVT_BUTTON, self.onAddConfig)
        self.removeConfigBtn = wx.Button(self, wx.ID_REMOVE, "Remove Config")
        self.removeConfigBtn.Bind(wx.EVT_BUTTON, self.onRemoveConfig)
        if len(self.component.configs) < 2:
            self.disableButton(self.removeConfigBtn, 'notEnoughConfigs')
        self.configBtns = wx.StdDialogButtonSizer()
        self.configBtns.Add(addConfigBtn, 0, wx.ALL, border=3)
        self.configBtns.Add(self.removeConfigBtn, 0, wx.ALL, border=3)

        # show the dialog and get the params
        self.show()
        if self.OK:
            self.getParams() # get new vals from dlg
            # update the configs
            newConfigs = {}
            for config in self.configsNotebook.paramSets.itervalues():
                # Need to go through all the configs because the dictionary key
                # might not be the correct name anymore if name has changed
                newConfigs[config.getName()] = config
            self.component.setConfigs(newConfigs)
            
    def onAddConfig(self, event=None):
        """
        Adds a new config to the dialog and
        switches the focus to the new config
        """
        usedNames = self.configsNotebook.paramSets.keys()
        for ctrls in self.configsNotebook.paramSetCtrls.itervalues():
            usedNames.append(str(ctrls['name'].valueCtrl.GetValue()))
        num = 1
        name = 'config '
        while name + str(num) in usedNames:
            num += 1
        name += str(num)
        # get the new config and add the ctrls
        newConfig = self.component.getNewConfig(name)
        self.configsNotebook.addParamSet(newConfig, name)
        
        # enable remove button
        self.enableButton(self.removeConfigBtn, 'notEnoughConfigs')
        
    def onRemoveConfig(self, event=None):
        if self.configsNotebook.getCurrentSetName() == 'standard':
            showError("'standard' config cannot be removed")
            return
        self.configsNotebook.removeCurrentSet()

        # Disable the remove button if only one config left
        if self.configsNotebook.GetPageCount() < 2:
            self.disableButton(self.removeConfigBtn, 'notEnoughConfigs')
            
    def checkName(self, event=None):
        """
        Checkes whether all the configs of this routine
        have a different name. Overwrites the method of _BaseParamsDlg.
        """
        label = ""
        # TODO (code quality) merge this somehow with parent function
        newName = self.paramCtrls['name'].getValue()
        if newName == '':
            label = "Missing name"
            self.disableButton(self.OKbtn, 'mainNameWrong')
        elif newName.lower() == 'name':
            label = "'name' is reserved"
            self.disableButton(self.OKbtn, 'mainNameWrong')
        else:
            used = self.frame.exp.getUsedName(newName)
            if used != None and used != self.nameObject:
                # Disallow this name if it's not the name of the nameObject itself
                label = "Name '%s' is already used by a %s" % (newName, used.getType())
                self.disableButton(self.OKbtn, 'mainNameWrong')
            else:
                self.enableButton(self.OKbtn, 'mainNameWrong')
        
        # Get all the names currently set
        names = [ctrlSet['name'].getValue() for ctrlSet in self.paramSetNotebooks[0].paramSetCtrls.itervalues() if 'name' in ctrlSet]
        if '' in names:
            label = "Missing name"
            self.disableButton(self.OKbtn, 'namesWrong')
            self.disableButton(self.removeConfigBtn, 'namesWrong')
        elif sorted(names) != sorted(list(set(names))):
            label = "All names must be different"
            self.disableButton(self.OKbtn, 'namesWrong')
            self.disableButton(self.removeConfigBtn, 'namesWrong')
        else:
            # All good, enable the ok button
            self.enableButton(self.OKbtn, 'namesWrong')
            self.enableButton(self.removeConfigBtn, 'namesWrong')
        self.nameOKlabel.SetLabel(label)
            
    def _addAllToMainsizer(self):
        # Overwrite this method because we do a bit more complicated things here
        
        # Add the normal params
        self.mainSizer.Add(self.ctrlSizer, proportion = 0, flag=wx.EXPAND|wx.TOP, border=15)
        
        # Add all the notebooks and corresponding buttons with lines in between
        self.mainSizer.Add(wx.StaticLine(self), proportion = 0, flag=wx.GROW|wx.TOP, border=5)
        self.mainSizer.Add(self.configsNotebook, proportion = 1, flag=wx.EXPAND|wx.TOP, border=5)
        self.mainSizer.Add(self.configBtns, proportion = 0, flag=wx.ALIGN_RIGHT)
        self.mainSizer.Add(wx.StaticLine(self), proportion = 0, flag=wx.GROW|wx.TOP, border=5)
        
        # Name OK label and buttons
        self.mainSizer.Add(self.nameOKlabel, proportion = 0, flag=wx.ALIGN_RIGHT|wx.RIGHT, border = 10)
        self.mainSizer.Add(self.buttons, proportion = 0, flag=wx.ALIGN_RIGHT)
        
        
        
class DlgComponentTimelineProperties(_BaseParamsDlg):
    def __init__(self, frame, title, componentTimeline, affectedConditions, routine,
            helpUrl=None, pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT|wx.RESIZE_BORDER):
        _BaseParamsDlg.__init__(self, frame, title, {}, [], doNameCheck=False, 
                                helpUrl=helpUrl, pos=pos, size=size, style=style)
        self.componentTimeline = componentTimeline
        self.dialogWidth += self.dpi # make dialog a bit wider because we have the 'as in standard' checkboxes
        
        self.activationsNotebook = None
        self.displayTimesNotebook = None
        
        # Note to say which timelines are being edited
        self.noteText = wx.StaticText(self, 
            label='You are editing the timeline of compontent "%s" affecting conditions "%s" of routine "%s".' % 
                (self.componentTimeline.component.getName(),
                '", "'.join(affectedConditions),
                routine.getName()))
        self.noteText.Wrap(self.dialogWidth)
        
        # Add the display time controls
        if self.componentTimeline.isDrawable():
            displayTimeHandlers = {} 
            for displayTime in self.componentTimeline._displayTimes:
                displayTimeHandlers[displayTime.getName()] = displayTime
            self.displayTimesNotebook = self.addParamNotebook(displayTimeHandlers)
        
        # Add the activation controls
        activationHandlers = {} 
        for activation in self.componentTimeline._activations:
            activationHandlers[activation.getName()] = activation
        self.activationsNotebook = self.addParamNotebook(activationHandlers)
        
        # Add the remove and add activation buttons
        addActivationBtn = wx.Button(self, wx.ID_ADD, "Add Activation")
        addActivationBtn.Bind(wx.EVT_BUTTON, self.onAddActivation)
        self.removeActivationBtn = wx.Button(self, wx.ID_REMOVE, "Remove Activation")
        self.removeActivationBtn.Bind(wx.EVT_BUTTON, self.onRemoveActivation)
        if len(self.componentTimeline._activations) < 2:
            self.removeActivationBtn.Disable()
        self.activationBtns = wx.StdDialogButtonSizer()
        self.activationBtns.Add(addActivationBtn, 0, wx.ALL, border=3)
        self.activationBtns.Add(self.removeActivationBtn, 0, wx.ALL, border=3)
        
        if self.componentTimeline.isDrawable():
            # Add the remove and add display buttons
            addDisplayTimeBtn = wx.Button(self, wx.ID_ADD, "Add Display Time")
            addDisplayTimeBtn.Bind(wx.EVT_BUTTON, self.onAddDisplayTime)
            self.removeDisplayTimeBtn = wx.Button(self, wx.ID_REMOVE, "Remove Display Time")
            self.removeDisplayTimeBtn.Bind(wx.EVT_BUTTON, self.onRemoveDisplayTime)
            if len(self.componentTimeline._displayTimes) < 2:
                self.removeDisplayTimeBtn.Disable()
            self.displayTimeBtns = wx.StdDialogButtonSizer()
            self.displayTimeBtns.Add(addDisplayTimeBtn, 0, wx.ALL, border=3)
            self.displayTimeBtns.Add(self.removeDisplayTimeBtn, 0, wx.ALL, border=3)

        # show the dialog and get the params
        self.show()
        if self.OK:
            self.getParams() # get new vals from dlg
            
            activations = [activation for activation in self.activationsNotebook.paramSets.itervalues()]
            # Update the activations and display times
            self.componentTimeline.updateActivations(activations)
            if self.componentTimeline.isDrawable():
                displays = [dispTime for dispTime in self.displayTimesNotebook.paramSets.itervalues()]
                self.componentTimeline.updateDisplayTimes(displays)
            
                # BHBN ; test validity of timings and warn in case of problem.
                # test every display time
                noproblem = True
                for d in displays:
                    # test every activation to find one starting before the display time
                    display_activated = False
                    for a in activations:
                        if d.params['startTime'].val >= a.params['startTime'].val:
                            # found one activation before display; good
                            display_activated = True
                            break
                    # did not find an activation before display ; bad
                    if not display_activated:
                        noproblem = False
                        break
    
                if not noproblem:
                    dlg = MessageDialog(self, 'Invalid display and activation timings;\na module should be activated once before being displayed.\n\nThere might be problems at runtime.', type='Info')
                    dlg.Destroy()
        
    def onAddActivation(self, event=None):
        """
        Adds a new activation to the dialog and
        switches the focus to the new activation
        """
        # get the new condition and add the ctrls
        newAactivation = self.componentTimeline.getNewActivation(num=self.activationsNotebook.GetPageCount()+1)
        self.activationsNotebook.addParamSet(newAactivation, newAactivation.getName())
        
        # enable remove button
        if self.activationsNotebook.GetPageCount() > 1:
            self.removeActivationBtn.Enable()
        
    def onRemoveActivation(self, event=None):
        self.activationsNotebook.removeCurrentSet()

        # hide the remove button if only one activation left
        if self.activationsNotebook.GetPageCount() < 2:
            self.removeActivationBtn.Disable()
            
    def onAddDisplayTime(self, event=None):
        """
        Adds a new display time to the dialog and
        switches the focus to the new time
        """
        # get the new display time and add the ctrls
        newDispTime = self.componentTimeline.getNewDisplayTime(num=self.displayTimesNotebook.GetPageCount()+1)
        self.displayTimesNotebook.addParamSet(newDispTime, newDispTime.getName())
        
        # enable remove button
        if self.displayTimesNotebook.GetPageCount() > 1:
            self.removeDisplayTimeBtn.Enable()
        
    def onRemoveDisplayTime(self, event=None):
        self.displayTimesNotebook.removeCurrentSet()

        # hide the remove button if only one display time left
        if self.displayTimesNotebook.GetPageCount() < 2:
            self.removeDisplayTimeBtn.Disable()
            
    def _addAllToMainsizer(self):
        self.mainSizer.Add(self.noteText, flag=wx.EXPAND|wx.ALL, border=5)
        # Add all the notebooks and corresponding buttons with lines in between
        if self.displayTimesNotebook != None:
            self.mainSizer.Add(self.displayTimesNotebook, flag=wx.EXPAND)
            self.mainSizer.Add(self.displayTimeBtns, flag=wx.ALIGN_RIGHT)
            self.mainSizer.Add(wx.StaticLine(self), 0, flag=wx.EXPAND|wx.ALL, border=5)
        self.mainSizer.Add(self.activationsNotebook, flag=wx.EXPAND)
        self.mainSizer.Add(self.activationBtns, flag=wx.ALIGN_RIGHT)
        self.mainSizer.Add(wx.StaticLine(self), 0, flag=wx.EXPAND|wx.ALL, border=5)
        self.mainSizer.Add(self.buttons, flag=wx.ALIGN_RIGHT)    



class DlgLoggerSettings(_BaseParamsDlg):
    def __init__(self, frame,  
            pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT|wx.RESIZE_BORDER):
        title = 'Logger Settings'
        params = frame.exp.loggerSettings.params
        order = frame.exp.loggerSettings.order
        _BaseParamsDlg.__init__(self, frame, title, params, order, doNameCheck=False,
                                pos=pos, size=size, style=style)

        # show dialog and get the data
        self.show()
        if self.OK:
            self.getParams() # get new vals from dlg
        


class DlgDisplaySettings(_BaseParamsDlg):
    def __init__(self, frame,  
            pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT|wx.RESIZE_BORDER):
        camParams = frame.exp.cameraSettings.params
        camOrder = frame.exp.cameraSettings.order
        _BaseParamsDlg.__init__(self, frame, 'Display Settings', camParams, camOrder, 
                                doNameCheck=False, pos=pos, size=size, style=style)
                
        # Set the different sets of params
        setHandlers = self.exp.windowSettings
        self.addParamNotebook(setHandlers)
        
        # Add the remove and add window buttons
        addWindowBtn = wx.Button(self, wx.ID_ADD, "Add Window")
        addWindowBtn.Bind(wx.EVT_BUTTON, self.onAddWindow)
        self.addButton(addWindowBtn)
        self.removeWindowBtn = wx.Button(self, wx.ID_REMOVE, "Remove Window")
        self.removeWindowBtn.Bind(wx.EVT_BUTTON, self.onRemoveWindow)
        if self.paramSetNotebooks[0].GetPageCount() < 2:
            self.removeWindowBtn.Disable()
        self.addButton(self.removeWindowBtn)

        # Show dialog and get the data
        self.show()
        if self.OK:
            self.getParams() # get new vals from dlg
            # TODO: (minor) naming is off when removing another display than the last
            self.exp.windowSettings = self.paramSetNotebooks[0].paramSets
        
    def onModeChanged(self):
        print "mode changed"
        
    def onAddWindow(self, event=None):
        """
        Adds a new window setting to the experiment and switches the current 
        param set to the newly created ones
        """
        newSetting, newName = self.exp.getNewWindowSetting(num=self.paramSetNotebooks[0].GetPageCount()+1)
        self.paramSetNotebooks[0].addParamSet(newSetting, newName)
         
        # enable remove button
        self.removeWindowBtn.Enable()
        
    def onRemoveWindow(self, event=None):
        """
        Removes the currently selected window from the experiment
        """
        self.paramSetNotebooks[0].removeCurrentSet()

        # disable the remove button if only one window left
        if self.paramSetNotebooks[0].GetPageCount() < 2:
            self.removeWindowBtn.Disable()



class DlgRoutineProperties(_BaseParamsDlg):
    def __init__(self, frame, possPoints, id=-1, title='Add a routine', routine=None,
            helpUrl=None, pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT|wx.RESIZE_BORDER):
        # Set the routine or create a new one
        if routine == None:
            self.routine = experiment.Routine(exp=frame.exp, name='routine')
            currentPos = str(len(frame.exp.flow))
        else:
            self.routine = routine
            currentPos = str(frame.exp.flow.index(self.routine))
        
        # Initalise the dlg        
        _BaseParamsDlg.__init__(self, frame, title, self.routine.params, self.routine.order,
                                nameObject=self.routine, helpUrl=helpUrl, pos=pos, size=size, style=style)

        # Position choices
        self.paramCtrls['position'] = _PositionCtrls(dlg=self, parent=self, label='position', positions=possPoints)
        self.ctrlSizer.Add(self.paramCtrls['position'].nameCtrl, (self.currRow, 0), flag=wx.ALIGN_LEFT|wx.RIGHT|wx.LEFT, border=5)
        self.ctrlSizer.Add(self.paramCtrls['position'].valueCtrl, (self.currRow, 1), flag=wx.EXPAND|wx.ALL, border=2)
        self.currRow += 1
        self.paramCtrls['position'].setValue(currentPos)

        # Show dialog and get the data
        self.show()
        if self.OK:
            # Get new vals from dlg
            self.getParams()
    
    def getPosition(self):
        return self.paramCtrls['position'].getValue()



class DlgSelectComponentsImport(_BaseParamsDlg):
    
    def __init__(self, frame, listcomponents, id=-1, title='Select components to import',
            helpUrl=None, pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT|wx.RESIZE_BORDER):
        self.listcomponents = listcomponents
        params = {}
        order = []
        for c in self.listcomponents:
            params[c] = Param(True, valType='bool', hint="check to keep this component")
            order.append(c)
            
        # Initalise the dlg
        _BaseParamsDlg.__init__(self, frame, title, params, order,
            doNameCheck=False, helpUrl=helpUrl, pos=pos, size=size, style=style)
                        
        # Create the explanation text
        self.explanationText = wx.StaticText(self, 
            label="Select the components from this file which you want to import:\n", 
            size=(self.dialogWidth, 40))
        
        # show dialog and get the data
        self.show()
        if self.OK:
            self.getParams() # get new vals from dlg
                
    def _addAllToMainsizer(self):
        self.mainSizer.Add(self.explanationText, flag=wx.ALL, border=5)
        _BaseParamsDlg._addAllToMainsizer(self)
        
class DlgGenAllInstances(_BaseParamsDlg):
    max_num_instances = 30
    
    def __init__(self, frame, flow, id=-1, title='Generate many instances',
            helpUrl=None, pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT|wx.RESIZE_BORDER):
        # Get the loops that are shuffled from the flow
        self.flow = flow
        params = {}
        order = []
        for flowElement in self.flow:
            if flowElement.getType() == 'LoopInitiator' and flowElement.loop.generateAll:
                name = flowElement.loop.getName() 
                hint = "This loop has %i repetitions" % flowElement.loop.getNumReps()
                params[name] = Param(True, valType='bool', hint=hint)
                order.append(name)
                
        name = 'Maximum'
        params[name] =  Param(self.max_num_instances, valType='int', hint="How many instance to generate at most")
        order.append(name)
                        
        # Initalise the dlg
        _BaseParamsDlg.__init__(self, frame, title, params, order,
            doNameCheck=False, helpUrl=helpUrl, pos=pos, size=size, style=style)
        
        # Bind the checkbox changes to re-calculate the number of instances
        for ctrls in self.paramCtrls.itervalues():
            ctrls.valueCtrl.Bind(wx.EVT_CHECKBOX, self._checkNotTooManyInstances)
            ctrls.valueCtrl.Bind(wx.EVT_KEY_UP, self._checkNotTooManyInstances)
        
        # Create the explanation text
        self.explanationText = wx.StaticText(self, 
            label="Select the shuffle and factorial loops to generate all possible randomisations of.", 
            size=(self.dialogWidth, 40))
        self.instanceNumberText = wx.StaticText(self, label='', size=(self.dialogWidth, 40))
        self.noteText = wx.StaticText(self, 
            label="Note: No files will be overwritten. If you want to get rid of old instance files, delete them first.",
            size=(self.dialogWidth, 40))
            
        # Check if it's OK to generate that many instances
        self._checkNotTooManyInstances()

        # show dialog and get the data
        self.show()
        if self.OK:
            self.getParams() # get new vals from dlg
            
        
    def _checkNotTooManyInstances(self, evt=None):
        """
        Gets the amount of instances that would be generated with the current
        settings. Based on that is sets the label and enables or disables the
        OK button.
        """
        v = self.paramCtrls['Maximum'].getValue()
        self.max_num_instances = int(v) if len(v) else 0
        # Check that there is at least one loop selected
        hasSelectedLoop = False
        for ctrls in self.paramCtrls.itervalues():
            if ctrls.getValue() == True:
                hasSelectedLoop = True
                break
        if not hasSelectedLoop:
            self.instanceNumberText.SetLabel("Select at least one loop")
            self.OKbtn.Disable()
            return
        
        num = self._recursiveCalcNumberOfInstances(0)[0]        
        
        if num > self.max_num_instances:
            # Too many
            if num > 2000:
                label = "On the thouthands of combinations overall,\n"
            else:
                label = "On the %d combinations overall,\n" %  num
        else:
            label = "\n"
            self.max_num_instances = num
 
        label += "%d instances will be created." % self.max_num_instances
        self.instanceNumberText.SetLabel(label)
        self.OKbtn.Enable()
            
    def _recursiveCalcNumberOfInstances(self, index):
        """
        Calculates how many instances would be generated with the current
        settings. Recurively goes through the flow of the experiment
        """
        multiplier = 1
        while index < len(self.flow):
            if self.flow[index].getType() == 'LoopTerminator':
                # This loop is over, return
                break
            if self.flow[index].getType() == 'LoopInitiator':
                # Found a loop initator, start next recursion
                innerResult = self._recursiveCalcNumberOfInstances(index + 1)
                multiplier *= innerResult[0]
                
                loop = self.flow[index].loop
                if innerResult[0] > 1:
                    # If the inner loop has more than one possibility it has even 
                    # more now due to the repetition of this loop
                    multiplier **= loop.getNumReps()

                if loop.generateAll and self.paramCtrls[loop.getName()].getValue():
                    #
                    if loop.getNumReps() > 20:
                        # No need to calculate the factorial, will be too much anyway
                        multiplier = self.max_num_instances
                        break
                    multiplier *= math.factorial(loop.getNumReps())
                    
                if multiplier >= self.max_num_instances:
                    # No need to go any further
                    break
                index = innerResult[1]
            index += 1
        return (multiplier, index)
    
    def _addAllToMainsizer(self):
        self.mainSizer.Add(self.explanationText, flag=wx.ALL, border=5)
        _BaseParamsDlg._addAllToMainsizer(self)
        # Insert the text just before the buttons
        self.mainSizer.Insert(len(self.mainSizer.Children) - 1, 
            self.instanceNumberText, flag=wx.ALL, border=5)
        self.mainSizer.Insert(len(self.mainSizer.Children) - 1, 
            self.noteText, flag=wx.ALL, border=5)



class MessageDialog(wx.Dialog):
    """
    This is for general purpose dialogs, not related to particular functionality
    (For some reason the wx builtin message dialog has some issues on Mac OSX
    (buttons don't always work) so we need to use this instead.)
    """
    def __init__(self, parent=None, message='', type='Warning', title=None):
        if title == None:
            title = type
        wx.Dialog.__init__(self, parent, -1, title=title)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, -1, message, style=wx.ALIGN_LEFT), flag=wx.ALL, border=10)
        # add buttons
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        if type == 'Warning': # we need Yes, No, Cancel
            self.yesBtn = wx.Button(self, wx.ID_YES, 'Yes')
            self.yesBtn.SetDefault()
            self.cancelBtn = wx.Button(self, wx.ID_CANCEL, 'Cancel')
            self.noBtn = wx.Button(self, wx.ID_NO, 'No')
            self.Bind(wx.EVT_BUTTON, self.onButton, id=wx.ID_CANCEL)
            self.Bind(wx.EVT_BUTTON, self.onButton, id=wx.ID_YES)
            self.Bind(wx.EVT_BUTTON, self.onButton, id=wx.ID_NO)
            btnSizer.Add(self.noBtn, wx.ALIGN_LEFT)
            btnSizer.Add((60, 20), 0, wx.EXPAND)
            btnSizer.Add(self.cancelBtn, wx.ALIGN_RIGHT)
            btnSizer.Add((5, 20), 0)
            btnSizer.Add(self.yesBtn, wx.ALIGN_RIGHT)
        elif type == 'Info': # just an OK button
            self.okBtn = wx.Button(self,wx.ID_OK,'OK')
            self.okBtn.SetDefault()
            self.Bind(wx.EVT_BUTTON, self.onButton, id=wx.ID_OK)
            btnSizer.Add(self.okBtn, wx.ALIGN_RIGHT)
        # configure sizers and fit
        sizer.Add(btnSizer, flag=wx.ALIGN_RIGHT|wx.ALL, border=5)
        self.SetSizerAndFit(sizer)
        self.Center()
        
    def onButton(self,event):
        self.EndModal(event.GetId())