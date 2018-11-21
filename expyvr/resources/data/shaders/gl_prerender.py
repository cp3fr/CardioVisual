
# glClearColor(0.2, 0.2, 0.2, 1.0)
# glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
glColor3f(1, 1, 1)
glEnable(GL_DEPTH_TEST)
glEnable(GL_CULL_FACE)

glEnable(GL_BLEND)
#glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


# Simple light setup.
glEnable(GL_LIGHTING)
glEnable(GL_LIGHT0)

glLightfv(GL_LIGHT0, GL_POSITION, vec4f(self.lightPos[0]))
glLightfv(GL_LIGHT0, GL_AMBIENT, vecf(.3, .3, .3, 1))
glLightfv(GL_LIGHT0, GL_DIFFUSE, vecf(.75, .75, .75, 1))
glLightfv(GL_LIGHT0, GL_SPECULAR, vecf(.85, .85, .8, 1))

glLightf(GL_LIGHT0, GL_CONSTANT_ATTENUATION, 0.9)
glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION, 0.005)
glLightf(GL_LIGHT0, GL_QUADRATIC_ATTENUATION, 0.01)

glEnable(GL_LIGHT1)

glLightfv(GL_LIGHT1, GL_POSITION, vec4f(self.lightPos[1]))
glLightfv(GL_LIGHT1, GL_AMBIENT, vecf(.03, .03, .03, 1))
glLightfv(GL_LIGHT1, GL_DIFFUSE, vecf(.5, .5, .5, 1))
glLightfv(GL_LIGHT1, GL_SPECULAR, vecf(.5, .5, .5, 1))

glLightf(GL_LIGHT1, GL_CONSTANT_ATTENUATION, 1.0)
glLightf(GL_LIGHT1, GL_LINEAR_ATTENUATION, 0.05)
glLightf(GL_LIGHT1, GL_QUADRATIC_ATTENUATION, 0.01)