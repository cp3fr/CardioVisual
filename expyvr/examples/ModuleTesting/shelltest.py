'''
Created on May 12, 2010

Test the core functionality of ExpyVR toolkit 

@author: nathan
'''

import os,sys

#We have to modify PYTHONPATH to include the sources tree
#must know the OS delimiter... for window$$ & unix compatibility
ds = os.path.sep
sys.path.append('..'+ds+'src')

from controller import maincontrol
 
    
if __name__ == "__main__":
    cont = maincontrol.MainControl()
    cont.loadExperiment('gui/testExp.inst.xml')
    cont.startExperiment()
    

    #sys.exit(main())
