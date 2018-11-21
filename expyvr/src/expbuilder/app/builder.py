"""
@author: Tobias Leugger
@since: Spring 2010

@attention: Adapted from parts of the PsychoPy library
@copyright: 2009, Jonathan Peirce, Tobias Leugger
@license: Distributed under the terms of the GNU General Public License (GPL).
"""

import sys, os

#We have to modify PYTHONPATH to include the sources tree
sys.path.append(os.path.normpath( os.path.abspath(os.curdir) + '/../../') )

# Ensure 2.8 version of wx
if not hasattr(sys, 'frozen'):
    import wxversion
    wxversion.ensureMinimal('2.8')
    
from lxml import etree
import numpy, subprocess, time
import wx.aui, wx.lib.scrolledpanel as scrolled
from copy import deepcopy

import expbuilder, components, wxIDs, urls
from expbuilder import preferences
from dialogs import *
from errors import storeTracebackAndShowError, showInfo
from controller import getPathFromString

# colour for the background of the canvas
canvasColour = wx.Colour(213, 213, 213)

componentActivationColour = wx.Colour(50, 50, 200)
componentDisplayTimeColour = wx.Colour(200, 50, 50)

class _ScrolledCanvas(wx.ScrolledWindow):
    """
    Abstract class to group functionality for painting on a scrolled canvas,
    and for being able to select element with mouse clicks, as well as having
    context menus
    """
    def __init__(self, mainFrame, parent, size=wx.DefaultSize, style=0, contextMenuItems=[]):
        self.frame = mainFrame
        self.app = self.frame.app
        self.dpi = self.app.dpi
        wx.ScrolledWindow.__init__(self, parent, size=size, style=style)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.SetBackgroundColour(canvasColour)

        # create a PseudoDC to record our drawing
        self.pdc = wx.PseudoDC()

        # for the context menu
        self._menuObject = None
        self._objectFromID = {} # use the ID of the drawn icon to retrieve component (loop or routine)
        self._contextMenuItems = contextMenuItems
        self._contextItemFromID = {};
        self._contextIDFromItem = {}
        for item in self._contextMenuItems:
            id = wx.NewId()
            self._contextItemFromID[id] = item
            self._contextIDFromItem[item] = id

        # bind events
        self.Bind(wx.EVT_LEFT_DOWN, self._onMouse)
        self.Bind(wx.EVT_RIGHT_DOWN, self._onMouse)
        self.Bind(wx.EVT_PAINT, self._onPaint)

        # set scroll rate
        self.SetScrollRate(self.dpi/4, self.dpi/4)

    def _convertEventCoords(self, event):
        xView, yView = self.GetViewStart()
        xDelta, yDelta = self.GetScrollPixelsPerUnit()
        return (event.GetX() + (xView * xDelta),
            event.GetY() + (yView * yDelta))
        
    def _onMouse(self, event):
        if not event.RightDown() and not event.LeftDown():
            return
        x, y = self._convertEventCoords(event)
        objects = self.pdc.FindObjectsByBBox(x, y)
        if len(objects):
            self._menuObject = self._objectFromID[objects[0]]
            position = wx.Point(max(event.GetX() - 5, 0), max(event.GetY() - 5, 0))
            self._showContextMenu(position, self._getContextMenuItems(self._menuObject))
   
    def _getContextMenuItems(self, object):
        """
        Returns the names of the context menu items to include for this object.
        Can be overwritten in a child class. Only items that were given in the
        init can be returned here.
        """
        return self._contextMenuItems
            
    def _showContextMenu(self, xy, items):
        menu = wx.Menu()
        for item in items:
            id = self._contextIDFromItem[item]
            menu.Append(id, item)
            wx.EVT_MENU(menu, id, self._onContextSelect)
        self.PopupMenu(menu, xy)
        menu.Destroy() # destroy to avoid mem leak
        
    def _onContextSelect(self, event):
        self._onContextAction(self._contextItemFromID[event.GetId()], self._menuObject)
        self._menuObject = None
        
    def _onContextAction(self, action, object):
        """
        This function should be implemented in the child class.
        It is called when a certain action in a context menu is
        selected for a certain object
        """
        pass

    def _onPaint(self, event):
        # Create a buffered paint DC.  It will create the real
        # wx.PaintDC and then blit the bitmap to it when dc is deleted.
        dc = wx.AutoBufferedPaintDC(self)
        # we need to clear the dc BEFORE calling PrepareDC
        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()
        # use PrepateDC to set position correctly
        self.PrepareDC(dc)
        self.pdc.DrawToDC(dc)



class MenuFrame(wx.Frame):
    """
    A simple, empty frame with a menubar that should be the last frame to close on a mac
    """
    def __init__(self, parent=None, ID=-1, app=None, title="ExpyVR Experiment Builder"):
        wx.Frame.__init__(self, parent, ID, title, size=(1,1))
        self.app=app

        self.menuBar = wx.MenuBar()

        self.viewMenu = wx.Menu()
        self.menuBar.Append(self.viewMenu, '&View')
        self.viewMenu.Append(self.app.IDs.openBuilderView, "&Open Builder view\t%s" %self.app.keys['switchToBuilder'], "Open a new Builder view")
        wx.EVT_MENU(self, self.app.IDs.openBuilderView,  self.app.showBuilder)
        item=self.viewMenu.Append(wx.ID_EXIT, "&Quit\t%s" %self.app.keys['quit'], "Terminate the program")
        self.Bind(wx.EVT_MENU, self.app.quit, item)

        self.SetMenuBar(self.menuBar)
        self.Show()



class App(wx.App):
    def OnInit(self):
        self.version = expbuilder.__version__
        self.SetAppName('ExpyVR Experiment Builder')
        
        # set default paths and prefs
        self.prefs = preferences.Preferences() # from preferences.py
        self.keys = self.prefs.keys
        self.prefs.pageCurrent = 0  # track last-viewed page of prefs, to return there
        self.IDs = wxIDs
        self.urls = urls.urls
        self.quitting = False
        
        # change the cwd to the default save path
        os.chdir(self.prefs.paths['defaultSavePath'])

        #setup links for URLs
        #on a mac, don't exit when the last frame is deleted, just show a menu
        if sys.platform == 'darwin':
            self.menuFrame = MenuFrame(parent=None, app=self)
        
        self.dpi = int(wx.GetDisplaySize()[0]/float(wx.GetDisplaySizeMM()[0])*25.4)
        if not (50 < self.dpi < 120): 
            self.dpi = 80 # dpi was unreasonable, make one up
        
        # Import all the basic components
        components.importAllComponents(hiddenComponents=self.prefs.builder['hiddenComponents'])

        # Import extra components
        componentspaths = self.prefs.builder['componentsPath'].split(';')
        for comppath in componentspaths:
            compdir = os.path.abspath(getPathFromString(comppath))
            if os.path.isdir(compdir) and os.path.isfile( os.path.join( compdir, 'components.xml') ):
                # modify PYTHONPATH to include the components path given
                sys.path.append(compdir)
                # load components described in xml
                components.importAllComponents( os.path.join(compdir, "components.xml") )
            else:
                showInfo('''Component folder '%s' could not be found.\nIt will be ignored in the future.
                        \n\nTo set another extra components path, go to File/Preferences.''' % compdir)
                
                componentspaths.remove(comppath)
                self.prefs.saveUserPrefs()

        self.prefs.builder['componentsPath']  = ';'.join(componentspaths)

        # create frame for builder
        self.builder = None
        self.showBuilder()

        return True

    def showBuilder(self, event=None, fileList=None):
        if self.builder == None:
            self.builder = BuilderFrame(None, -1, title="ExpyVR Experiment Designer", files=fileList, app=self)
        self.builder.Show(True)
        self.builder.Raise()
        self.SetTopWindow(self.builder)
            
    def quit(self, event=None):
        self.quitting = True
        # see whether any files need saving
        for frame in [self.builder]:
            if frame == None: continue
        ok = self.builder.checkSave()
        if not ok:
            return # user cancelled quit
        
        # hide the frames then close
        for frame in [self.builder]:
            if frame == None:
                continue
            frame.closeFrame(checkSave=False) # should update (but not save) prefs.appData
            self.prefs.saveAppData() # must do this before destroying the frame?
            frame.Destroy() # because closeFrame actually just Hides the frame
        if sys.platform == 'darwin':
            self.menuFrame.Destroy()
        sys.exit() #really force a quit
        
    def showPrefs(self, event):
        prefsDlg = preferences.PreferencesDlg(app=self)
        prefsDlg.Show()

    def showAbout(self, event):
        msg = """Program for VR stimulus generation and experimental control in python.
        
ExpyVR is based on the PsychoPy project ; http://www.psychopy.org.
        
ExpyVR is developed at the Laboratory of Cognitive Neuroscience in EPFL (CH).
        """
        info = wx.AboutDialogInfo()
        info.SetName('ExpyVR Experiment Builder')
        info.SetVersion('v'+expbuilder.__version__)
        info.SetDescription(msg)
        info.SetCopyright('(C) 2009-2012 LNCO')
        info.SetWebSite('http://lnco.epfl.ch')
        info.AddDeveloper('Tobias Leugger')
        info.AddDeveloper('Nathan Evans')
        info.AddDeveloper('Bruno Herbelin')
        
        licFile = open(os.path.join(getPathFromString('$EXPYVRROOT$/expyvr/src/expbuilder'),'LICENSE.txt'))
        license = licFile.read()
        licFile.close()
        info.SetLicence(license)

        wx.AboutBox(info)

    def followLink(self, event=None, url=None):
        """
        Follow either an event id (which should be a key to a url defined in urls.py)
        or follow a complete url (a string beginning "http://")
        """
        if event!=None:
            wx.LaunchDefaultBrowser(self.urls[event.GetId()])
        elif url!=None:
            wx.LaunchDefaultBrowser(url)
            
            

class FlowPanel(_ScrolledCanvas):
    def __init__(self, frame):
        """
        A panel that shows how the routines will fit together
        """
        _ScrolledCanvas.__init__(self, frame, parent=frame, 
            size=(8*frame.app.dpi, 2*frame.app.dpi), 
            contextMenuItems=['show', 'properties', 'remove', 'move left', 'move right'])

        # If we're adding a loop or routine then add spots to timeline
        self.pointsToDraw = [] # Lists the x-vals of points to draw, eg loop locations

        # Create insert buttons
        self.btnInsertRoutine = wx.Button(self, label='Add Routine', pos=(2, 2))
        btnSize = self.btnInsertRoutine.GetSize()
        btnHeight = btnSize[1]
        self.btnInsertLoop = wx.Button(self, label='Add Loop', pos=(2, 2 + btnHeight), size=btnSize)
        self.btnInsertIsi = wx.Button(self, label='Add ISI', pos=(2, 2 + 2*btnHeight), size=btnSize)
        
        # Set size constants for drawing
        self.gap = self.dpi/2
        self.linePos = (btnSize[0]+20+self.gap, self.dpi)
        self.loopHeight = int ( self.dpi / 2.5)

        # bind events
        self.Bind(wx.EVT_MOUSE_EVENTS, self._onMouse)
        self.Bind(wx.EVT_BUTTON, self._onInsertRoutine, self.btnInsertRoutine)
        self.Bind(wx.EVT_BUTTON, self._onInsertLoop, self.btnInsertLoop)
        self.Bind(wx.EVT_BUTTON, self._onInsertIsi, self.btnInsertIsi)

        self.redrawFlow()

    def _onInsertRoutine(self, evt):
        """
        Handles the insert routine button.
        Shows a dialog to insert a name and a position of a new routine
        """        
        # add routine points to the timeline
        self._setDrawPoints('routines')
        self.redrawFlow()

        # bring up listbox to choose the routine to add and/or create a new one
        addRoutineDlg = DlgRoutineProperties(frame=self.frame, possPoints=self.pointsToDraw)
        
        if addRoutineDlg.OK:
            routine = addRoutineDlg.routine
            routineName = routine.getName()
            self.frame.exp.addRoutine(routineName, routine) # add to the experiment
            self.frame.exp.flow.addOrMoveElement(routine, addRoutineDlg.getPosition()) # and to the flow
            self.frame.exp.activeRoutine = routine # change this routine to be edited
            self.frame.addToUndoStack("AddRoutine")
            self.frame.routinePanel.redrawConditions(True)
            
        # remove the points from the timeline
        self._setDrawPoints(None)
        self.redrawFlow()

    def _onInsertLoop(self, evt):
        """
        Someone pushed the insert loop button.
        Fetch the dialog
        """
        # Add routine points to the timeline
        self._setDrawPoints('loops')
        self.redrawFlow()

        # Bring up listbox to choose the routine to add and/or create a new one
        loopDlg = DlgLoopProperties(frame=self.frame, possPoints=self.pointsToDraw)

        if loopDlg.OK:
            handler = loopDlg.setHandlers[loopDlg.currentSet]
            start, end = loopDlg.getPositions()
            self.frame.exp.flow.addOrMoveLoop(handler, startPos=start, endPos=end)
            self.frame.addToUndoStack("AddLoopToFlow")
            self.frame.routinePanel.redrawConditions(True)
        
        # Remove the points from the timeline
        self._setDrawPoints(None)
        self.redrawFlow()
        
    def _onInsertIsi(self, evt):
        """
        Someone pushed the insert isi button.
        Fetch the dialog
        """
        # Add routine points to the timeline
        self._setDrawPoints('loops')
        self.redrawFlow()

        # Bring up listbox to choose the routine to add and/or create a new one
        isiDlg = DlgIsiProperties(frame=self.frame, possPoints=self.pointsToDraw)

        if isiDlg.OK:
            position = isiDlg.getPosition()
            self.frame.exp.flow.addOrMoveElement(isiDlg.isiHandler, position)
            self.frame.addToUndoStack("AddIsiToFlow")
            
        # Remove the points from the timeline
        self._setDrawPoints(None)
        self.redrawFlow()
        
    def _editRoutineProperties(self, routine):        
        # Add routine points to the timeline
        self._setDrawPoints('routines')
        self.redrawFlow()

        routineDlg = DlgRoutineProperties(frame=self.frame, possPoints=self.pointsToDraw, 
            title=routine.getName() + ' Properties', routine=routine)
        if routineDlg.OK:
            newPos = routineDlg.getPosition()
            routine = routineDlg.routine
            # Move to new position
            self.frame.exp.flow.addOrMoveElement(routine, newPos)
            self.frame.addToUndoStack("EditRoutine")
            
        # Remove the points from the timeline
        self._setDrawPoints(None)
        self.redrawFlow()

    def _editLoopProperties(self, loop):
        # Add routine points to the timeline
        self._setDrawPoints('routines')
        self.redrawFlow()

        loopDlg = DlgLoopProperties(frame=self.frame, possPoints=self.pointsToDraw,
            title = loop.getName() + ' Properties', loop=loop)
        if loopDlg.OK:
            newStartPos, newEndPos = loopDlg.getPositions()
            newLoop = loopDlg.setHandlers[loopDlg.currentSet]
            if newLoop != loop:
                # If the loop type has changed, remove the old loop
                self.frame.exp.flow.removeComponent(loop)
            self.frame.exp.flow.addOrMoveLoop(newLoop, newStartPos, newEndPos)
            self.frame.addToUndoStack("EditLoop")
            self.frame.routinePanel.redrawConditions(True)
            
        # Remove the points from the timeline
        self._setDrawPoints(None)
        self.redrawFlow()
        
    def _editIsiProperties(self, isi):
        # Add routine points to the timeline
        self._setDrawPoints('loops')
        self.redrawFlow()

        isiDlg = DlgIsiProperties(frame=self.frame, possPoints=self.pointsToDraw, 
            title = isi.getName() + ' Properties', isiHandler=isi) 
        if isiDlg.OK:
            newPos = isiDlg.getPosition()
            self.frame.exp.flow.addOrMoveElement(isi, newPos)
            self.frame.addToUndoStack("EditIsi")
        
        # Remove the points from the timeline
        self._setDrawPoints(None)
        self.redrawFlow()
    
    def _getContextMenuItems(self, object):
        items = copy(self._contextMenuItems)
        if not isinstance(object, experiment.Routine):
            items.remove('show')
        if isinstance(object, loops._BaseLoop):
            items.remove('move left')
            items.remove('move right')
        else:
            # Only show the directions that are possible
            pos = self.frame.exp.flow.index(object)
            if pos == 0:
                items.remove('move left')
            if pos + 1 == len(self.frame.exp.flow):
                items.remove('move right')
            
        return items

    def _onContextAction(self, action, object):
        """
        Perform a given action on the component chosen
        """
        flow = self.frame.exp.flow
        if action == 'show':
            if isinstance(object, experiment.Routine):
                # Bring the selected routine to the foreground
                if self.frame.exp.activeRoutine != object:
                    self.frame.exp.activeRoutine = object
                    self.frame.updateAllViews()
        elif action == 'properties':
            if isinstance(object, experiment.Routine):
                self._editRoutineProperties(routine=object)
            elif isinstance(object, loops._BaseLoop):
                self._editLoopProperties(loop=object)
            elif isinstance(object, experiment.Isi):
                self._editIsiProperties(isi=object)
        elif action == 'remove':
            # Remove it from the flow
            flow.removeComponent(object)
            if isinstance(object, experiment.Routine):
                # If it's a routine also delete it from the experiment and from the routine panel
                self.frame.exp.removeRoutine(object.getName())
            else:
                self.redrawFlow()
            self.frame.updateAllViews()
            self.frame.addToUndoStack("removed %s" % object.getName())
        elif action.startswith('move'):
            pos = self.frame.exp.flow.index(object)
            if action == 'move left':
                pos -= 1
            elif action == 'move right':
                pos += 2    # Have to move by 2 to get somewhere else
            # Move to new position
            self.frame.exp.flow.addOrMoveElement(object, pos)
            self.frame.addToUndoStack("MoveObject")
            self.redrawFlow()
            if isinstance(object, experiment.Routine):
                # If we moved around a routine, redraw the conditions
                self.frame.routinePanel.redrawConditions(True)

    def redrawFlow(self, evt=None):
        if not hasattr(self.frame, 'exp'):
            return # we haven't yet added an exp
        expFlow = self.frame.exp.flow # retrieve the current flow from the experiment
        pdc = self.pdc

        self._objectFromID = {} # use the ID of the drawn icon to retrieve component (loop or routine)

        pdc.Clear() # clear the screen
        pdc.RemoveAll() # clear all objects (icon buttons)
        pdc.BeginDrawing()

        font = self.GetFont()

        # pre-compute number of nested loops
        self.loops = {} # NB the loop is itself the key!? and the value is further info about it
        nestLevel = 0
        LoopDepth = 0        
        for ii, entry in enumerate(expFlow):
            if entry.getType() == 'LoopInitiator':
                self.loops[entry.loop] = {}
                self.loops[entry.loop]['nest'] = nestLevel
                nestLevel += 1 # start of loop so increment level of nesting 
                LoopDepth = max( nestLevel, LoopDepth) 
            elif entry.getType() == 'LoopTerminator':
                nestLevel -= 1 # end of loop so decrement level of nesting

        # set positions
        currX = self.linePos[0]
        self.linePos = (self.linePos[0], self.dpi + max(0,LoopDepth -0.5)*self.loopHeight  )
        
        # draw main line : step through components in flow
        pdc.DrawLine(x1=self.linePos[0]-self.gap, y1=self.linePos[1], x2=self.linePos[0], y2=self.linePos[1])
        self.gapMidPoints=[currX-self.gap/2]
        for ii, entry in enumerate(expFlow):
            if entry.getType() == 'LoopInitiator':
                self.loops[entry.loop]['init'] = currX
                self.loops[entry.loop]['id'] = ii
            elif entry.getType() == 'LoopTerminator':
                self.loops[entry.loop]['term'] = currX 
            elif entry.getType() == 'Routine':
                bold = False
                if self.frame.exp.activeRoutine == entry:
                    bold = True
                currX = self._drawFlowRoutineOrIsi(pdc, entry, id=ii, name=entry.getName(), boldText=bold, pos=[currX,self.linePos[1]-30])
            elif entry.getType() == 'Isi':
                currX = self._drawFlowRoutineOrIsi(pdc, entry, id=ii, name=entry.getName(), rgb=[50,50,50], pos=[currX,self.linePos[1]-30])
            self.gapMidPoints.append(currX+self.gap/2)
            pdc.SetPen(wx.Pen(wx.BLACK))
            pdc.DrawLine(x1=currX, y1=self.linePos[1], x2=currX+self.gap, y2=self.linePos[1])
            currX += self.gap
        
        # draw the loops 
        for thisLoop in self.loops.keys():
            thisInit = self.loops[thisLoop]['init']
            thisTerm = self.loops[thisLoop]['term']
            thisNest = self.loops[thisLoop]['nest']
            thisId = self.loops[thisLoop]['id']
            name = thisLoop.getName()
            self._drawLoop(pdc, name, thisLoop, id=thisId,
                        startX=thisInit, endX=thisTerm,
                        base=self.linePos[1], height=self.linePos[1] + (thisNest-LoopDepth-1)*self.loopHeight)
            self._drawLoopStart(pdc, pos=[thisInit,self.linePos[1]])
            self._drawLoopEnd(pdc, pos=[thisTerm,self.linePos[1]])

        # draw all possible locations for routines
        for n, xPos in enumerate(self.pointsToDraw):
            font.SetPointSize(600/self.dpi)
            self.SetFont(font);
            pdc.SetFont(font)
            w,h = self.GetFullTextExtent(str(n))[0:2]
            pdc.SetPen(wx.BLACK_PEN)
            pdc.SetBrush(wx.BLACK_BRUSH)
            pdc.DrawCircle(xPos, self.linePos[1], 8)
            pdc.SetTextForeground([255, 255, 255])
            pdc.DrawText(str(n), xPos-w/2, self.linePos[1]-h/2-1)

        self.SetVirtualSize((currX, self.linePos[1]+20))
        pdc.EndDrawing()
        self.Refresh() # refresh the visible window after drawing (using _onPaint)

    def _setDrawPoints(self, ptType, startPoint=None):
        """
        Set the points of 'routines', 'loops', or None
        """
        if ptType=='routines':
            self.pointsToDraw=self.gapMidPoints
        elif ptType=='loops':
            self.pointsToDraw=self.gapMidPoints
        else:
            self.pointsToDraw=[]
            
    def _drawLoopEnd(self, dc, pos):
        """
        Draws a spot that a loop end will later attach to
        """
        dc.SetBrush(wx.BLACK_BRUSH)
        dc.SetPen(wx.BLACK_PEN)
        dc.DrawPolygon([[5,5],[0,0],[-5,5]], pos[0],pos[1]-5) # points up

    def _drawLoopStart(self, dc, pos):
        """
        Draws a spot that a loop start will later attach to
        """
        dc.SetBrush(wx.BLACK_BRUSH)
        dc.SetPen(wx.BLACK_PEN)
        dc.DrawPolygon([[5,0],[0,5],[-5,0]], pos[0],pos[1]-5) # points down
        
    def _drawFlowRoutineOrIsi(self, dc, element, id, name, boldText=False, rgb=[200,50,50], pos=[0,0]):
        """
        Draw a box to show a routine or an ISI on the timeline
        """
        font = self.GetFont()
        if sys.platform == 'darwin':
            font.SetPointSize(1400/self.dpi)
        else:
            font.SetPointSize(1000/self.dpi)
        if boldText:
            font.SetWeight(wx.FONTWEIGHT_BOLD)
        r, g, b = rgb

        # get size based on text
        self.SetFont(font)
        dc.SetFont(font)
        w,h = self.GetFullTextExtent(name)[0:2]
        pad = 20
        # draw box
        rect = wx.Rect(pos[0], pos[1], w+pad,h+pad)
        endX = pos[0]+w+20
        # the edge should match the text
        dc.SetPen(wx.Pen(wx.Colour(r, g, b)))
        # for the fill, draw once in white near-opaque, then in transp colour
        dc.SetBrush(wx.Brush(wx.Colour(r,g*3,b*3)))
        dc.DrawRoundedRectangleRect(rect, 8)
        # draw text
        dc.SetTextForeground(rgb)
        dc.DrawText(name, pos[0]+pad/2, pos[1]+pad/2)

        self._objectFromID[id] = element
        dc.SetId(id)
        # set the area for this component
        dc.SetIdBounds(id,rect)
        
        # set font back to normal
        font.SetWeight(wx.FONTWEIGHT_NORMAL)
        self.SetFont(font)
        dc.SetFont(font)
        return endX
    
    def _drawLoop(self, dc, name, loop, id, startX, endX, base, height, rgb=[0,0,0]):
        xx = [endX,  endX,   endX,   endX-5, endX-10, startX+10,startX+5, startX, startX, startX]
        yy = [base,height+10,height+5,height, height, height,  height,  height+5, height+10, base]
        pts = []
        r,g,b = rgb
        pad = 8
        dc.SetPen(wx.Pen(wx.Colour(r, g, b)))
        for n in range(len(xx)):
            pts.append([xx[n], yy[n]])
        dc.DrawSpline(pts)

        # add a name label that can be clicked on
        font = self.GetFont()
        font.SetPointSize(800/self.dpi)
        self.SetFont(font);
        dc.SetFont(font)
        # get size based on text
        w,h = self.GetFullTextExtent(name)[0:2]
        x = startX+(endX-startX)/2-w/2
        y = height-h/2

        # draw box
        rect = wx.Rect(x, y, w+pad,h+pad)
        # the edge should match the text
        dc.SetPen(wx.Pen(wx.Colour(r, g, b)))
        # for the fill, draw once in white near-opaque, then in transp colour
        dc.SetBrush(wx.Brush(canvasColour))
        dc.DrawRoundedRectangleRect(rect, 8)
        # draw text
        dc.SetTextForeground([r,g,b])
        dc.DrawText(name, x+pad/2, y+pad/2)

        self._objectFromID[id] = loop
        dc.SetId(id)
        # set the area for this component
        dc.SetIdBounds(id,rect)



class ConditionCanvas(_ScrolledCanvas):
    """
    Represents a single condition (used as page in RoutineNotebook)
    """    
    def __init__(self, notebook, id=-1, condition=None):
        """
        This window is based heavily on the PseudoDC demo of wxPython
        """
        _ScrolledCanvas.__init__(self, notebook.frame, parent=notebook, style=wx.SUNKEN_BORDER, 
                                 contextMenuItems=['edit','remove','move to top','move up','move down','move to bottom'])
        self.notebook = notebook
        self.lines = []
        self.maxWidth  = 15 * self.dpi
        self.maxHeight = 15 * self.dpi
        self.groupingCheckboxes = []
        self.configDropdowns = []

        self.condition = condition        
        
        self.sizePix = self.GetClientSize()
        self.yPosTop = 50
        self.componentStep = 60 # the step in Y between each component
        self.iconXpos = 20 # the left hand edge of the icons
        self.timeXposStart = 230
        self.timeXposEnd = self.sizePix[0] - 70

        self.Bind(wx.EVT_SIZE, self._onResize)
        self.Bind(wx.EVT_SHOW, self._onShow)
        
    def _onResize(self, event):
        if self.sizePix != event.GetSize():
            # Calculate new end and redraw
            self.sizePix = event.GetSize()
            self.timeXposEnd = self.sizePix[0] - 70
            self.redrawCondition()
    
    def _onShow(self, event):
        if self.notebook.getCurrentPage() == self:
            # Redraw if the focus is on this canvas
            self.redrawCondition()

    def _onContextAction(self, action, object):
        """
        Perform a given action on the timeline chosen
        """
        cond = self.condition
        if action == 'edit':
            self._editComponentTimelineProperties(object)
        elif action == 'remove':
            cond.removeComponentTimeline(object)
            self.frame.addToUndoStack("removed" + object.component.getName())
        elif action.startswith('move'):
            lastLoc = cond._componentTimelines.index(object)
            cond._componentTimelines.remove(object)
            if action == 'move to top': 
                cond._componentTimelines.insert(0, object)
            elif action == 'move up': 
                cond._componentTimelines.insert(lastLoc-1, object)
            elif action == 'move down': 
                cond._componentTimelines.insert(lastLoc+1, object)
            elif action == 'move to bottom': 
                cond._componentTimelines.append(object)
            self.frame.addToUndoStack("moved" + object.component.getName())
        self.redrawCondition()

    def redrawCondition(self):
        self.pdc.Clear() # clear the screen
        self.pdc.RemoveAll() # clear all objects (icon buttons)
        
        # Delete all grouping checkboxes
        for checkbox in self.groupingCheckboxes:
            # TODO: do this more intelligently
            checkbox.Destroy()
        self.groupingCheckboxes = [] 
            
        # Delete all config dropdowns
        for dropdown in self.configDropdowns:
            # TODO: do this more intelligently
            dropdown.Destroy()
        self.configDropdowns = []

        self.pdc.BeginDrawing()
        # Draw timeline at bottom of page
        yPosBottom = self.yPosTop + len(self.condition._componentTimelines) * self.componentStep
        self._drawTimeGrid(self.pdc, self.yPosTop, yPosBottom)
        yPos = self.yPosTop + 10

        for yIndex, componentTimeline in enumerate(self.condition._componentTimelines):
            self._drawComponentTimeline(self.pdc, componentTimeline, yPos, yIndex)
            yPos += self.componentStep

        self.SetVirtualSize((self.sizePix[0] - 20, yPosBottom + 50)) # The 50 allows space for labels below the time axis
        self.pdc.EndDrawing()
        self.Refresh() # Refresh the visible window after drawing (using _onPaint)

    def _drawTimeGrid(self, dc, yPosTop, yPosBottom, labelAbove=True):
        """
        Draws the grid of lines and labels the time axes
        """
        tMax = self.condition.getMaxTime() * 1.1
        xScale = self._getSecsPerPixel()
        xSt = self.timeXposStart
        xEnd = self.timeXposEnd
        dc.SetPen(wx.BLACK_PEN)
        
        # Draw horizontal lines on top and bottom
        dc.DrawLine(x1=xSt, y1=yPosTop, x2=xEnd, y2=yPosTop)
        dc.DrawLine(x1=xSt, y1=yPosBottom, x2=xEnd, y2=yPosBottom)
        
        # Draw vertical time points
        rounded = 10 ** math.ceil(numpy.log10(tMax * 0.8))
        unitSize = rounded / 10.0     # Gives roughly 1/10 the width, but in rounded to base 10 of 0.1,1,10...
        if tMax / unitSize < 3: 
            unitSize = rounded / 50.0 # Gives units of 2 (0.2, 2, 20)
        elif tMax / unitSize < 6:
            unitSize = rounded / 20.0 # Gives units of 5 (0.5, 5, 50)
        
        font = self.GetFont()
        font.SetPointSize(600 / self.dpi)
        dc.SetFont(font)
        
        for lineN in range(int(math.ceil(tMax / unitSize))):
            # Vertical line
            xPos = xSt + lineN * unitSize / xScale
            if xPos > xEnd:
                break
            dc.DrawLine(xPos, yPosTop - 4, xPos, yPosBottom + 4)
            # Label above
            label = '%.2g' % (lineN * unitSize)
            dc.DrawText(label, xPos-2*len(label), yPosTop - 20)
            if yPosBottom > 300:
                # If bottom of grid is far away then draw labels below too
                dc.DrawText(label, xPos-2*len(label), yPosBottom + 10)
        
        # Add a label
        halfTextHeight = self.GetFullTextExtent('t')[1] / 2.0  # y is y-half height of text
        dc.DrawText('t (sec)', xEnd + 5, yPosTop - halfTextHeight)
        if yPosBottom > 300:
            # If bottom of grid is far away then draw labels here too
            dc.DrawText('t (sec)', xEnd + 5, yPosBottom - halfTextHeight)
            
    def _drawComponentTimeline(self, dc, componentTimeline, yPos, yIndex):
        """
        Draw the timing of one componentTimeline on the timeline
        """
        # Draw the icon
        thisIcon = components.getComponentIcon(componentTimeline.component.getType())
        dc.DrawBitmap(thisIcon, self.iconXpos, yPos, True)
        
        # Set font
        font = self.GetFont()
        font.SetPointSize(800/self.dpi)
        dc.SetFont(font)
        
        # Draw text
        x = self.iconXpos + 48 + 20 # 48 for the width of the icon, 20 for spacing
        name = componentTimeline.component.getName()
        dc.DrawText(name, x, yPos)
        
        # Insert the dropdowns for the config
        if len(self.configDropdowns) <= yIndex:
            configs = sorted(componentTimeline.component.configs.keys())
            dropdown = wx.Choice(self, pos=self.CalcScrolledPosition((x, yPos + 20)), size=(100, 25), choices=configs)
            dropdown.SetToolTipString("Config to use in this condition")
            dropdown.Bind(wx.EVT_CHOICE, self._onConfigChange)
            self.configDropdowns.append(dropdown)
            
        # Revert to standard config if the name of the config is invalid 
        if configs.count(self.condition.getConfig(componentTimeline)) == 0:
            self.condition.setConfig(componentTimeline, 'standard')
        
        self.configDropdowns[yIndex].SetStringSelection(self.condition.getConfig(componentTimeline))
            
        # Insert the checkbox for grouping
        if len(self.groupingCheckboxes) <= yIndex:
            checkbox = wx.CheckBox(self, pos=self.CalcScrolledPosition((x + dropdown.Size.x + 10, yPos + 15)))
            checkbox.SetToolTipString("Toggle whether this timeline is in the group. All timelines of a group are the same.")
            checkbox.Bind(wx.EVT_CHECKBOX, self._onGroupingChange)
            self.groupingCheckboxes.append(checkbox)
        self.groupingCheckboxes[yIndex].SetValue(componentTimeline.numConditionsInGroup > 0)
        self.groupingCheckboxes[yIndex].Show()

        # Draw entries on timeline
        xScale = self._getSecsPerPixel()
        h = self.componentStep/4
        yDisplay = yPos + 10
        yActivation = yDisplay + h
        
        if componentTimeline.isDrawable():
            for displayTime in componentTimeline._displayTimes:
                self._drawOccurence(dc, displayTime, xScale, yDisplay, h, componentDisplayTimeColour)
        
        for activation in componentTimeline._activations:
            self._drawOccurence(dc, activation, xScale, yActivation, h, componentActivationColour)

        # Set an id for the region where the component.icon falls (so it can act as a button)
        # See if we created this already
        id = None
        for key in self._objectFromID.keys():
            if self._objectFromID[key] == componentTimeline:
                id = key
                break
        if not id:
            # Create one and add to the dict
            id = wx.NewId()
            self._objectFromID[id] = componentTimeline
        dc.SetId(id)
        
        # Set the area for this component
        rect = wx.Rect(self.timeXposStart, yDisplay, self.timeXposEnd - self.timeXposStart, h*2)
        dc.SetIdBounds(id, rect)
        
    def _drawOccurence(self, dc, occurence, xScale, y, h, colour):
        """
        Draws an occurence (activation or display time)
        """
        dc.SetPen(wx.Pen(colour))
        dc.SetBrush(wx.Brush(colour))
        
        # Calculate x position
        try:
            start = occurence.params['startTime'].val
        except: 
            start = 0
        if start < 0:
            start = 0
        x = self.timeXposStart + start / xScale
        
        # Calculate width
        try:
            # Get end time
            duration = occurence.params['duration'].val
        except:
            # Set infinite (negative) if it can't be parsed
            duration = -1
        if duration < 0:
            # If duration is negative, it is actually infinite, make sure the
            # box is drawn to the end of the screen
            w = self.sizePix[0];
        else:
            w = duration / xScale
            if duration != 0 and w < 2:
                # Make sure at least one pixel shows if duration is not 0
                w = 2
        
        # Draw the line
        dc.DrawRectangle(x, y, w, h)

    def _editComponentTimelineProperties(self, componentTimeline):
        # Get the conditions that will be affected
        conditionsInGroup = self.condition.routine.getConditionsInGroup(componentTimeline)
        if len(conditionsInGroup) == 0:
            conditionsInGroup.append(self.condition.getName())
        
        # Create the dialog
        component = componentTimeline.component
        dlg = DlgComponentTimelineProperties(frame=self.frame,
            title=component.getName() + ' Timeline Properties',
            componentTimeline=componentTimeline, 
            affectedConditions=conditionsInGroup,
            routine=self.condition.routine)
        if dlg.OK:
            self.frame.addToUndoStack("edit %s" % component.getName())
            self.redrawCondition()
        return dlg.OK
                
    def _onGroupingChange(self, evt):
        """
        Handles the changes of the checkboxes that control the grouping
        of the componentTimelines
        """
        # Get the y index (position) of the checkbox that was pressed
        yIndex = self.groupingCheckboxes.index(evt.GetEventObject())
        
        # Add or remove the componentTimeline from the gruop
        if evt.Checked():
            self._onAddedToGroup(yIndex)
        else:
            self._onRemovedFromGroup(yIndex)
    
    def _onAddedToGroup(self, yIndex):
        # Add the componentTimeline to the group
        newComponentTimeline = self.condition.routine.addToGroup(self.condition._componentTimelines[yIndex])
        
        # Set the new componentTimeline
        self.condition._componentTimelines[yIndex] = newComponentTimeline
        
        # Redraw
        self.redrawCondition()
        
        # Show message of what was done
        componentName = newComponentTimeline.component.getName()
        conditionsInGroup = self.condition.routine.getConditionsInGroup(newComponentTimeline)
        message = 'Added the timeline of component "%s" to the group.\n\n' % componentName
        if len(conditionsInGroup) > 1:
            message += 'The timelines are now the same in conditions :\n- %s' % '\n- '.join(conditionsInGroup)
        else: 
            message += 'There are no other timelines in the group.'
        showInfo(message)
        
        self.frame.addToUndoStack("added component %s in condition %s of routine %s to group" % 
            (componentName, self.condition.getName(),
            self.condition.routine.getName()))
        
    def _onRemovedFromGroup(self, yIndex):
        # Remove the componentTimeline from the gruop
        newComponentTimeline = self.condition.routine.removeFromGroup(self.condition._componentTimelines[yIndex])
        
        # Set the returned componentTimeline
        self.condition._componentTimelines[yIndex] = newComponentTimeline
        
        # Show the timeline edit dialog
        if self._editComponentTimelineProperties(newComponentTimeline):
            self.frame.addToUndoStack("removed component %s in condition %s of routine %s from group" % 
                (newComponentTimeline.component.getName(), 
                self.condition.getName(), 
                self.condition.routine.getName()))
        else:
            # User cancelled, add it back to the group
            self.condition._componentTimelines[yIndex] = self.condition.routine.addToGroup(newComponentTimeline)
        
        # Redraw
        self.redrawCondition()
        
    def _onConfigChange(self, evt):
        """
        Handles changes of the config dropdowns, updates the configs in the condition
        """
        yIndex = self.configDropdowns.index(evt.GetEventObject())
        timeline = self.condition._componentTimelines[yIndex]
        newConfig = evt.GetString()
        # Only update if it has really changed
        if self.condition.getConfig(timeline) != newConfig:
            self.condition.setConfig(timeline, newConfig)
            self.frame.addToUndoStack("changed config of component %s" % timeline.getComponentName())

    def _getSecsPerPixel(self):
        return float(self.condition.getMaxTime()) / (self.timeXposEnd-self.timeXposStart)
    
    
    
class RoutineNotebook(wx.aui.AuiNotebook):
    """
    A notebook that displays a routine with its different condition timelines
    """
    def __init__(self, frame, id=-1):
        self.frame = frame
        self.app = frame.app
        self.dpi = self.app.dpi
        wx.aui.AuiNotebook.__init__(self, frame, id, style=wx.aui.AUI_NB_DEFAULT_STYLE & ~wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB)
        

        
    def getCurrentCondition(self):
        conditionPage = self.getCurrentPage()
        if conditionPage:
            return conditionPage.condition
        else: #no routine page
            return None
        
    def getCurrentPage(self):
        if self.GetSelection() >= 0:
            return self.GetPage(self.GetSelection())
        else: # there are no routine pages
            return None
        
    def _addConditionPage(self, condition):
        conditionPage = ConditionCanvas(notebook=self, condition=condition)
        self.AddPage(conditionPage, condition.routine.getName() + ": " + condition.getName())
        
    def removePages(self):
        """
        Removes all pages
        """
        # TODO: (minor) This operation is extremly slow, should somehow speed that up
        for ii in range(self.GetPageCount()):
            self.DeletePage(0)
        
    def redrawConditions(self, redrawAllConditions):
        """
        Removes all the conditions, adds them back and sets current back to orig
        """
        if self.frame.exp.activeRoutine:
            # There is an active routine,
            currPage = self.GetSelection()
            if redrawAllConditions:
                # Get the current selection and re-insert all pages
                self.removePages()
                for condition in self.frame.exp.activeRoutine._conditions:
                    self._addConditionPage(condition)
                if currPage >- 1:
                    self.SetSelection(currPage)
            elif currPage >- 1:
                self.GetPage(currPage).redrawCondition()
        else:
            # No active routine, remove all pages
            self.removePages()


class ComponentsPanel(scrolled.ScrolledPanel):
    def __init__(self, frame, id=-1):
        """
        A panel that shows all the components available
        """
        self.frame = frame
        self.app = frame.app
        self.dpi = self.app.dpi
        scrolled.ScrolledPanel.__init__(self,frame,id,size=(1.5*frame.app.dpi, frame.app.dpi))
        sizer = wx.BoxSizer(wx.VERTICAL)

        # add a button for each type of event that can be added
        self._objectFromID = {}
        
        compTypes = components.getAllComponentTypes()
        for compType in compTypes:
            compIcon = components.getComponentIcon(compType, 1)
            btn = wx.BitmapButton(self, -1, compIcon, (20, 20),
                           (compIcon.GetWidth() + 10, compIcon.GetHeight() + 10),
                           name=compType)
            btn.SetToolTipString(compType)
            self._objectFromID[btn.GetId()] = compType
            self.Bind(wx.EVT_BUTTON, self._onComponentAdd, btn)
            sizer.Add(btn, 0, wx.EXPAND|wx.ALIGN_CENTER)

        self.SetSizer(sizer)
        self.SetAutoLayout(1)
        self.SetupScrolling()

    def _onComponentAdd(self, evt):
        exp = self.frame.exp   
        # get component
        newComp = components.getNewComponent(self.frame.exp, self._objectFromID[evt.GetId()])
        
        # does this component have a help page?
        if hasattr(newComp, 'url'):
            helpUrl = newComp.url
        else:
            helpUrl = None
        
        # create component template
        dlg = DlgComponentProperties(frame=self.frame, title=newComp.getType() + ' Properties',
            component=newComp, helpUrl=helpUrl)
        if dlg.OK:
            exp.components.append(newComp) # add to the experiment
            self.frame.addToUndoStack("added %s" % newComp.getName())
            self.frame.experimentComponentsPanel.redrawComponents()



class ExperimentComponentsPanel(_ScrolledCanvas):
    def __init__(self, frame):
        """
        A panel that shows all the component instances that have 
        been created for this experiment
        """
        _ScrolledCanvas.__init__(self, frame, parent=frame, size=(1.5*frame.app.dpi, frame.app.dpi), 
                                 contextMenuItems=['edit', 'add to condition', 'add to all conditions', 'remove', 'duplicate', 'enable/disable', 'move to top','move up','move down','move to bottom'])
        self.maxWidth = self.dpi
        self.maxHeight = 15 * self.dpi

        self.SetVirtualSize((self.maxWidth, self.maxHeight))
        
        self.yPosTop = 20
        self.componentStep = 80 # the step in Y between each component
        self.iconXpos = 20 # the left hand edge of the icons

        self.redrawComponents()

    def _onContextAction(self, action, object):
        """
        Perform a given action on the component chosen
        """
        if action == 'edit':
            self._editComponentProperties(object)
        elif action == 'duplicate':
            newComp = deepcopy(object)
            newComp.params['name'].val += '_bis'
            self.frame.exp.components.insert(self.frame.exp.components.index(object), newComp) # add to the experiment
            self.frame.addToUndoStack("added %s" % newComp.getName())
            self.frame.experimentComponentsPanel.redrawComponents()
            pass
        elif action == 'remove':
            self.frame.exp.removeComponent(object)
            self.frame.addToUndoStack("removed" + object.getName())
            self.redrawComponents()
            self.frame.routinePanel.redrawConditions(False)
        elif action == 'add to condition':
            # get name of current condition
            currCondition = self.frame.routinePanel.getCurrentCondition()
            if currCondition:
                if currCondition.containsComponent(object):
                    showError("The current condition already contains this component")
                else:
                    self._addComponentToCondition(object, currCondition)
            else:
                showError("Create and select a routine before adding components to conditions")
        elif action == 'add to all conditions':
            currRoutine = self.frame.exp.activeRoutine
            if not currRoutine:
                showError("Create and select a routine before adding components to conditions")
            else:
                self._addComponentToAllConditions(object, currRoutine)
        elif action == 'enable/disable':
            object.toggleEnabled()
            self.redrawComponents()
            self.frame.addToUndoStack("Enabled" if object.enabled() else "Disabled" + object.getName())
        elif action.startswith('move'): 
            lastLoc = self.frame.exp.components.index(object)
            self.frame.exp.components.remove(object)
            if action == 'move to top': 
                self.frame.exp.components.insert(0, object)
            elif action == 'move up': 
                self.frame.exp.components.insert(lastLoc-1, object)
            elif action == 'move down': 
                self.frame.exp.components.insert(lastLoc+1, object)
            elif action == 'move to bottom': 
                self.frame.exp.components.append(object)
            self.frame.addToUndoStack("Moved" + object.getName())
            self.redrawComponents()

    def redrawComponents(self):
        if not hasattr(self.frame, 'exp'):
            return # we haven't yet added an exp
        self.pdc.Clear() # clear the screen
        self.pdc.RemoveAll() # clear all objects (icon buttons)
        self.pdc.BeginDrawing()
        
        # Draw the components
        yPos = self.yPosTop
        for component in self.frame.exp.components:
            self._drawComponent(self.pdc, component, yPos)
            yPos += self.componentStep

        self.SetVirtualSize((self.maxWidth, yPos))
        self.pdc.EndDrawing()
        self.Refresh() # Refresh the visible window after drawing (using _onPaint)
            
    def _drawComponent(self, dc, component, yPos):
        """
        Draw the icon of one component
        """
        thisIcon = components.getComponentIcon(component.getType(), 0 if component.enabled() else 2)
        dc.DrawBitmap(thisIcon, self.iconXpos, yPos, True)
        
        # Draw the text
        font = self.GetFont()
        font.SetPointSize(800/self.dpi)
        dc.SetFont(font)
        name = component.getName()
        dc.DrawText(name, self.iconXpos, yPos + thisIcon.GetHeight())

        # Set an id for the region where the component.icon falls (so it can act as a button)
        # See if we created this already
        id = None
        for key in self._objectFromID.keys():
            if self._objectFromID[key] == component:
                id = key
        if not id: # Then create one and add to the dict
            id = wx.NewId()
            self._objectFromID[id] = component
        dc.SetId(id)
        # Set the area for this component
        r = wx.Rect(self.iconXpos, yPos, thisIcon.GetWidth(), thisIcon.GetHeight())
        dc.SetIdBounds(id, r)

    def _editComponentProperties(self, component):
        # does this component have a help page?
        if hasattr(component, 'url'):
            helpUrl=component.url
        else:
            helpUrl=None
        # create the dialog
        dlg = DlgComponentProperties(frame=self.frame,
            title = component.getName() + ' Properties',
            component = component,
            helpUrl = helpUrl)
        if dlg.OK:
            self.frame.routinePanel.redrawConditions(False)
            self.frame.addToUndoStack("edit %s" % component.getName())
            
        self.redrawComponents()
            
    def _addComponentToCondition(self, component, condition):
        """
        Shows the dialog to add a component to a condition
        """
        groupedTimeline = condition.routine.getGroupedTimeline(component)
        if groupedTimeline:
            condition.addComponentTimeline(groupedTimeline, addToGroup=True)
            self.frame.addToUndoStack("added grouped comp %s to condition %s" % (component.getName(), condition.getName()))
            self.frame.routinePanel.redrawConditions(False)
            return
            
        componentTimeline = component.getNewComponentTimeline()
        # create the dialog
        dlg = DlgComponentTimelineProperties(frame=self.frame,
            title='Add ' + component.getName() + ' to condition ' + condition.getName(), 
            componentTimeline=componentTimeline,
            affectedConditions=[condition.getName()],
            routine=condition.routine)
        if dlg.OK:
            condition.addComponentTimeline(componentTimeline) # add to the actual condition
            self.frame.addToUndoStack("added comp %s to condition %s" % (component.getName(), condition.getName()))
            self.frame.routinePanel.redrawConditions(False)
        
    def _addComponentToAllConditions(self, component, routine):
        """
        Adds the given component to all conditions in the routine that do not
        already have it. If there is already a group for that component, is is 
        used for all the conditions. If there is no group, a dialogue is shown
        to configure the occurences.
        """
        # Go throug all the conditions and check whether they already have that component
        conditionsWithoutThisComp = []
        groupedTimeline = None
        affectedConditions = []
        for condition in routine._conditions:
            timeline = condition.containsComponent(component) 
            if not timeline:
                conditionsWithoutThisComp.append(condition)
                affectedConditions.append(condition.getName())
            elif timeline.isInGroup():
                groupedTimeline = timeline
        
        # If all conditions already have it, show an error
        if len(conditionsWithoutThisComp) == 0:
            showError("All conditions already contains this component")
            return
        
        # If we found that there is already a group for this component, add it to all the other components
        if groupedTimeline:
            for condition in conditionsWithoutThisComp:
                condition.addComponentTimeline(groupedTimeline, addToGroup=True)
            self.frame.addToUndoStack("added grouped comp %s to all conditions" % component.getName())
            self.frame.routinePanel.redrawConditions(False)
            return
        
        # Need to show a dialogue and then add that to all the conditions
        timeline = component.getNewComponentTimeline()
        # create the dialog
        dlg = DlgComponentTimelineProperties(frame=self.frame,
            title='Add ' + component.getName() + ' to all conditions', 
            componentTimeline=timeline, affectedConditions=affectedConditions,
            routine=routine)
        if dlg.OK:
            # Add to all the conditions and make sure it's a group
            for condition in conditionsWithoutThisComp:
                condition.addComponentTimeline(timeline, addToGroup=True)
            self.frame.addToUndoStack("added comp %s to all conditions" % component.getName())
            self.frame.routinePanel.redrawConditions(False)



class BuilderFrame(wx.Frame):
    def __init__(self, parent, id=-1, title='ExpyVR Experiment Designer',
                 pos=wx.DefaultPosition, files=None,
                 style=wx.DEFAULT_FRAME_STYLE, app=None):
        self.app = app
        self.dpi = self.app.dpi
        self.appData = self.app.prefs.appData['general'] # things the user doesn't set like winsize etc
        self.prefs = self.app.prefs.builder # things about the builder that get set
        self.paths = self.app.prefs.paths
        self.IDs = self.app.IDs
        self.instanceFileName = '' 
        
        if self.appData['winH'] == 0 or self.appData['winW'] == 0:
            # we didn't have the key or the win was minimized/invalid
            self.appData['winH'], self.appData['winW'] =wx.DefaultSize
            self.appData['winX'],self.appData['winY'] =wx.DefaultPosition
        
        wx.Frame.__init__(self, parent, id, title, (self.appData['winX'], self.appData['winY']),
                         size=(self.appData['winW'],self.appData['winH']), style=style)

        # create icon
        if sys.platform == 'darwin':
            pass # doesn't work and not necessary - handled by application bundle
        else:
            iconFile = os.path.join(self.paths['resources'], 'expyvr.png')
            if os.path.isfile(iconFile):
                self.SetIcon(wx.Icon(iconFile, wx.BITMAP_TYPE_PNG))
                
        if self.appData.has_key('state') and self.appData['state'] == 'maxim':
            self.Maximize()

        # create our panels
        self.flowPanel = FlowPanel(frame=self)
        self.routinePanel = RoutineNotebook(self)
        self.componentsPanel = ComponentsPanel(self)
        self.experimentComponentsPanel = ExperimentComponentsPanel(self)
        
        # menus and toolbars
        self._makeToolbar()
        self._makeMenus()

        self.stdoutOrig = sys.stdout
        self.stderrOrig = sys.stderr
        
        # setup a default exp
        if files != None and len(files) and os.path.isfile(files[0]):
            self._fileOpen(filename=files[0], closeCurrent=False)
        elif self.prefs['reloadPrevExp'] and os.path.isfile(self.appData['prevFile']):
            self._fileOpen(filename=self.appData['prevFile'], closeCurrent=False)
        else:
            self.lastSavedCopy = None
            self._fileNew(closeCurrent=False) # don't try to close before opening

        # control the panes using aui manager
        self._mgr = wx.aui.AuiManager(self)
        self._mgr.AddPane(self.flowPanel, wx.aui.AuiPaneInfo().
                          Name("Flow").Caption("Flow").BestSize((8*self.dpi,2*self.dpi)).
                          RightDockable(True).LeftDockable(True).CloseButton(False).Top())
        self._mgr.AddPane(self.routinePanel, wx.aui.AuiPaneInfo().
                          Name("Routines").Caption("Routines").
                          CenterPane().CloseButton(False).MaximizeButton(True)) #'center panes' expand to fill space
        self._mgr.AddPane(self.componentsPanel, wx.aui.AuiPaneInfo().
                          Name("Components").Caption("Components").
                          RightDockable(True).LeftDockable(True).CloseButton(False).Left().Row(0))
        self._mgr.AddPane(self.experimentComponentsPanel, wx.aui.AuiPaneInfo().
                          Name("Experiment Components").Caption("Experiment Components").
                          RightDockable(True).LeftDockable(True).CloseButton(False).Left().Row(1))
        # tell the manager to 'commit' all the changes just made
        self._mgr.Update()

        if self.appData['auiPerspective'] and self.appData['expyvrVersion'] == self.app.version:
            # load the perspective saved if its not from an old version
            self._mgr.LoadPerspective(self.appData['auiPerspective'])
        self.SetMinSize(wx.Size(800, 600)) # min size for the whole window
        self.Fit()
        self.SendSizeEvent()
        self._mgr.Update()
        self.Bind(wx.EVT_CLOSE, self.closeFrame)
        
    def _makeToolbar(self):
        #---toolbar---#000000#FFFFFF----------------------------------------------
        self.toolbar = self.CreateToolBar( (wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT))

        if sys.platform=='win32' or sys.platform.startswith('linux') or float(wx.version()[:3]) >= 2.8:
            if self.prefs['largeIcons']:
                toolbarSize = 32
            else:
                toolbarSize = 16
        else:
            toolbarSize = 32 #size 16 doesn't work on mac wx; does work with wx.version() == '2.8.7.1 (mac-unicode)'
            
        self.toolbar.SetToolBitmapSize((toolbarSize,toolbarSize))
        self.toolbar.SetToolBitmapSize((toolbarSize,toolbarSize))
        new_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'filenew%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)
        open_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'fileopen%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)
        save_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'filesave%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)
        saveAs_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'filesaveas%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)
        undo_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'undo%i.png' %toolbarSize),wx.BITMAP_TYPE_PNG)
        redo_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'redo%i.png' %toolbarSize),wx.BITMAP_TYPE_PNG)
        logger_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'settingsExp%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)
        display_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'monitors%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)
        testroutine_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'testroutine%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)
        test_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'test%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)
        run_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'run%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)
        gen_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'gen%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)

        ctrlKey = 'Ctrl+'  # show key-bindings in tool-tips in an OS-dependent way
        if sys.platform == 'darwin': ctrlKey = 'Cmd+'  
        self.toolbar.AddSimpleTool(self.IDs.tbFileNew, new_bmp, ("New [%s]" %self.app.keys['new']).replace('Ctrl+', ctrlKey), "Create new python file")
        self.toolbar.Bind(wx.EVT_TOOL, self._fileNew, id=self.IDs.tbFileNew)
        
        self.toolbar.AddSimpleTool(self.IDs.tbFileOpen, open_bmp, ("Open [%s]" %self.app.keys['open']).replace('Ctrl+', ctrlKey), "Open an existing file")
        self.toolbar.Bind(wx.EVT_TOOL, self._fileOpen, id=self.IDs.tbFileOpen)
        
#        self.toolbar.AddSimpleTool(self.IDs.tbFileImport, open_bmp, "Import components... " , "Import the components from another experiment file...")
#        self.toolbar.Bind(wx.EVT_TOOL, self._fileImport, id=self.IDs.tbFileImport)
        
        self.toolbar.AddSimpleTool(self.IDs.tbFileSave, save_bmp, ("Save [%s]" %self.app.keys['save']).replace('Ctrl+', ctrlKey),  "Save current file")
        self.toolbar.EnableTool(self.IDs.tbFileSave, False)
        self.toolbar.Bind(wx.EVT_TOOL, self._fileSave, id=self.IDs.tbFileSave)
        
        self.toolbar.AddSimpleTool(self.IDs.tbFileSaveAs, saveAs_bmp, ("Save As... [%s]" %self.app.keys['saveAs']).replace('Ctrl+', ctrlKey), "Save current python file as...")
        self.toolbar.Bind(wx.EVT_TOOL, self._fileSaveAs, id=self.IDs.tbFileSaveAs)
        
        self.toolbar.AddSimpleTool(self.IDs.tbUndo, undo_bmp, ("Undo [%s]" %self.app.keys['undo']).replace('Ctrl+', ctrlKey), "Undo last action")
        self.toolbar.Bind(wx.EVT_TOOL, self._undo, id=self.IDs.tbUndo)
        
        self.toolbar.AddSimpleTool(self.IDs.tbRedo, redo_bmp, ("Redo [%s]" %self.app.keys['redo']).replace('Ctrl+', ctrlKey),  "Redo last action")
        self.toolbar.Bind(wx.EVT_TOOL, self._redo, id=self.IDs.tbRedo)
        
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool(self.IDs.tbLogSettings, logger_bmp, "Logger Settings",  "Logger settings for this exp")
        self.toolbar.Bind(wx.EVT_TOOL, self._setLoggerSettings, id=self.IDs.tbLogSettings)
        
        self.toolbar.AddSimpleTool(self.IDs.tbDispSettings, display_bmp, "Display Settings",  "Display settings for this exp")
        self.toolbar.Bind(wx.EVT_TOOL, self._setDisplaySettings, id=self.IDs.tbDispSettings)
        
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool(self.IDs.tbTestroutine, testroutine_bmp, "Test current routine and condition",  "Generates a test instance for the current routine and runs it")
        self.toolbar.Bind(wx.EVT_TOOL, self._testRoutineCondition, id=self.IDs.tbTestroutine)
        self.toolbar.AddSimpleTool(self.IDs.tbTest, test_bmp, "Test experiment",  "Generates a test instance and runs it")
        self.toolbar.Bind(wx.EVT_TOOL, self._testExperiment, id=self.IDs.tbTest)
        self.toolbar.AddSimpleTool(self.IDs.tbGen, gen_bmp, "Generate instance",  "Generate an instance of this experiment")
        self.toolbar.Bind(wx.EVT_TOOL, self._genInstance, id=self.IDs.tbGen)
        self.toolbar.AddSimpleTool(self.IDs.tbRun, run_bmp, "Run instance",  "Run an instance of this experiment")
        self.toolbar.Bind(wx.EVT_TOOL, self._runInstance, id=self.IDs.tbRun)
        
        self.toolbar.Realize()

    def _makeMenus(self):
        #---Menus---#000000#FFFFFF--------------------------------------------------
        menuBar = wx.MenuBar()
        #---_file---#000000#FFFFFF--------------------------------------------------
        self.fileMenu = wx.Menu()
        menuBar.Append(self.fileMenu, '&File')
        self.fileMenu.Append(wx.ID_NEW,     "&New\t%s" %self.app.keys['new'])
        self.fileMenu.Append(wx.ID_OPEN,    "&Open...\t%s" %self.app.keys['open'])
        self.fileMenu.Append(self.IDs.componentFileImport, "Import components", "Open experiment and import its modules")
        self.fileMenu.Append(wx.ID_SAVE,    "&Save\t%s" %self.app.keys['save'])
        self.fileMenu.Append(wx.ID_SAVEAS,  "Save &as...\t%s" %self.app.keys['saveAs'])
        self.fileMenu.Append(wx.ID_CLOSE,   "&Close file\t%s" %self.app.keys['close'])
        wx.EVT_MENU(self, wx.ID_NEW,  self._fileNew)
        wx.EVT_MENU(self, wx.ID_OPEN,  self._fileOpen)
        wx.EVT_MENU(self, self.IDs.componentFileImport,  self._fileImport)
        wx.EVT_MENU(self, wx.ID_SAVE,  self._fileSave)
        self.fileMenu.Enable(wx.ID_SAVE, False)
        wx.EVT_MENU(self, wx.ID_SAVEAS,  self._fileSaveAs)
        wx.EVT_MENU(self, wx.ID_CLOSE,  self.closeFrame)
        item = self.fileMenu.Append(wx.ID_PREFERENCES, text = "&Preferences")
        self.Bind(wx.EVT_MENU, self.app.showPrefs, item)
        #-------------quit
        self.fileMenu.AppendSeparator()
        self.fileMenu.Append(wx.ID_EXIT, "&Quit\t%s" %self.app.keys['quit'], "Terminate the program")
        wx.EVT_MENU(self, wx.ID_EXIT, self.quit)

        self.editMenu = wx.Menu()
        menuBar.Append(self.editMenu, '&Edit')
        self.editMenu.Append(wx.ID_UNDO, "Undo\t%s" %self.app.keys['undo'], "Undo last action", wx.ITEM_NORMAL)
        wx.EVT_MENU(self, wx.ID_UNDO,  self._undo)
        self.editMenu.Append(wx.ID_REDO, "Redo\t%s" %self.app.keys['redo'], "Redo last action", wx.ITEM_NORMAL)
        wx.EVT_MENU(self, wx.ID_REDO,  self._redo)

        #---_experiment---#000000#FFFFFF--------------------------------------------------
        self.expMenu = wx.Menu()
        menuBar.Append(self.expMenu, 'E&xperiment')
        self.expMenu.Append(self.IDs.logSettings, "Logger Settings", "Edit the logger settings")
        wx.EVT_MENU(self, self.IDs.logSettings,  self._setLoggerSettings)
        self.expMenu.Append(self.IDs.dispSettings, "Display Settings", "Edit the display settings")
        wx.EVT_MENU(self, self.IDs.dispSettings,  self._setDisplaySettings)
        
        self.expMenu.AppendSeparator()
        self.expMenu.Append(self.IDs.addRoutineToFlow, "Add Routine", "Add a new routine to the flow")
        wx.EVT_MENU(self, self.IDs.addRoutineToFlow,  self.flowPanel._onInsertRoutine)
        self.expMenu.Append(self.IDs.addLoopToFlow, "Add Loop", "Add a new loop to the flow")
        wx.EVT_MENU(self, self.IDs.addLoopToFlow,  self.flowPanel._onInsertLoop)
        self.expMenu.Append(self.IDs.addIsiToFLow, "Add ISI", "Add a new ISI to the flow")
        wx.EVT_MENU(self, self.IDs.addIsiToFLow,  self.flowPanel._onInsertIsi)
        self.expMenu.AppendSeparator()
        
        self.expMenu.Append(self.IDs.testExperiment,
            "Test experiment\t%s" %self.app.keys['testExperiment'], 
            "Generates a test instance and runs it (freezes expyvr during test)")
        wx.EVT_MENU(self, self.IDs.testExperiment, self._testExperiment)
        self.expMenu.Append(self.IDs.testRoutine,
            "Test current routine && condition\t%s" %self.app.keys['testRoutine'], 
            "Generates a test instance for the current routine-condition and runs it (freezes expyvr during test)")
        wx.EVT_MENU(self, self.IDs.testRoutine, self._testRoutineCondition)
        self.expMenu.Append(self.IDs.genInstance,
            "Generate instance",
            "Generate an instance of this experiment")
        wx.EVT_MENU(self, self.IDs.genInstance, self._genInstance)
        self.expMenu.Append(self.IDs.genAllInstances,
            "Generate many instances",
            "Generate many randomisations of this experiment")
        wx.EVT_MENU(self, self.IDs.genAllInstances, self._genAllInstances)
        self.expMenu.Append(self.IDs.runInstance,
            "Execute instance",
            "Execute an instance of experiment")
        wx.EVT_MENU(self, self.IDs.runInstance, self._runInstance)
        self.expMenu.Append(self.IDs.rerunInstance,
            "Re-execute previous instance\t%s" %self.app.keys['rerunInstance'], 
            "Re-execute the last instance executed")
        wx.EVT_MENU(self, self.IDs.rerunInstance, self._rerunInstance)

        #---_help---#000000#FFFFFF--------------------------------------------------
        self.helpMenu = wx.Menu()
        menuBar.Append(self.helpMenu, '&Help')
        self.helpMenu.Append(self.IDs.builderHelp, "&Documentation", "Open documentation")
        wx.EVT_MENU(self, self.IDs.builderHelp, self.app.followLink)
        self.helpMenu.Append(self.IDs.expyvrHome, "Explore SVN &Repository", "Go to the project SVN homepage")
        wx.EVT_MENU(self, self.IDs.expyvrHome, self.app.followLink)
        self.helpMenu.Append(self.IDs.expyvrTrac, "Submit new &Ticket (bug report)", "Submit a bug report or a feature request")
        wx.EVT_MENU(self, self.IDs.expyvrTrac, self.app.followLink)

        self.helpMenu.AppendSeparator()
        self.helpMenu.Append(self.IDs.about, "&About...", "About ExpyVR")
        wx.EVT_MENU(self, self.IDs.about, self.app.showAbout)

        self.SetMenuBar(menuBar)
        
    def closeFrame(self, event=None, checkSave=True):
        if sys.platform != 'darwin':
            if not self.app.quitting:
                self.app.quit()
                return # app.quit() will have closed the frame already

        if checkSave:
            ok = self.checkSave()
            if not ok: 
                return False
        self.appData['prevFile'] = self.filename

        # Get size and window layout info
        if self.IsIconized():
            self.Iconize(False) # Will return to normal mode to get size info
            self.appData['state'] = 'normal'
        elif self.IsMaximized():
            self.Maximize(False) # Will briefly return to normal mode to get size info
            self.appData['state'] = 'maxim'
        else:
            self.appData['state'] = 'normal'
        self.appData['auiPerspective'] = self._mgr.SavePerspective()
        self.appData['winW'], self.appData['winH'] = self.GetSize()
        self.appData['winX'], self.appData['winY'] = self.GetPosition()
        if sys.platform=='darwin':
            self.appData['winH'] -= 39 # For some reason mac wxpython <=2.8 gets this wrong (toolbar?)
        self.appData['expyvrVersion'] = self.app.version

        self.Destroy()
        self.app.builder = None
        return True # Indicates that check was successful
    
    def quit(self, event=None):
        """
        Quit the app
        """
        self.app.quit()
        
    def _fileNew(self, event=None, closeCurrent=True):
        """
        Create a default experiment (maybe an empty one instead)
        """
        # Close the existing file
        if closeCurrent and not self._fileClose():
            # User cancelled the file closing somehow
            return False
        
        self.filename = 'untitled.exp.xml'
        self.exp = experiment.Experiment()
        self._resetUndoStack()
        self._setIsModified(False)
        self.updateAllViews()
        
    def _fileOpen(self, event=None, filename=None, closeCurrent=True):
        """
        Open a FileDialog, then load the file if possible.
        """
        if filename == None:
            dlg = wx.FileDialog(self, message="Open file ...", 
                defaultDir=os.path.dirname(self.filename),
                style=wx.FD_OPEN|wx.FD_CHANGE_DIR,
                wildcard=helpers.getExpFileWildcard())

            if dlg.ShowModal() != wx.ID_OK:
                return False
                
            filename = dlg.GetPath()
        
        if closeCurrent and not self._fileClose(): 
            # User cancelled the file closing somehow, can't open other file
            return False
        
        # where the file is is where the experiment is
        os.environ['EXPDIR'] = os.path.realpath(os.path.dirname(filename))
        
        self.exp = experiment.Experiment()
        try:
            self.exp.loadFromXML(filename)
        except:
            storeTracebackAndShowError('Could not load experiment.')
            # Open a new empty project instead
            self._fileNew(closeCurrent=False)
            return
        
        self._resetUndoStack()
        self._setIsModified(False)
        self.filename = filename
        
        # update the views
        self.updateAllViews()
        
    def _fileImport(self, event=None, filename=None):
        """
        Open a FileDialog, then load the file if possible.
        """
        if filename == None:
            dlg = wx.FileDialog(self, message="Import file ...", 
                defaultDir=os.path.dirname(self.filename),
                style=wx.FD_OPEN|wx.FD_CHANGE_DIR,
                wildcard=helpers.getExpFileWildcard())

            if dlg.ShowModal() != wx.ID_OK:
                return False
                
            filename = dlg.GetPath()
        
        # open the file using a parser that ignores prettyprint blank text
        parser = etree.XMLParser(remove_blank_text=True)
        f = open(filename)
        root = etree.XML(f.read(), parser)
        f.close()
        
        # Fetch the list of experiment components
        componentslist = []
        componentsNode = root.find('Components')
        for cp in componentsNode:   
            componentslist.append(cp.get('name'))
        
        # show a dialog asking for which components to keep/exclude
        dlg = DlgSelectComponentsImport(self, componentslist)
        if dlg.OK:
            excludelist = []
            for componentName in dlg.params.keys():
                if dlg.params[componentName].val is False:
                    excludelist.append(componentName)
            
            # import the components (minus the list of excluded)
            try:
                self.exp.importComponentsFromXML(filename, excludelist)
            except:
                storeTracebackAndShowError('Could not import components from experiment.')
                return
            
            self._setIsModified(True)
    
            # update the views
            self.updateAllViews()
        
    def _fileSave(self, event=None, filename=None):
        """
        Save file, revert to SaveAs if the file hasn't yet been saved
        """
        if filename == None:
            filename = self.filename
        if filename.startswith('untitled'):
            if not self._fileSaveAs(filename):
                # User cancelled during save as
                return False
        else:
            self.exp.saveToXML(filename)   
            
        self._setIsModified(False)
        return True
    
    def _fileSaveAs(self, event=None, filename=None):
        if filename == None:
            filename = self.filename
        initPath, filename = os.path.split(filename)

        os.getcwd()
        returnVal = False
        dlg = wx.FileDialog(self, message="Save file as ...", defaultDir=initPath,
            defaultFile=filename, style=wx.FD_SAVE|wx.FD_CHANGE_DIR,
            wildcard=helpers.getExpFileWildcard())
        
        if dlg.ShowModal() == wx.ID_OK:
            newPath = dlg.GetPath()
            # actually save
            self._fileSave(event=None, filename=newPath)
            self.filename = newPath
            
            # where the file is is where the experiment is
            os.environ['EXPDIR'] = os.path.realpath(os.path.dirname(self.filename))   
            
            returnVal = True
        try: # this seems correct on PC, but not on mac
            dlg.destroy()
        except:
            pass
        return returnVal
    
    def checkSave(self):
        """
        Check whether we need to save before quitting
        """
        if hasattr(self, 'isModified') and self.isModified:
            dlg = MessageDialog(self, 'Experiment has changed. Save before quitting?', type='Warning')
            resp = dlg.ShowModal()
            dlg.Destroy()
            if resp  == wx.ID_CANCEL: 
                return False # Return, don't quit
            elif resp == wx.ID_YES:
                if not self._fileSave():
                    return False # User might cancel during save
            elif resp == wx.ID_NO: 
                pass # Don't save just quit
        return True
    
    def _fileClose(self, event=None, checkSave=True):
        """
        Close the current file and ask check whether we need to save before if
        checkSave is True
        """
        if checkSave and not self.checkSave():
            # User cancelled 
            return False
        
        # Close self
        self.filename = 'untitled.exp.xml'
        self._resetUndoStack() # Will add the current exp as the start point for undo
        self.updateAllViews()
        return True
    
    def updateAllViews(self, redrawAllConditions=True):
        self.flowPanel.redrawFlow()
        self.routinePanel.redrawConditions(redrawAllConditions)
        self.experimentComponentsPanel.redrawComponents()
        self._updateWindowTitle()
        
    def _updateWindowTitle(self, newTitle=None):
        if newTitle == None:
            shortName = os.path.split(self.filename)[-1]
            newTitle='ExpyVR Experiment Designer - %s (%s)' %(shortName, self.filename)
        self.SetTitle(newTitle)
        
    def _setIsModified(self, newVal=None):
        """
        Sets current modified status and updates save icon accordingly.

        This method is called by the methods fileSave, undo, redo, addToUndoStack
        and it is usually preferably to call those than to call this directly.

        Call with ``newVal=None``, to only update the save icon(s)
        """
        if newVal == None:
            newVal = self.isModified
        else:
            self.isModified = newVal
        # update buttons/menus
        self.toolbar.EnableTool(self.IDs.tbFileSave, newVal)
        self.fileMenu.Enable(wx.ID_SAVE, newVal)
    
    def _resetUndoStack(self):
        """
        Reset the undo stack. e.g. do this *immediately after* creating a new exp.

        Will implicitly call addToUndoStack() using the current exp as the state
        """
        self.currentUndoLevel = 1 # 1 is current, 2 is back one setp...
        self.currentUndoStack = []
        self.addToUndoStack()
        self._enableUndo(False)
        self._enableRedo(False)
        self._setIsModified(newVal=False) # update save icon if needed
        
    def addToUndoStack(self, action="", state=None):
        """
        Add the given ``action`` to the currentUndoStack, associated with the @state@.
        ``state`` should be a copy of the exp from *immediately after* the action was taken.
        If no ``state`` is given the current state of the experiment is used.

        If we are at end of stack already then simply append the action.
        If not (user has done an undo) then remove orphan actions and then append.
        """
        if state == None:
            state = deepcopy(self.exp)
        # Remove actions from after the current level
        if self.currentUndoLevel > 1:
            self.currentUndoStack = self.currentUndoStack[:-(self.currentUndoLevel-1)]
            self.currentUndoLevel = 1
        # Append this action
        self.currentUndoStack.append({'action':action, 'state':state})
        self._enableUndo(True)
        self._setIsModified(True) # Update save icon if needed
        
    def _undo(self, event=None):
        """
        Step the exp back one level in the @currentUndoStack@ if possible,
        and update the windows

        Returns the final undo level (1=current, >1 for further in past)
        or -1 if redo failed (probably can't undo)
        """
        if (self.currentUndoLevel) >= len(self.currentUndoStack):
            return -1 # can't undo
        self.currentUndoLevel += 1
        self.exp = deepcopy(self.currentUndoStack[-self.currentUndoLevel]['state'])
        # set undo redo buttons
        self._enableRedo(True) # if we've undone, then redo must be possible
        if self.currentUndoLevel == len(self.currentUndoStack):
            self._enableUndo(False)
        self.updateAllViews()
        self._setIsModified(newVal=True) # update save icon if needed
        # return
        return self.currentUndoLevel
    
    def _redo(self, event=None):
        """
        Step the exp up one level in the @currentUndoStack@ if possible,
        and update the windows

        Returns the final undo level (0=current, >0 for further in past)
        or -1 if redo failed (probably can't redo)
        """
        if self.currentUndoLevel <= 1:
            return -1 # can't redo, we're already at latest state
        self.currentUndoLevel -= 1
        self.exp = deepcopy(self.currentUndoStack[-self.currentUndoLevel]['state'])
        # set undo redo buttons
        self._enableUndo(True) # if we've redone then undo must be possible
        if self.currentUndoLevel == 1:
            self._enableRedo(False)
        self.updateAllViews()
        self._setIsModified(newVal=True) # update save icon if needed
        # return
        return self.currentUndoLevel
    
    def _enableRedo(self,enable=True):
        self.toolbar.EnableTool(self.IDs.tbRedo,enable)
        self.editMenu.Enable(wx.ID_REDO,enable)
        
    def _enableUndo(self,enable=True):
        self.toolbar.EnableTool(self.IDs.tbUndo,enable)
        self.editMenu.Enable(wx.ID_UNDO,enable)
        
    def _setLoggerSettings(self, event=None):
        dlg = DlgLoggerSettings(frame=self)
        if dlg.OK:
            self.addToUndoStack("edit logger settings")
            
    def _setDisplaySettings(self, event=None):
        dlg = DlgDisplaySettings(frame=self)
        if dlg.OK:
            self.addToUndoStack("edit display settings")
    
    def _testRoutineCondition(self, event=None):
        
        if not os.path.isfile(self.filename):
            showInfo("You have to save the experiment before running a test.")
            return
        else:
            if not self._fileSave():
                return  # User might cancel during save
        
        instFilename = os.path.join( os.path.dirname(self.filename), "test-%f.inst.xml" % time.time())
        cr = self.routinePanel.getCurrentCondition()
        self.exp.generateRoutineInstance(cr.routine.getName(), cr.getName(), instFilename, self.filename)
        p = subprocess.Popen(['python', 'runexperiment.py', instFilename, '-closeWindows'],
                            cwd=os.path.join(os.environ['EXPYVRROOT'], 'expyvr', 'src', 'controller'))
        p.wait()
        os.remove(instFilename)
    
    def _testExperiment(self, event=None):
        
        if not os.path.isfile(self.filename):
            showInfo("You have to save the experiment before running a test.")
            return
        else:
            if not self._fileSave():
                return  # User might cancel during save
        
        instFilename = os.path.join( os.path.dirname(self.filename), "test-%f.inst.xml" % time.time())
        self.exp.generateInstance(instFilename, self.filename)
        p = subprocess.Popen(['python', 'runexperiment.py', instFilename, '-closeWindows'],
                            cwd=os.path.join(os.environ['EXPYVRROOT'], 'expyvr', 'src', 'controller'))
        p.wait()
        os.remove(instFilename)
    
    def _runInstance(self, event=None):
        """
        Lets the user select an instance file and runs the file 
        with the maincontroller
        """
        initPath = os.path.dirname(self.filename)
        
        os.getcwd()        
        dlg = wx.FileDialog(self, message="Select instance to run ...", defaultDir=initPath,
            style=wx.FD_OPEN|wx.FD_CHANGE_DIR, wildcard=helpers.getInstFileWildcard())
        
        if dlg.ShowModal() == wx.ID_OK:
            self.instanceFileName = dlg.GetPath()
            self._startExperiment(self.instanceFileName)
    
    def _rerunInstance(self, event=None):
        if len(self.instanceFileName) > 0:
            self._startExperiment(self.instanceFileName)
        else:
            showError("You have to run an instance before you can rerun it.")
    
    def _startExperiment(self, instanceFile):
        # start the experiment in a new process
        subprocess.Popen(['python', 'runexperiment.py', instanceFile],
            cwd=os.path.join(os.environ['EXPYVRROOT'], 'expyvr', 'src', 'controller'))
        
    def _genInstance(self, event=None):
        """
        Generate an instance in a specific place
        """
        if not self._fileSave():
            return False # User might cancel during save
        filename = self.filename.replace(".exp.xml", ".inst.xml")
        initPath, filename = os.path.split(filename)

        os.getcwd()
        dlg = wx.FileDialog(self, message="Generate instance ...", defaultDir=initPath,
            defaultFile=filename, style=wx.FD_SAVE|wx.FD_CHANGE_DIR,
            wildcard=helpers.getInstFileWildcard())
        
        if dlg.ShowModal() == wx.ID_OK:
            newPath = dlg.GetPath()
            # actually generate instance
            self.exp.generateInstance(newPath, self.filename)
        try: # this seems correct on PC, but not on mac
            dlg.destroy()
        except:
            pass
        
    def _genAllInstances(self, event=None):
        """
        Let the user choose for which loops that are shuffled all possible 
        randomisations should be generated and where the instances should be
        saved.
        """
        dlg = DlgGenAllInstances(self, self.exp.flow)
        if dlg.OK:
            # Create the list of loops that are shuffled to generate all randomisations
            generateAllFor = []
            numinstances = dlg.max_num_instances
            for name, param in dlg.params.iteritems():
                if param.val and param.valType == 'bool':
                    generateAllFor.append(name)
            
            # Show the directory dialog where to store the instances
            dlg = wx.DirDialog(self, message="Generate many instances ...", 
                defaultPath=os.path.dirname(self.filename))
            
            if dlg.ShowModal() == wx.ID_OK:
                newPath = dlg.GetPath()
                # actually generate instances
                self.exp.generateAllInstances(newPath, self.filename, generateAllFor, numinstances)
            try: # this seems correct on PC, but not on mac
                dlg.destroy()
            except:
                pass



if __name__=='__main__':
    try:
        app = App()
        app.MainLoop()
    except:
        storeTracebackAndShowError("An error occured and ExpyVR has to be terminated.")
        sys.exit(-1)
