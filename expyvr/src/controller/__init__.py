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
Controller module
Created on Nov 23, 2010
@author: tobias
'''

from os import path, getenv
from re import findall, sub


def getPathFromString(p):
    # interpret variables in the form $VARNAME$ in path as OS environment variables
    for var in findall( '\$(.*?)\$', p ):
        var = sub( '[\\\]', '/', getenv(var,'/') )
        p = sub( '\$.*?\$', var, p, count=1)
    return path.normpath(p)
