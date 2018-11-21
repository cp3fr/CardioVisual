"""
Extensible set of components for the ExpyVR Builder

@author: Tobias Leugger
@since: Spring 2010

@attention: Adapted from parts of the PsychoPy library
@copyright: 2009, Jonathan Peirce, Tobias Leugger
@license: Distributed under the terms of the GNU General Public License (GPL).
"""

import wx, imp, Image
from os.path import *
from lxml import etree

from expbuilder.app.components.component import Component
from expbuilder.app.errors import storeTracebackAndShowWarning


_compTypes = []     # list of components, in the order that they where specified in the xml
_icons = {}         # icons of all the components
_importPaths = {}   # import paths of all the components
_moduleMains = {}   # the ModuleMain class of all the components

def _pilToBitmap(pil):
    image = wx.EmptyImage(pil.size[0], pil.size[1])
    image.SetData(pil.convert("RGB").tostring())
    image.SetAlphaData(pil.convert("RGBA").tostring()[3::4])
    return image.ConvertToBitmap()#wx.Image and wx.Bitmap are different


def _getIcons(icon, directory):
    """
    Creates wxBitmaps ``self.icon`` and ``self.iconAdd`` based on the the image. 
    The latter has a plus sign added over the top.
    The file must be in the resources folder. 
    
    png files work best, but anything that wx.Image can import should be fine
    """
    if directory is None:
        directory = dirname(abspath(__file__))
    
    # if the filename given does not work, try to find the file in the given directory or the ressources folder
    if exists(abspath(icon)):
        filename = abspath(icon)
    elif exists( join(directory, icon) ):
        filename = join(directory, icon) 
    else:
        filename = join(directory, 'resources', icon)
        
    # if the filename is not valid anyway, setup the default icon
    if not exists(filename):
        filename = join(dirname(abspath(__file__)), 'resources', 'base.png')
    im = Image.open(filename)
    icon = _pilToBitmap(im)
    
    # add the plus sign
    add = Image.open(join(dirname(abspath(__file__)), 'resources', 'add.png'))
    im.paste(add, [0,0,add.size[0], add.size[1]], mask=add)
    iconAdd = _pilToBitmap(im)
    
    # add the disabled sign
    dis = Image.open(join(dirname(abspath(__file__)), 'resources', 'disabled.png'))
    im = Image.open(filename)
    im.paste(dis, [0,0,dis.size[0], dis.size[1]], mask=dis)
    iconDisabled = _pilToBitmap(im)

    return icon, iconAdd, iconDisabled


def importAllComponents(filename=None, hiddenComponents=[]):
    """
    Imports all modules specified in the components.xml file in the same directory.
    Also loads the corresponding icon files in the resources folder
    """
    # Read the component types and import paths from xml file
    parser = etree.XMLParser(remove_blank_text=True)
    # if no filename is provided, read the default components (in same folder as py file)
    if filename is None:
        filename = join(dirname(abspath(__file__)), 'components.xml')

    f = None
    try:
        f = open(filename)
        root = etree.XML(f.read(), parser)
        for comp in root.findall('Components/Component'):
            if comp.attrib['type'] not in hiddenComponents:
                _compTypes.append(comp.attrib['type'])
                _importPaths[comp.attrib['type']] = comp.attrib['importPath']
                if comp.attrib.has_key('icon'):
                    _icons[comp.attrib['type']] = _getIcons(comp.attrib['icon'], dirname(abspath(filename)))
        
        # Import all the components and prepare the icons
        for type, importPath in _importPaths.items():
            fp = None
            try:
                # if not set when loading xml, set the icon by guessing filename from module type 
                if not _icons.has_key(type):
                    _icons[type] = _getIcons(type.lower() + '.png', dirname(abspath(filename)))
                
                # Load the module
                module = imp.new_module('dummy')
                module.__path__ = None
                for moduleName in importPath.split('.'):
                    fp, pathname, description = imp.find_module(moduleName, module.__path__)
                    module = imp.load_module(moduleName, fp, pathname, description)
                _moduleMains[type] = module.ModuleMain
            except:
                # If we can't load a component, simply delete it from the components
                _compTypes.remove(type)
                del _importPaths[type]
                if type in _icons:
                    del _icons[type]
                storeTracebackAndShowWarning('Component %s could not be loaded.' % type)
            finally:
                # Since we may exit via an exception, close fp explicitly.
                if fp is not None:
                    fp.close()
    except:
        storeTracebackAndShowWarning('Component descriptor %s is not valid.' %  filename )
    finally:
        if f is not None:
            f.close()
        
        
def getNewComponent(exp, type, name=''):
    """
    Returns a newly created component of the given type and with the given name
    """
    return Component(exp, type, _importPaths[type], _moduleMains[type], name)
    
    
def getAllComponentTypes():
    """
    Returns a list of the types of all components
    """
    return _compTypes
    
    
def getComponentIcon(type, symbol=0):
    """
    Retruns the icon of the given type with either a plus symbol
    added on the image or not
    """
    if symbol == 1:
        return _icons[type][1]
    elif symbol == 2:
        return _icons[type][2]
    return _icons[type][0]


