"""
Communication with real-time BCI 

UDP connection sends classification decisions / info

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

########
# Protocol Vocabulary for TCP
protocolVocab = { }

protocolVocab["decision"] = 1000         ## Request/Reponse Type


#############
# GLOBAL data
bciUDP = 0
server_thread = 0
server_lock = threading.Lock()
classDecision = 0

class BCIHandler():    
    
    def __init__(self,uPort,nIface):    
        self.udpPort = uPort
        self.netiface = nIface
    
        self.isopen = False
        self.isstreaming = False
        
        self.connect()
    
    def connect(self):
        global server_thread, bciUDP, protocolVocab
        
        # disconnect previous connection if already connected
        if self.isopen:
            self.disconnect()
        
        # configure new connection
        try:

            bciUDP = SocketServer.UDPServer((self.get_ip_address(self.netiface), self.udpPort), BCIUDPHandler)
            print "UDP server started: " + str(bciUDP)
            
            server_thread = threading.Thread(target=bciUDP.serve_forever)
            server_thread.setDaemon(True)  

            # send start up message !
            # check for initial response    
            #bciUDP.socket.settimeout(1.0)
            #response = bciUDP.socket.recv(18)
    
            #TODO: add check
            #print "First response: " + str(response)
            self.isopen = True
            #sprint "BCI Interface Connected to Localhost Socket"
    
        except error, msg:
            raise RuntimeError("BCI Interface cannot Connect (%s)"%msg)   
    
    
    def start(self):
        global server_thread, bciUDP
        if not self.isopen:
            print "BCI Interface cannot start: connect first!"
            return
        server_thread.start()
        self.isstreaming = True
        print "BCI Interface started in thread: ", server_thread.getName()
            
    def stop(self):
        global bciUDP, isstreaming
        if self.isstreaming:
            #bciUDP.socket.sendto(msgDataStreamingOff, (bciServerIP, bciServerPort))
            self.isstreaming = False
            bciUDP.shutdown()
            
    def disconnect(self):
        global server_thread, bciUDP
        if self.isstreaming:
            print "BCI Interface cannot disconnect: stop streaming first!"
            return
        if self.isopen:
            #bciUDP.socket.sendto(msgStop, (bciServerIP, bciServerPort))
            bciUDP.shutdown()
            self.isopen = False
            print "BCI Interface disconnected"
               
    def getDecision(self):
        global classDecision
        return classDecision
    
    def get_ip_address(self,ifname):
        if platform.system() == "Linux":
            s = socket(AF_INET, SOCK_DGRAM)
            return inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, # SIOCGIFADDR
                                     pack('256s', ifname[:15]))[20:24])
        else:
            return gethostbyname(gethostname())



class BCIUDPHandler(SocketServer.DatagramRequestHandler):
    """
    Handle incoming UDP packets (position coordinates)
    """
    def handle(self):
        global classDecision, server_lock
        d = self.request[0].strip()                
        d = d.split(';')
        mType = int(d[0])
        data = d[1].rstrip('\0')            #remove null bytes at end that matlab loves to send

        if mType == protocolVocab["decision"]:
            server_lock.acquire()  
            classDecision = float(data)
            server_lock.release()
        else:
            print "Unknown type of UDP packet"