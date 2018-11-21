from pyglet.gl import *


def get_model_matrix(array_type=c_float, glGetMethod=glGetFloatv):
    """
    Returns the current modelview matrix.
    """
    m = (array_type*16)()
    glGetMethod(GL_MODELVIEW_MATRIX, m)
    return m

def get_projection_matrix(array_type=c_float, glGetMethod=glGetFloatv):
    """
    Returns the current modelview matrix.
    """
    m = (array_type*16)()
    glGetMethod(GL_PROJECTION_MATRIX, m)
    return m

def get_viewport():
    """
    Returns the current viewport.
    """
    m = (c_int*4)()
    glGetIntegerv(GL_VIEWPORT, m)
    return m

def screen_to_model(x,y,z):
    m = get_model_matrix(c_double, glGetDoublev)
    p = get_projection_matrix(c_double, glGetDoublev)
    w = get_viewport()
    mx,my,mz = c_double(),c_double(),c_double()
    gluUnProject(x,y,z,m,p,w,mx,my,mz)
    
    return float(mx.value),float(my.value),float(mz.value)

def model_to_screen(x,y,z):
    m = get_model_matrix(c_double, glGetDoublev)
    p = get_projection_matrix(c_double, glGetDoublev)
    w = get_viewport()
    
    mx,my,mz = c_double(),c_double(),c_double()
    gluProject(x,y,z,m,p,w,mx,my,mz)
    return float(mx.value),float(my.value),float(mz.value)


  #Set the orthographic projection for 2d drawing
def _set_2d(self,w,h):

        near = 0.0
        far  = 10.0
    
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, w, 0, h, near, far)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()


    #Unset the orthographic projection for 2d drawing
def _unset_2d(self,):
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
