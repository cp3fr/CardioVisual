# -*- coding: utf-8 -*-


from pyglet.gl import *
import pyglet.image
from os.path import join, dirname
from copy import copy
from tools import vec2f, vec3f
    
def MTL(path, filename):
    contents = {}
    mtl = None
    textures = {}
    
    for line in open( join(path, filename), "r"):
        if line.startswith('#'): continue
        values = line.split()
        if not values: continue
        if values[0] == 'newmtl':
            mtl = contents[values[1]] = {}
        elif mtl is None:
            raise ValueError, "mtl file doesn't start with newmtl tag"
        elif values[0].count('map_') > 0:
            # load the texture referred by this declaration
            filename = join(path, values[1])
            if filename not in textures.keys():
                print "Loading texture", filename
                pic = pyglet.image.load( filename )
                rawimage = pic.get_image_data()
                format = 'RGBA'
                imagedata = rawimage.get_data(format, rawimage.width * len(format))
                id = c_uint()
                glGenTextures(1, byref(id))
                textures[filename] = id
                
            mtl[values[0]] = textures[filename]
            glBindTexture(GL_TEXTURE_2D, textures[filename])
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, pic.width, pic.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, imagedata)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        else:
            mtl[values[0]] = map(float, values[1:])
            
    for k in contents:     
        # default illumination model depending on available colors
        if contents[k].keys().count('illum') == 0:
            if contents[k].keys().count('Ka'):
                if contents[k].keys().count('Ks'):
                    contents[k]['illum'] = [2] # Kd, Ka & Ks
                else:
                    contents[k]['illum'] = [1] # Kd & Ka
            else:
                contents[k]['illum'] = [0] # only Kd   
    
    return contents
 
class OBJ:
    def __init__(self, filename="", swapyz=False, mtl=None):
        """Loads a Wavefront OBJ file. """
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        self.target = GL_TEXTURE_2D
        self.gl_list = -1
        self.mtl = None

        if len(filename)<1:
            return

        material = None
        print "Loading OBJ model", filename
        for line in open(filename, "r"):
            if line.startswith('#'): continue
            values = line.split()
            if not values: continue
            if values[0] == 'v':
                v = map(float, values[1:4])
                if swapyz:
                    v = v[0], v[2], v[1]
                self.vertices.append(v)
            elif values[0] == 'vn':
                v = map(float, values[1:4])
                if swapyz:
                    v = v[0], v[2], v[1]
                self.normals.append(v)
            elif values[0] == 'vt':
                self.texcoords.append(map(float, values[1:3]))
            elif values[0] in ('usemtl', 'usemat'):
                material = values[1]
            elif values[0] == 'mtllib':
                if mtl is None:
                    self.mtl = MTL( dirname(filename), values[1] )
                else:
                    self.mtl = mtl
            elif values[0] == 'f':
                face = []
                texcoords = []
                norms = []
                for v in values[1:]:
                    w = v.split('/')
                    face.append(int(w[0]))
                    if len(w) >= 2 and len(w[1]) > 0:
                        texcoords.append(int(w[1]))
                    else:
                        texcoords.append(0)
                    if len(w) >= 3 and len(w[2]) > 0:
                        norms.append(int(w[2]))
                    else:
                        norms.append(0)
                self.faces.append((face, norms, texcoords, material))
 
        self.generate_displaylist()
 
    def generate_displaylist(self): 
 
        print "Generating openGL display list"
        self.gl_list = glGenLists(1)
        glNewList(self.gl_list, GL_COMPILE)
        glFrontFace(GL_CCW)
        currentmaterial = "(null)" # this is also the OBJ default string
        texture_changed = False
        for face in self.faces:
            vertices, normals, texture_coords, material = face
            if material == "(null)" or material == "" or material is None:
                glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, vec3f([0,0,0]))
                glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, vec3f([0,0,0]))
                glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, vec3f([0,0,0]) )
                glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 0)
                glDisable(GL_TEXTURE_2D)

            elif material != currentmaterial:
                mtl = self.mtl[material]
                currentmaterial = material
                
                # illum 0  =  only color
                glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, vec3f(mtl['Kd']))
                # illum 1 and more =  Ambient on
                if (mtl['illum'][0] > 0):
                    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, vec3f(mtl['Ka']))
                # illum 2 and more = Specular on
                if (mtl['illum'][0] > 1):
                    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, vec3f(mtl['Ks']))
                    shininess = min(mtl['Ns'][0], 127)
                    glMaterialf (GL_FRONT_AND_BACK, GL_SHININESS, shininess)
                else:
                    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, vec3f([0,0,0]) )
                    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 0)

                # the diffuse color texture map : Texture[0] in GLSL
                if 'map_Kd' in mtl:
                    texture_changed = True
                    glActiveTexture(GL_TEXTURE0)
                    glEnable(GL_TEXTURE_2D)
                    glBindTexture(GL_TEXTURE_2D, mtl['map_Kd'])
                # the ambient texture map : Texture[1]
                if 'map_Ka' in mtl:
                    texture_changed = True
                    glActiveTexture(GL_TEXTURE1)
                    glEnable(GL_TEXTURE_2D)
                    glBindTexture(GL_TEXTURE_2D, mtl['map_Ka'])
                # specular color texture map : Texture[2]
                if 'map_Ks' in mtl:
                    texture_changed = True
                    glActiveTexture(GL_TEXTURE2)
                    glEnable(GL_TEXTURE_2D)
                    glBindTexture(GL_TEXTURE_2D, mtl['map_Ks'])
                # the alpha texture map : Texture[3]
                if 'map_d' in mtl:
                    texture_changed = True
                    glActiveTexture(GL_TEXTURE3)
                    glEnable(GL_TEXTURE_2D)
                    glBindTexture(GL_TEXTURE_2D, mtl['map_d'])
                # bump map (which by default uses luminance channel of the image)  : Texture[4]
                if 'map_bump' in mtl:
                    texture_changed = True
                    glActiveTexture(GL_TEXTURE4)
                    glEnable(GL_TEXTURE_2D)
                    glBindTexture(GL_TEXTURE_2D, mtl['map_bump'])
                    
            if len(vertices) == 4:
                glBegin(GL_QUADS)
            elif len(vertices) == 3:
                glBegin(GL_TRIANGLES)
            else:
                glBegin(GL_POLYGON)
            for i in range(0, len(vertices)):
                if normals[i] > 0:
                    glNormal3fv( vec3f(self.normals[normals[i] - 1]) )
                if texture_coords[i] > 0:
                    glTexCoord2fv( vec2f(self.texcoords[texture_coords[i] - 1]) )
                    
                glVertex3fv( vec3f(self.vertices[vertices[i] - 1]) )
            glEnd()
            
            if texture_changed:
                texture_changed = False
                glActiveTexture(GL_TEXTURE4)
                glDisable(GL_TEXTURE_2D)
                glActiveTexture(GL_TEXTURE3)
                glDisable(GL_TEXTURE_2D)
                glActiveTexture(GL_TEXTURE2)
                glDisable(GL_TEXTURE_2D)
                glActiveTexture(GL_TEXTURE1)
                glDisable(GL_TEXTURE_2D)
                glActiveTexture(GL_TEXTURE0)
                glDisable(GL_TEXTURE_2D)
            
        glEndList()
        
    def draw(self):
        glCallList(self.gl_list)
#        
#    def __copy__(self, memo):
#        newone = type(self)()
#        # copy of vertices, normals and other arrays
#        self.vertices = memo.vertices[:]
#        self.normals = memo.normals[:]
#        self.texcoords = memo.texcoords[:]
#        self.faces = memo.faces[:]
#        # simple copy of the rest
#        self.target = GL_TEXTURE_2D
#        self.gl_list = memo.gl_list

    def __copy__(self):
        newone = OBJ()
        newone.__dict__.update(self.__dict__)
        return newone

class MORPH:

    def __init__(self, filename_base, filename_target, steps = 0, swapyz=False):
        # check validity of steps argument
        if steps < 0 or steps > 20:
            print 'invalid number of steps'
            return
        self.steps = steps + 2
        # create the array of meshes
        self.mesh = [None for i in range(self.steps)]
        # initialize the array of meshes
        self.mesh[0]=OBJ(filename_base, swapyz)
        for m in range(1, self.steps-1):
            self.mesh[m] = copy(self.mesh[0])
        self.mesh[self.steps-1]=OBJ(filename_target, swapyz, self.mesh[0].mtl)
        # test validity of meshes
        if len(self.mesh[0].faces) != len(self.mesh[self.steps-1].faces) or len(self.mesh[0].vertices) != len(self.mesh[self.steps-1].vertices):
            print "not same topology"
            return
        # compute the difference vector between the corresponding vertices of the two objects
        diff = []
        for i in range(len(self.mesh[0].vertices)):
            diff.append( [self.mesh[self.steps-1].vertices[i][j] - self.mesh[0].vertices[i][j] for j in range(3)] )
        # generate morph vertices and display lists for intermediate objects
        for m in range(1, self.steps-1):
            morphfactor = float(m) / float(len(self.mesh)-1)
            print "Generating morph mesh of %s and %s at %d%%"%(filename_base, filename_target, int(morphfactor * 100.0) )
            self.mesh[m].vertices = []
            for i in range(len(self.mesh[0].vertices)):
                v = self.mesh[0].vertices[i][0]+ morphfactor * diff[i][0], self.mesh[0].vertices[i][1]+ morphfactor * diff[i][1], self.mesh[0].vertices[i][2]+ morphfactor * diff[i][2] 
                self.mesh[m].vertices.append( v )
            self.mesh[m].generate_displaylist()
        
    def draw(self, percent=0):
        percent = max(0, min(percent, 100))
        # find the object in mesh array closest to the percentage requested
        i = int(round(float(percent)/100.0*float(len(self.mesh)-1)))
        # draw the intermediate mesh
        self.mesh[i].draw()
