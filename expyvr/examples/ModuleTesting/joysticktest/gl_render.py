glTranslatef(self.x, self.y, -100)
glScalef(1 + self.z, 1 + self.z, 1 + self.z)
glRotatef(-self.angle, 0, 0, 1)
glBegin(GL_TRIANGLES)
glVertex2f(-10, 0)
glVertex2f(0, 13)
glVertex2f(10, 0)
glEnd()

glLoadIdentity()
x = -50
y = -30
glColor3f(0, 1, 1)
glBegin(GL_POINTS)
for button in self.buttons:
	if button:
		glVertex3f(x, y, -100)
	x += 20
glEnd()
