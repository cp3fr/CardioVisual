"""
A central location to store information about urls  

@author: Tobias Leugger
@since: Spring 2010

@attention: Adapted from parts of the PsychoPy library
@copyright: 2009, Jonathan Peirce, Tobias Leugger
@license: Distributed under the terms of the GNU General Public License (GPL).
"""

import wxIDs
import os

urls={}

#links keyed by wxIDs (e.g. menu item IDs)
urls[wxIDs.expyvrTrac]="http://expyvr.rpg-forge.com/newticket"
urls[wxIDs.expyvrHome]="http://svn.epfl.ch/polysvn/protected/repository/manage.do?id=1020"
urls[wxIDs.builderHelp]="file:///" + os.getenv('EXPYVRROOT') + "/expyvr/doc/html/index.html"
