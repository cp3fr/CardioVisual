from ctypes import (
    byref, c_char, c_char_p, c_int, cast, create_string_buffer, pointer,
    POINTER
)
from pyglet import gl


class ShaderError(Exception): pass
class CompileError(ShaderError): pass
class LinkError(ShaderError): pass


shaderErrors = {
    gl.GL_INVALID_VALUE: 'GL_INVALID_VALUE (bad 1st arg)',
    gl.GL_INVALID_OPERATION: 'GL_INVALID_OPERATION '
        '(bad id or immediate mode drawing in progress)',
    gl.GL_INVALID_ENUM: 'GL_INVALID_ENUM (bad 2nd arg)',
}


class _Shader(object):

    shadertype = None

    def __init__(self, sources):
        if isinstance(sources, file):
            self.sources = self.read_source(sources)
        elif isinstance(sources, basestring):
            self.sources = [sources]
        else:
            self.sources = sources
        self.id = None
        
    def read_source(self, f):
        try:
            src = f.read()
        finally:
            f.close()
        return src
        
    def _get(self, paramId):
        outvalue = c_int(0)
        gl.glGetShaderiv(self.id, paramId, byref(outvalue))
        value = outvalue.value
        if value in shaderErrors.keys():
            msg = '%s from glGetShader(%s, %s, &value)'
            raise ValueError(msg % (shaderErrors[value], self.id, paramId))
        return value


    def getCompileStatus(self):
        return bool(self._get(gl.GL_COMPILE_STATUS))


    def getInfoLogLength(self):
        return self._get(gl.GL_INFO_LOG_LENGTH)


    def getInfoLog(self):
        length = self.getInfoLogLength()
        if length == 0:
            return ''
        buffer = create_string_buffer(length)
        gl.glGetShaderInfoLog(self.id, length, None, buffer)
        return buffer.value


    def _srcToArray(self):
        num = len(self.sources)
        all_source = (c_char_p * num)(*self.sources)
        return num, cast(pointer(all_source), POINTER(POINTER(c_char)))
        

    def compile(self):
        self.id = gl.glCreateShader(self.shadertype)

        num, src = self._srcToArray()
        gl.glShaderSource(self.id, num, src, None)
        
        gl.glCompileShader(self.id)

        if not self.getCompileStatus():
            raise CompileError(self.getInfoLog())



class VertexShader(_Shader):
    shadertype = gl.GL_VERTEX_SHADER


class FragmentShader(_Shader):
    shadertype = gl.GL_FRAGMENT_SHADER



class ShaderProgram(object):

    def __init__(self, *shaders):
        self.shaders = list(shaders)
        while self.shaders.count(None):
            self.shaders.remove(None)
        self.id = None
        self.locationTexture = {}
        self.uniform = {}
    
    def _get(self, paramId):
        outvalue = c_int(0)
        gl.glGetProgramiv(self.id, paramId, byref(outvalue))
        value = outvalue.value
        if value in shaderErrors.keys():
            msg = '%s from glGetProgram(%s, %s, &value)'
            raise ValueError(msg % (shaderErrors[value], self.id, paramId))
        return value
        
        
    def getLinkStatus(self):
        return bool(self._get(gl.GL_LINK_STATUS))


    def getInfoLogLength(self):
        return self._get(gl.GL_INFO_LOG_LENGTH)


    def getInfoLog(self):
        length = self.getInfoLogLength()
        if length == 0:
            return ''
        buffer = create_string_buffer(length)
        gl.glGetProgramInfoLog(self.id, length, None, buffer)
        return buffer.value
        

    def _getMessage(self):
        messages = []
        for shader in self.shaders:
            log = shader.getInfoLog()
            if log:
                messages.append(log)
        log = self.getInfoLog()
        if log:
            messages.append(log)
        return '\n'.join(messages)

        
    def set_uniform(self, name, value):
        self.use()
        if not self.uniform.has_key(name):
            self.uniform[name] = gl.glGetUniformLocation(self.id, name);
        if type(value) == int:
            gl.glUniform1i(self.uniform[name], value);
        elif type(value) == float:
            gl.glUniform1f(self.uniform[name], value);
        
    def use(self):
        if (self.id == None):
            self.id = gl.glCreateProgram()
            
            for shader in self.shaders:
                shader.compile()
                gl.glAttachShader(self.id, shader.id)
            
            gl.glLinkProgram(self.id)
            
            message = self._getMessage()
            if not self.getLinkStatus():
                raise LinkError(message)
            
            gl.glUseProgram(self.id)
            
            for i in range(4):
                self.set_uniform('Texture[' + str(i) + ']', i )
                
            return message
        else:
            gl.glUseProgram(self.id)

