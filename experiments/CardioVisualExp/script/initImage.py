from time import time

#components used
self.ecg = self.controller.gModuleList['ecg']
self.imgLeft = self.controller.gModuleList['imgLeft']
self.imgRight = self.controller.gModuleList['imgRight']

#runtime variables left stim
self.onTimeLeft = 0.0
self.stimDurLeft = 0.5
self.stimOnLeft = 0

#runtime variables right stim
self.onTimeRight = 0.0
self.stimDurRight = 0.5
self.stimOnRight = 0