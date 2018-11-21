'''
@author: bh, Tobias Leugger
@since: Summer 2010
'''

from os import path
import pyglet
#from pyglet import media

from abstract.AbstractClasses import BasicModule

class ModuleMain(BasicModule):
    """
    A simple module to play an audio white noise.
    """
    defaultInitConf = {
        'name': 'whitenoise'
    }
    
    defaultRunConf = {
        'volume': 100
    }
    
    confDescription = [
        ('name', 'str', "White Noise"),
        ('volume', 'int', "Volume of audio output in %")
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

        # load audio file
        filename = path.join( path.dirname(__file__),  "WhiteNoise1m.mp3" )
        w = pyglet.media.load( filename )
        if w.audio_format is None:
            raise RuntimeError( "AudioFile module error; the file %s is silent"%filename ) 
        self.audioSource = pyglet.media.Player() 
        self.audioSource.queue( w )
        self.audioSource.eos_action = pyglet.media.Player.EOS_LOOP
        
        # start playing from start
        self.audioSource.volume = 0.0
        
        
    def start(self, dt=0, duration=-1, configName=None):
        """
        Play the file from the beginning
        """
        BasicModule.start(self, dt, duration, configName)
        
        self.audioSource.volume = float(self.activeConf['volume']) / 100.0
        
        self.audioSource.seek(0.0)
        self.audioSource.play()
        
    def stop(self, dt=0):
        """
        Interrupt play 
        """
        BasicModule.stop(self, dt)
        self.audioSource.volume = 0.0
        self.audioSource.pause()

