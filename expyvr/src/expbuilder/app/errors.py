"""
@author: Tobias Leugger
@since: Spring 2010

@attention: Adapted from parts of the PsychoPy library
@copyright: 2009, Jonathan Peirce, Tobias Leugger
@license: Distributed under the terms of the GNU General Public License (GPL).
"""

import wx, traceback, time, os

class ErrorDialog(wx.Dialog):
    """
    A simple dialog to show some message to the user
    """
    def __init__(self, message, title):
        wx.Dialog.__init__(self, parent=None, id=-1, title=title)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Add message
        message = wx.StaticText(self, -1, message)
        message.Wrap(400)
        sizer.Add(message, flag=wx.ALL, border=15)
        
        # Add buttons
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.okBtn = wx.Button(self,wx.ID_OK, 'OK')
        self.okBtn.SetDefault()
        self.Bind(wx.EVT_BUTTON, self.onButton, id=wx.ID_OK)
        btnSizer.Add(self.okBtn)
        sizer.Add(btnSizer, flag=wx.ALIGN_RIGHT|wx.ALL, border=5)
        
        # Configure sizers and fit
        self.SetSizerAndFit(sizer)
        self.Center()
        
    def onButton(self,event):
        self.EndModal(event.GetId())

def showInfo(infoText):
    """
    Shows a message dialog with the passed info 
    """
    ErrorDialog(message=infoText, title='Info').ShowModal()    

def showWarning(warningText):
    """
    Shows a message dialog with the passed warning 
    """
    ErrorDialog(message=warningText, title='Warning').ShowModal()

def showError(errorText):
    """
    Shows a message dialog with the passed error 
    """
    ErrorDialog(message=errorText, title='Error').ShowModal()
    
def storeTracebackAndShowWarning(warningText):
    """
    Stores the traceback of the last error to file and shows the warningText.
    Adds a line to to the warningText saying it stored the warning to file. 
    """
    path, error = storeTraceback()
    warningText += '\nInfo about this warning was stored to a file in\n%s.' % path
    warningText += '\n\nFYI, last error line is: \n%s\n' % error
    showWarning(warningText)
    
def storeTracebackAndShowError(errorText):
    """
    Stores the traceback of the last error to file and shows the errorText.
    Adds a line to to the errorText saying it stored the error to file. 
    """
    path, error = storeTraceback()
    errorText += '\n\nComplete error log was stored in %s' % path
    errorText += '\n\nFYI, last error line is: \n%s\n' % error
    showError(errorText)
    
def storeTraceback():
    """
    Stores the traceback of the last error to a file in the cwd.
    Returns the path where the file was stored
    """
    if(os.environ.has_key('EXPYVRROOT')):
        path = os.path.join(os.environ['EXPYVRROOT'], 'log')
        if not os.path.isdir(path):
            os.mkdir(path)
    else:
        path = os.getcwd()
    path = os.path.join(path, 'expyvrerror.log')
    f = open(path, 'a')
    f.write('\nTime: %s:\n' % time.strftime("%d %b %Y %H:%M:%S"))
    traceback.print_exc(file=f)
    listoferrorlines = traceback.format_exc().splitlines()
    print listoferrorlines
    f.close()
    return path, listoferrorlines[len(listoferrorlines)-1]

