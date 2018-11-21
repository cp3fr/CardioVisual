=============================

  Python toolkit for LNCO

+ ExpyVR builder interface

=============================


1. Requirements
2. Installation
3. Launch expyVR builder
4. MS Windows
5. Team


Requirements
------------

Python 2.6
lxml 2.2.4
pyglet 1.1.4
wxPython 2.8.X
PIL 1.1.7
NumPy 1.5.x
SciPy 0.8.0
OpenCV 2.1.0
pysvn Extension 1.7.4
pyserial 2.5
pyUSB 1.0


Installation
------------

Install python from python.org. Choose version 2.6.x. 
Do NOT install the x64 versions or higher verions (2.7 or 3.x) because many dependencies are not compatible (as of today, 10.08.2010)...

Install lxml 2.2.4 from http://pypi.python.org/pypi/lxml/2.2.4 (for Python 2.6)

Install pyglet 1.1.4 from http://www.pyglet.org/download.html (for Python 2.6)
Overwrite the existing vertexattribute.py in python26/Lib/site-packages/pyglet/graphics/
with the version from the svn in /doc/installation/pyglet-hack/

Install wxPython 2.8.x from http://www.wxpython.org/download.php#binaries (win32 unicode for Python 2.6)

Install PIL 1.1.7 from http://www.pythonware.com/products/pil/ (for Python 2.6)

Install NumPy 1.5.x from http://sourceforge.net/projects/numpy/files/ (win32 for Python 2.6)

Install SciPy 0.8.0 from http://sourceforge.net/projects/scipy/files/ (win32 for Python 2.6)

Install OpenCV 2.1.0 from http://sourceforge.net/projects/opencvlibrary/files/ (win32 vs2008)
For creating the all-in-one package:
- Create new folder 'bin' in the python26 folder (where python was installed to)
- Copy all the .dll from OpenCv2.1\bin\ to that folder
- Copy all the contents of the OpenCV2.1\Python2.6\Lib\site-packages\ to the python26\Lib\site-packages\
- This is all we need from the OpenCV install

Install pysvn Extension 1.7.4 from http://pysvn.tigris.org/project_downloads.html (svn 1.6.12)

Install pyserial 2.5 from http://pypi.python.org/pypi/pyserial (win32 for Python 2.x)

Install avbin from http://code.google.com/p/avbin/ (avbin-win32-5.zip)
For creating the all-in-one package:
- Copy the avbin.dll to the python26\bin\ folder

Get the source of pylnco from svn :
svn co https://svn.epfl.ch/svn/pylnco/trunk pylnco
Use your EPFL gaspar id to login.

Install pyUSB 1.0.0-alpha-1 from http://sourceforge.net/projects/pyusb/
Run 'python setup.py install'


Lanch expyVR builder
-----------------

Launch "builder.py" which is in "src\expbuilder\app"

-> (1) the click way: double click on builder.py
-> (2) the console way: change to the src\expbuilder\app directory and run "python ./builder.py"

(launching the builder in a console from another directory does not work, unless you add the path to "src\" into your PYTHON_PATH environment variable).


Team
----

Staff    : Nathan, Bruno, Danilo
Students : Tobias Leugger (2010)
