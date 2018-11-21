"""
Communication with IR tracker

Simple UDP reader to grab incoming streamed data

@author : Nathan Evans
"""

from struct import *
from socket import *
import threading
import platform
import SocketServer
import numpy as np

if platform.system() == "Linux":
    import fcntl


#############
# GLOBAL data
camUDP = 0
server_thread = 0
server_lock = threading.Lock()
positions = np.zeros(3)

class IRCamInterface():
    def __init__(self,uPort,nIface):    
        self.udpPort = uPort
        self.netiface = nIface
    
        self.isopen = False
        self.isstreaming = False
        
        self.connect()
    
    def connect(self):
        global server_thread, camUDP, protocolVocab
        
        # disconnect previous connection if already connected
        if self.isopen:
            self.disconnect()
        
        # configure new connection
        try:
            camUDP = SocketServer.UDPServer((self.get_ip_address(self.netiface), self.udpPort), CamUDPHandler)
            print "UDP server starting on port " + str(self.udpPort)
            
            server_thread = threading.Thread(target=camUDP.serve_forever)
            server_thread.setDaemon(True)  

            self.isopen = True
    
        except error, msg:
            raise RuntimeError("IRCam UDP Interface cannot Connect (%s)"%msg)   
    
    
    def start(self):
        global server_thread, camUDP
        if not self.isopen:
            print "IRCam UDP Interface cannot start: connect first!"
            return
        server_thread.start()
        self.isstreaming = True
        print "IRCam UDP Interface started in thread: ", server_thread.getName()
            
    def stop(self):
        global camUDP, isstreaming
        if self.isstreaming:
            self.isstreaming = False
            camUDP.shutdown()
            
    def disconnect(self):
        global server_thread, camUDP
        if self.isstreaming:
            print "IRCam UDP Interface cannot disconnect: stop streaming first!"
            return
        if self.isopen:
            #camUDP.socket.sendto(msgStop, (bciServerIP, bciServerPort))
            camUDP.shutdown()
            self.isopen = False
            print "IRCam UDP Interface disconnected"
               
    def getPositions(self):
        global positions
        return positions
    
    def get_ip_address(self,ifname):
        if platform.system() == "Linux":
            s = socket(AF_INET, SOCK_DGRAM)
            return inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, # SIOCGIFADDR
                                     pack('256s', ifname[:15]))[20:24])
        else:
            return gethostbyname(gethostname())



class CamUDPHandler(SocketServer.DatagramRequestHandler):
    """
    Handle incoming UDP packets (position coordinates)
    """
    def handle(self):
        global positions, server_lock
        d = self.request[0].strip()                
        d = d.split(';')
        print "received UDP message: " + str(d)
        server_lock.acquire()  
        positions[0] = d[0]                                     
        positions[1] = d[1]                 
        positions[2] = 0 #d[2]
        server_lock.release()