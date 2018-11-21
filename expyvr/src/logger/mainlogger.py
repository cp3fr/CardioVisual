"""
Takes care of periodic backups, logging and stopping
people from overwriting their data files.

@author: Tobias Leugger, Danilo Rezende
@since: Spring 2010
"""

import pyglet, csv, os, re
from time import time as unix_time
from time import strftime, localtime
from datetime import timedelta
from datetime import datetime

from controller import getPathFromString

class Logger():
    def __init__(self, controller, backup_dt, path, description, mode='console'):        
        # publics
        self.backup_dt = float(backup_dt)   # every how many seconds the log is written to file
        self.mode = mode                    # modes = console, file, console-file (both)
        self.description = description

        # privates
        self._controller = controller     
        self._gTimeManager = self._controller.gTimeManager
        self._lastWriteTime = 0.0
        self._stopped = False
        # the main logs
        self._logWriter = None
        self._logData = []          # a list of lists with the following elements: 'componentType', 'componentName', 'absoluteTime', 'relativeTime', 'logData'
        self._logBuffer = []
        # the remembered start and stop times
        self._startTimes = {}
        self._startingModules = []
    
        # interpret variables in the form $VARNAME$ in path as OS environment variables
        path = getPathFromString(path)
    
        # Make sure the log path exists
        if not os.path.isdir(path):
            os.makedirs(path)
        self.Path = os.path.realpath(path)
            
        # Setup file log
        if self.mode != 'console':
            # Create a new log file, making sure it doesn't overwrite anything
            fname = datetime.today().strftime('%y%m%d%H%M%S_') + description + '_log'
            fname = os.path.join(self.Path, fname)
            fname = self._getFreeFilename(fname, '.csv')
            self.logFileName = fname
            self._logWriter = csv.writer(open(self.logFileName, 'wb'))
            # Write the header row
            self._logWriter.writerow(['componentType', 'componentName', 'absoluteTime', 'relativeTime', 'displayTime', 'message'])
#            file.close(
    
    def _getFreeFilename(self, filename, extension=""):
        """
        Returnes a filename that is not existing based on the filename passed.
        The filename can be an absolute or relative path,
        The extension should be given with the the leading dot
        """
        freeName = filename + extension
        number = 0
        while os.path.isfile(freeName) or os.path.isdir(freeName):
            freeName = filename + '-' + str(number) + extension
            number += 1
        return freeName

    def start(self, verbose=True):
        """
        Start the logger: Schedule regular saving of the log data
        """
        if self.mode != 'console' and self.backup_dt > 0:
            pyglet.clock.schedule_interval(self._saveMe, self.backup_dt)
            if verbose:
                print 'logger scheduled to save to file every %.2f seconds'%self.backup_dt
                
        # schedule buffer logging mechanism at each frame (Starting next frame)
        pyglet.clock.schedule(self._doLog)
        if verbose:
            self._log('Logger Started')
        
        # reset 
        self._startTimes = {}
        self._startingModules = []
        
        # explicit buffer logging now
        self._doLog()

    def logMe(self, compType, compName, message):
        """
        Main log function. compType is the module that is logging
        and compName the name of the instance.
        message can be anything that can be converted to a string.
        """
        absTime = "%0.4f"%self._gTimeManager.absoluteTime()
        expTime = "%0.4f"%self._gTimeManager.experimentTime()
        # push the data to log into the temporary buffer
        self._logBuffer.append([compType, compName, absTime, expTime, str(message)])
        
    def logMeStart(self, compType, compName, configName):
        absTime = self._gTimeManager.absoluteTime()
        expTime = self._gTimeManager.experimentTime()
        # push the data to log into the temporary buffer
        self._logBuffer.append([compType, compName, str("%0.4f"%absTime), str("%0.4f"%expTime), str("Starting config: " + configName)])
        self._startTimes[compName] = [absTime, expTime, -1]
        self._startingModules.append(compName)
        
    def logMeStop(self, compType, compName, configName):
        self.logMe(compType, compName, str("Stopped  config: " + configName))
        # remove start time of stopped component
        if self._startTimes.has_key(compName):
            self._startTimes.pop(compName)
        
    def getStartingTimes(self, compName):
        if self._startTimes.has_key(compName):
            return self._startTimes[compName]
        else:
            return [-1, -1, -1]

    def stop(self):
        """
        Stops the logger, writes out all the log messages
        """
        if self._stopped:
            # We're already stopped
            return
        
        self._startTimes = {}
        self._startingModules = []
        
        # Unschedule the saving
        pyglet.clock.unschedule(self._saveMe)
        pyglet.clock.unschedule(self._doLog)
        
        # Log summary of the experiment duration
        expEndTime = self._gTimeManager.absoluteTime()
        self._log('Experiment started %s and ended %s' % 
                  (strftime("%a, %d %b %Y %H:%M:%S", localtime(self._gTimeManager._time_of_start)),
                   strftime("%a, %d %b %Y %H:%M:%S", localtime(unix_time()))))
        self._log('Total experiment duration: %s, unpaused experiment duration: %s' % 
                  (timedelta(seconds=expEndTime - self._gTimeManager._time0), 
                   timedelta(seconds=self._gTimeManager.experimentTime())))
        # explicit buffer logging
        self._doLog()
        # Make sure everything is written to file
        self._saveMe()
        self._stopped = True
        print('\nLogger stopped\n')
        
    def _saveMe(self, dt=0.0):
        """
        Writes all the log messages since the last time to the log file
        """
        # save the main logs
        if self._logWriter is not None:
            # time the saving
            t0 = self._gTimeManager.absoluteTime()
            # save log
            self._logWriter.writerows(self._logData)
            # echo
            dt = self._gTimeManager.absoluteTime() - t0
            self._log('Logs %s saved in %.1f ms' %(self.logFileName, dt*1000.0))
        
        # Reset the data list
        self._logData = []
        
    def _log(self, message):
        """
        Wrapper for logging inside the logger
        """
        self.logMe('mainLogger', 'mainLogger', message)

    def _doLog(self, dt=0):
        """
        Perform the actual logging ONE FRAME AFTER it has been asked by calls to 'logMe'
        This allows to have the EXACT display time of the current frame.
        """
        # fill in the display times of starting modules
        for m in self._startingModules:
            self._startTimes[m][2] = self._gTimeManager.displayTime()
        self._startingModules = []
        
        # make a string of display time
        dispTime = "%0.4f"%self._gTimeManager.displayTime()
        # empty the temp buffer of logs into console and/or file
        for logElement in self._logBuffer:
            
            if self.mode in ['file', 'console-file'] and not self._stopped:
                self._logData.append( logElement[0:4] + [dispTime] + logElement[4:])
            
            if self.mode in ['console', 'console-file'] or self._stopped:
                print(str('{0:>20}:{1:<20}').format(logElement[0], logElement[1]) + "; " + logElement[3] + "; " + dispTime + "; " + logElement[4])
                
        self._logBuffer = []

