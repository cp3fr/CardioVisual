"""
Savely executes an update of ExpyVR to the latest version from SVN
The latest files are downloaded to the current working directory.
If an installation is already found it is backuped and restored in
case the update fails.

@author: Tobias Leugger
@since: October 2010
"""

import pysvn, os, shutil, time, traceback
from getpass import getpass

# globals where the new version will be installed to and where a backup of the old version will be made
INSTALL_DIR = ""
BACKUP_DIR = ""
epflusername = None
epflpassword = None
loginattempt = 0

def getLogin(realm, username, maySave):
    """
    PySVN callback_get_login handler:
    Asks user for username and password if not already entered
    """
    global epflusername, epflpassword, loginattempt
    if epflusername is None or epflpassword is None:
        print("Username and password of EPFL required (password will not be stored):")
        epflusername = raw_input("Username: ")
        epflpassword = getpass()
    loginattempt += 1
    return loginattempt < 2, epflusername, epflpassword, False


def sslServerTrustPrompt(trustDict):
    """
    PySVN callback_ssl_server_trust_prompt handler:
    Blindly accepts all server certificates
    """
    print("Accepting certificate from %s with fingerprint %s." % (trustDict['hostname'], trustDict['finger_print']))
    return True, 0, False


def progressOutput(eventDict):
    """
    PySVN callback_notify handler:
    Prints the file name if the event is an 'update_add' event
    """
    if eventDict['action'] == pysvn.wc_notify_action.update_add:
        print("Downloading %s."%eventDict['path'].decode('utf-8'))

  
def update(svnclient, REPO_URL, DIR_NAME, deleteBackups):
    """
    Executes the update of ExpyVR to the latest version from SVN
    It is assumed that the cwd is the one where the trunk is located.
    """
    global INSTALL_DIR, BACKUP_DIR
    DIR_NAME = unicode(DIR_NAME)
    INSTALL_DIR = unicode(os.path.join(os.getcwdu(), DIR_NAME))
    BACKUP_DIR = unicode(os.path.join(os.getcwdu(), DIR_NAME + '-backup-' + time.strftime("%Y-%m-%d-%H-%M-%S")))
        
    # Make backup of current install if there is one
    if os.path.isdir(BACKUP_DIR):
        # Make sure a folder with that name doesn't already exist
        shutil.rmtree(BACKUP_DIR)
    if os.path.isdir(INSTALL_DIR):
        print("Making backup of current install")
        os.rename(INSTALL_DIR, BACKUP_DIR)

    # Export the latest version
    print("Downloading new files:")
    r = svnclient.export(REPO_URL, INSTALL_DIR)
    print("Finished downloading %s (revision %d)"%(DIR_NAME, r.number))
    f = open( os.path.join(INSTALL_DIR, 'VERSION.txt'), 'w' )
    f.write("Revision %d"%(r.number) )
    f.close()
    
    # if old backups should be deleted
    if deleteBackups.lower() != 'y':
        print("Cleaning up:")
        for dir in os.listdir(os.getcwd()):
            # Go through all dirs and remove the ones looking like backups
            if dir.startswith(DIR_NAME + '-backup-'):
                print("Removing '%s'" % dir)
                shutil.rmtree(dir)


def handleException():
    """
    Handles any exception occuring during the update
    by saving the traceback to file and restoring the
    last install from the backup if needed
    """
    global INSTALL_DIR, BACKUP_DIR, loginattempt
    cleanup = True
    # invalid login error ; Not really an error
    if loginattempt > 1:
        if INSTALL_DIR.count('lncocomponents'):
            cleanup=False
            raw_input("Update of expyvr successfully finished. \n\nPress Enter key to terminate.")
        else:
            print("Invalid username or password. \n")
    # other cases ; really an error
    else:
        # Store the last exception to file
        path = unicode(os.path.join(os.getcwd(), 'updateError.log'))
        f = open(path, 'a')
        f.write('\nTime: %s:\n' % time.strftime("%d %b %Y %H:%M:%S"))
        traceback.print_exc(file=f)
        f.close()
        # Print error message
        print("An error occured (did you close ExpyVR before running update?). \nDetails where stored in '%s'" % path)
        
    if cleanup:
        # See if we need to restore a previous backup
        print("Restoring previous installation.")
        if os.path.isdir(BACKUP_DIR):
            # We already made the backup, copy it back to the install directory
            if os.path.isdir(INSTALL_DIR):
                # New version already partially downloaded, delete it
                shutil.rmtree(INSTALL_DIR)
            os.rename(BACKUP_DIR, INSTALL_DIR)
        raw_input("\nUpdate aborted. \n\nPress Enter key to terminate.")

if __name__ == '__main__':        
    try:
        # Ask if update should really be executed
        print("=================================")    
        print("==      EPFL LNCO ExpyVR       ==")    
        print("=================================")    
        print("")
        print("This script will update ExpyVR to the latest version in '%s'."%os.getcwdu() )  
        print("To get information about how to obtain EPFL credential, visit http://lnco.epfl.ch/expyvr")
        print("")
        print("Please close all ExpyVR programs before continuing." )    
        start = raw_input("Proceed with update? [y/N]: ")
        if start.lower() != 'y':
            raw_input("\nAborting update. Press Enter key to terminate.")
        else:
            # Ask if old backups should be deleted
            deleteBackups = raw_input("Keep a backup copy ? [y/N]: ")
        
            # Set up the svn client
            client = pysvn.Client()
            client.callback_get_login = getLogin
            client.callback_ssl_server_trust_prompt = sslServerTrustPrompt
            client.callback_notify = progressOutput
        
            # do updates
            update(client, 'https://svn.epfl.ch/svn/expyvr/trunk', 'expyvr', deleteBackups)
            update(client, 'https://svn.epfl.ch/svn/lncocomponents/trunk', 'lncocomponents', deleteBackups)
       
            raw_input("\nUpdate of expyvr and lncocomponents successfully finished. \n\nPress Enter key to terminate.")
    except:
        # TODO: handle some exceptions from svn export better (like no connection, no password provided)
        handleException()
