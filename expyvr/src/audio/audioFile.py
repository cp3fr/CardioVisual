'''
@author: bh, Tobias Leugger
@since: Summer 2010
'''
import os, pyglet

from abstract.AbstractClasses import BasicModule
from controller import getPathFromString

class ModuleMain(BasicModule):
    """
    A simple module to play sound files. Supported audio formats are:
        AU
        MP2
        MP3
        OGG/Vorbis
        WAV
        WMA
    """
    defaultInitConf = {
        'name': 'audioFile'
    }
    
    defaultRunConf = {
        'filename': 'audio_file_name.wav',
        'loop': True,
        'volume': 100
    }
    
    confDescription = [
        ('name', 'str', "Module playing an audio file"),
        ('filename', 'str', "Full path and filename of the audio to play (.wav, .mp3, .mp2, .ogg, .wma)"),
        ('loop', 'bool', "Loop playback"),
        ('volume', 'int', "Volume of audio output in %"),
        ('replay()', 'info', "Plays the sound again.")
    ]
    
    has_avbin = False
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        BasicModule.__init__(self, controller, initConfig, runConfigs)

        if not ModuleMain.has_avbin: 
            try:
                from pyglet.media import avbin
                ModuleMain.has_avbin = True
                self.log("Using avbin library version %d"%avbin.get_version())
            except ImportError as e:
                raise RuntimeError("AudioFile module error; %s"%str(e))    


        self.audioSource = {}
        # create a media player for each audio file
        for conf in self.runConfs.values():
            fileName = conf['filename']
            if fileName in self.audioSource:
                # We've already loaded that file
                continue
            self.audioSource[fileName] = pyglet.media.Player() 
            w = pyglet.media.load( getPathFromString(fileName) )
            if w.audio_format is None:
                raise RuntimeError( "AudioFile module error; the file %s is silent"%fileName ) 
            self.audioSource[fileName].queue( w )
            self.audioSource[fileName].seek( w.duration )
        
    def start(self, dt=0, duration=-1, configName=None):
        """
        Play the file from the beginning
        """
        BasicModule.start(self, dt, duration, configName)
        
        # adjust parameters of the player to the config
        if self.activeConf['loop']:
            self.audioSource[self.activeConf['filename']].eos_action = pyglet.media.Player.EOS_LOOP
        else:
            self.audioSource[self.activeConf['filename']].eos_action = pyglet.media.Player.EOS_PAUSE 
        self.audioSource[self.activeConf['filename']].volume = float(self.activeConf['volume']) / 100.0
        
        # start playing from start
        self.audioSource[self.activeConf['filename']].seek(0.0)
        self.audioSource[self.activeConf['filename']].play()
        
    def stop(self, dt=0):
        """
        Interrupt play 
        """
        BasicModule.stop(self, dt)
        self.audioSource[self.activeConf['filename']].pause()     

    def replay(self):
        self.audioSource[self.activeConf['filename']].eos_action = pyglet.media.Player.EOS_PAUSE 
        self.audioSource[self.activeConf['filename']].seek(0.0)
        self.audioSource[self.activeConf['filename']].play()
