# This specifies defaults for the psychopy prefs
# A prefsSite.cfg will be created from it when psychopy is first run
# these settings can be over-ridden in a platform-dependent way
# e.g., prefsDarwin.cfg makes PsychpoPy feel more Mac-like by default
# users can then further customize their prefs by editing the user prefs page within PsychoPy

# each line should have a default= ___, and it should appear as the last item on the line

### General settings
[general]
    largeIcons = boolean(default='True')
    reloadPrevExp = boolean(default=False)
    # for the user to add custom components (comma-separated list)
    componentsFolders = list(default=list('/Users/Shared/ExpyVR/components'))
    # a list of components to hide (eg, because you never use them)
    hiddenComponents = list(default=list())

[keyBindings]
    # File:
    open = string(default='Ctrl+O')
    new = string(default='Ctrl+N')
    save = string(default='Ctrl+S')
    saveAs = string(default='Ctrl+Shift+S')
    close = string(default='Ctrl+W')
    quit = string(default='Ctrl+Q')

    # Edit:
    undo = string(default='Ctrl+Z')
    redo = string(default='Ctrl+Shift+Z')
    
    # Experiment
	testExperiment = string(default='Ctrl+T')
	rerunInstance = string(default='Ctrl+R')