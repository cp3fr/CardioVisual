# -*- coding: utf-8 -*-
#===============================================================================
# Copyright (c) 2009-2011 EPFL (Ecole Polytechnique federale de Lausanne) 
# Laboratory of Cognitive Neuroscience (LNCO) 
# 
# ExpyVR is free software ; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation ; either version 2 of the License, or (at your option) any later version.
# 
# ExpyVR is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY ; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with ExpyVR ; if not, write to the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA.
# 
# Authors : Tobias Leugger leugger.tobias@web.de
#          Bruno Herbelin bruno.herbelin@epfl.ch
#          Nathan Evans   nathan.evans@epfl.ch
# Web site : http://lnco.epfl.ch/expyvr
#===============================================================================

'''
runexperiment.py
Stand-alone script to execute an instance of experiment generated with ExpyVR
@author: Bruno
'''

import sys
import os

# Ensure 2.8 version of wx
if not hasattr(sys, 'frozen'):
	import wxversion
	wxversion.ensureMinimal('2.8')
import wx

#We have to modify PYTHONPATH to include the sources tree
sys.path.append(os.path.normpath( os.path.abspath(os.curdir) + '/../../src') )

from controller import maincontrol, getPathFromString
from expbuilder.app.errors import storeTracebackAndShowError

class MySplashScreen(wx.SplashScreen):
	def __init__(self, parent=None):
		aBitmap = wx.Image(name = getPathFromString("$EXPYVRROOT$/expyvr/resources/splash.png")).ConvertToBitmap()
		wx.SplashScreen.__init__(self, aBitmap, wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT, 10000, parent)
		wx.Yield()

app = wx.App(redirect=False)
	
arg = ''
if len(sys.argv) > 1:
	if os.path.isabs(sys.argv[1]): # if this is an absolute path
		arg = sys.argv[1]
	else:
		arg = os.path.normpath( os.path.abspath(os.curdir) + '/' + sys.argv[1])
else :
	print("No experiment instance file specified, asking with file browser")

	if sys.platform == 'darwin':
		wildcard = "ExpyVR instances (*.inst.xml)|*.inst.xml|Any file (*.*)|*"
	else:
		wildcard = "ExpyVR instances (*.inst.xml)|*.inst.xml|Any file (*.*)|*.*"
	
	dlg = wx.FileDialog(None, message="Select instance to run ...", defaultDir=os.getcwd(),
										style=wx.FD_OPEN | wx.FD_CHANGE_DIR, wildcard=wildcard)
	
	if dlg.ShowModal() == wx.ID_OK:
		arg = dlg.GetPath()
	else:
		sys.exit(2)
		
print("Trying experiment " + arg)
#os.environ['INSTDIR'] = os.path.dirname(arg)

MySplash = MySplashScreen()
MySplash.Show()

cont = maincontrol.MainControl()
try:
	# Try to load the experiment
	cont.loadExperiment(arg)
except:
	MySplash.Hide()
	storeTracebackAndShowError("Error during loading of experiment %s."%arg)
	app.Yield()
	sys.exit(-1)

MySplash.Hide()
app.Yield()

closeWindowOnExit = False
# test for second parameter
if len(sys.argv) > 2:
	if sys.argv[2] == '-closeWindows':
		closeWindowOnExit = True
try:
	# Try to run the experiment
	cont.startExperiment(closeWindowOnExit)
except:
	storeTracebackAndShowError("Error during execution of experiment %s."%arg)
	app.Yield()
	sys.exit(-1)
