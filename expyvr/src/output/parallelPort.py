'''
Python wrapper for input/output parallel port interface DLL

@author: Nathan Evans
@version: March 15, 2011
'''

import platform, os
from ctypes import *
from ctypes.util import find_library

class ParallelPort():
    lib = None          #input/output DLL

    def __init__(self,address):
        if ParallelPort.lib is None:
            #Load dll
            try:
                if platform.system() == "Windows":
                    #self.lib = cdll.LoadLibrary(find_library('inpout32.dll'))     
                    ParallelPort.lib = windll.inpout32
                    
                elif platform.system() == "Darwin" or platform.system() == "Linux":
                    raise RuntimeError("Darwin & *nix are currently unsupported in HALCA")    
            
            except Exception:
                raise RuntimeError("Failed to import parallel port interface (inpout32.dll). Ensure it's in the system DLL search path.")

        #Clear parallel port.
        try:
            self.write(0,address)
        except Exception:
            raise RuntimeError("Could not clear parallel port on initialization. Interface library problem.")


    '''
    Setup function prototypes for python-suppoted type casting/checking 
    '''
    def setupArgTypes(self):
        '''
        /* Definitions in the build of inpout32.dll are:            */
        /*   short _stdcall Inp32(short PortAddress);               */
        /*   void _stdcall Out32(short PortAddress, short data);    */
        
        /* prototype (function typedef) for DLL function Inp32: */        
        typedef short (_stdcall *inpfuncPtr)(short portaddr);
        typedef void (_stdcall *oupfuncPtr)(short portaddr, short datum);
        '''
        ParallelPort.lib.Inp32.argtypes = [c_short]                                                              #read from parallel port (input address)
        ParallelPort.lib.Inp32.restype = c_short                    
        ParallelPort.lib.Out32.argtypes = [c_short, c_short]                                                      #write to parallel port (out address, data)
        ParallelPort.lib.Out32.restype = c_void_p                                                 


    '''
    Quick interface functions
    '''
    def write(self,data,address):
        ParallelPort.lib.Out32(int(address,16),data)
        
    def read(self,address):
        return ParallelPort.lib.Inp32(int(address,16))


    def cleanup(self):
        return          #do nothing