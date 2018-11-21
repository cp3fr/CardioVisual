if self.joystick is None:
	self.joystick = self.controller.gModuleList['joystick'].joystick

self.x = (self.joystick.x) * 10
self.y = (-self.joystick.y) * 10
self.z = self.joystick.z
self.angle = self.joystick.rz * 180
self.buttons = self.joystick.buttons 