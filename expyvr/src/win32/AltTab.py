'''
Created on Jul 8, 2010

@author: bh
@since: Winter 2012

@license: Distributed under the terms of the GNU General Public License (GPL).
'''

from abstract.AbstractClasses import BasicModule

import win32gui, win32api, win32con, win32process
import re

class WindowMgr:
    """Encapsulates some calls to the winapi for window management"""
    def __init__ (self):
        """Constructor"""
        self._handle = None
        self._x = 0
        self._y = 0
        self._w = 0
        self._h = 0
        
        # Emulate ALT key press to unlock the SetForegroundWindow() method
        win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_EXTENDEDKEY | win32con.KEYEVENTF_KEYUP, 0)

    def find_window(self, class_name, window_name = None):
        """find a window by its class_name"""
        self._handle = None
        self._handle = win32gui.FindWindow(class_name, window_name)
        return self._handle != None

    def _window_enum_callback(self, hwnd, wildcard):
        '''Pass to win32gui.EnumWindows() to check all the opened windows'''
        if re.match(wildcard, str(win32gui.GetWindowText(hwnd))) != None:
            self._handle = hwnd
            self._x, self._y, self._w, self._h = win32gui.GetWindowRect(hwnd)
            self._w -= self._x
            self._h -= self._y

    def find_window_wildcard(self, wildcard):
        self._handle = None
        win32gui.EnumWindows(self._window_enum_callback, wildcard)
        return self._handle != None

    def _window_id_callback(self, hwnd, id):
        '''Pass to win32gui.EnumWindows() to check all the opened windows'''
        TId, PId = win32process.GetWindowThreadProcessId(hwnd)
        if PId == id:
            self._handle = hwnd

    def find_window_process_id(self, id):
        self._handle = None
        win32gui.EnumWindows(self._window_id_callback, id)
        return self._handle != None
        
    def set_foreground(self):
        """put the window in the foreground"""
        win32gui.SetForegroundWindow(self._handle)
        
    def restore(self):
        win32gui.ShowWindow(self._handle, win32con.SW_RESTORE)
    
    def hide(self):
        win32gui.ShowWindow(self._handle, win32con.SW_HIDE)
        
    def maximize(self):
        win32gui.ShowWindow(self._handle, win32con.SW_MAXIMIZE)

    def set_position(self, x, y, w, h):
        win32gui.SetWindowPos(self._handle, win32con.HWND_NOTOPMOST, x, y, w, h, win32con.SWP_FRAMECHANGED)
        
class ModuleMain(BasicModule):
    """
    A simple module to 
    """
    defaultInitConf = {
        'name': 'AltTab'
    }
    
    defaultRunConf = {    
        'WindowName': '.*name.*',
        'maximize': False
    }
    
    confDescription = [
        ('name', 'str', "Your window switcher: simulates Alt-Tab to show another program."),
        ('WindowName', 'str', "Name of the window to switch to (regular expressions)"),
        ('maximize', 'bool', "Maximize the window when showing it.")
    ]
   
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        BasicModule.__init__(self, controller, initConfig, runConfigs)
        
        self.w = WindowMgr()
        
        # check for the existence of all window names given 
        for conf in self.runConfs.values():
            if not self.w.find_window_wildcard( conf['WindowName'] ):
                raise RuntimeError("There is no window with the name corresponding to %s."%conf['WindowName'])   
        
        self.controller = controller
           
    def start(self, dt=0, duration=-1, configName=None):
        """
        Activate the program given
        """
        BasicModule.start(self, dt, duration, configName)  
        
        # set the current window from the given program name
        if self.w.find_window_wildcard(self.activeConf['WindowName']):
        
            # show the window
            if self.activeConf['maximize']:
                # maximize if requested 
                self.w.maximize()
            else:
                # or simply restore it
                self.w.restore()
            
            # set it as foreground window
            self.w.set_foreground()
        
        # hide the expyvr window
        if self.controller.gDisplay.renderers[0].window._fullscreen:
            win32gui.ShowWindow(self.controller.gDisplay.renderers[0].window._hwnd, win32con.SW_HIDE)
        
    def stop(self, dt=0):
        # get start times before stopping module
        BasicModule.stop(self, dt)  

        # show the expyvr window
        win32gui.ShowWindow(self.controller.gDisplay.renderers[0].window._hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(self.controller.gDisplay.renderers[0].window._hwnd)
        win32gui.SetFocus(self.controller.gDisplay.renderers[0].window._hwnd)
        
        # hide the window 
        # self.w.hide()
        
    def cleanup(self):
        BasicModule.cleanup(self)
        
        # restore the window
        self.w.restore()
        
      