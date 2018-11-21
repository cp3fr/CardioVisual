"""
@author: Tobias Leugger
@since: Spring 2010

@attention: Adapted from parts of the PsychoPy library
@copyright: 2009, Jonathan Peirce, Tobias Leugger
@license: Distributed under the terms of the GNU General Public License (GPL).
"""

import wx
#create wx event/object IDs
exit=wx.NewId()

#experiment menu
logSettings = wx.NewId()
dispSettings = wx.NewId()
addRoutineToFlow = wx.NewId()
addLoopToFlow = wx.NewId()
addIsiToFLow = wx.NewId()
remRoutineFromFlow = wx.NewId()
remLoopFromFlow = wx.NewId()
testRoutine = wx.NewId();
testExperiment = wx.NewId();
genInstance = wx.NewId()
genAllInstances = wx.NewId()
runInstance = wx.NewId()
rerunInstance = wx.NewId()
componentFileImport = wx.NewId()

#view menu
openBuilderView = wx.NewId()

#help menu
#these should be assigned to the relevant buttons/menu items in the app
#AND for those with weblinks the relevant URL should be provided at top of psychopyApp.py
about = wx.NewId()
license = wx.NewId()
builderHelp = wx.NewId()
expyvrTrac = wx.NewId()
expyvrHome = wx.NewId()
api = wx.NewId()
#help pages (from help buttons)
docsPrefsDlg = wx.NewId()

#toolbar IDs
tbFileNew = 10
tbFileOpen = 20
tbFileSave = 30
tbFileSaveAs = 40
tbUndo = 50
tbRedo = 60
tbLogSettings = 70
tbDispSettings = 80
tbRun = 90
tbGen = 100
tbTest = 110
tbTestroutine = 120

