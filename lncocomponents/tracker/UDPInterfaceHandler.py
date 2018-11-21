"""
Communication with real-time UDP 

UDP connection sends classification decisions / info

@author : Nathan Evans, Michel Askelrod, Joan Llobera

last udpate: december 2012
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
#protocolVocab = { }

#protocolVocab["decision"] = 1000         ## Request/Reponse Type


#############
# GLOBAL data
UDP = 0
server_thread = 0
server_lock = threading.Lock()
udpPacket = 0
previousPacket = 0
newpacketReceived = False
deviceused = None

class UDPHandler():    

    def __init__(self,uPort,nIface):    
        self.udpPort = uPort
        self.netiface = nIface
    
        self.isopen = False
        self.isstreaming = False
        
        self.connect()
    
    def connect(self):
        #global server_thread, UDP, protocolVocab
        global server_thread, UDP
        
        # disconnect previous connection if already connected
        if self.isopen:
            self.disconnect()
        
        # configure new connection
        try:

            UDP = SocketServer.UDPServer((self.get_ip_address(self.netiface), self.udpPort), PacketHandler)
            print "UDP server started: " + str(UDP)
            
            server_thread = threading.Thread(target=UDP.serve_forever)
            server_thread.setDaemon(True)  

            # send start up message !
            # check for initial response    
            #UDP.socket.settimeout(1.0)
            #response = UDP.socket.recv(18)
    
            #TODO: add check
            #print "First response: " + str(response)
            self.isopen = True
            #sprint "UDP Interface Connected to Localhost Socket"
    
        except error, msg:
            raise RuntimeError("UDP Interface cannot Connect (%s)"%msg)   
    
    
    #def start(self):
    def start(self, configuration):
        
        global server_thread, UDP, deviceused
        deviceused = configuration
        
        if not self.isopen:
            print "UDP Interface cannot start: connect first!"
            return
        server_thread.start()
        self.isstreaming = True
        print "UDP Interface started in thread: ", server_thread.getName()
            
    def stop(self):
        global UDP, isstreaming
        if self.isstreaming:
            #UDP.socket.sendto(msgDataStreamingOff, (UDPServerIP, UDPServerPort))
            self.isstreaming = False
            UDP.shutdown()
            
    def disconnect(self):
        global server_thread, UDP
        if self.isstreaming:
            print "UDP Interface cannot disconnect: stop streaming first!"
            return
        if self.isopen:
            #UDP.socket.sendto(msgStop, (UDPServerIP, UDPServerPort))
            UDP.shutdown()
            self.isopen = False
            print "UDP Interface disconnected"
               
    def getPacket(self):
        global udpPacket
        return udpPacket
        
    def checkPacket(self):
        global newpacketReceived
        return newpacketReceived
    
    def get_ip_address(self,ifname):
        if platform.system() == "Linux":
            s = socket(AF_INET, SOCK_DGRAM)
            return inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, # SIOCGIFADDR
                                     pack('256s', ifname[:15]))[20:24])
        else:
            return gethostbyname(gethostname())



class PacketHandler(SocketServer.DatagramRequestHandler):
    """
    Handle incoming UDP packets
    """   
    
    def handle(self):
        global udpPacket, server_lock, deviceused

        if(deviceused =='two_finger_bot'):  
            d = self.request[0].strip()                
            d = d.split(';')
            data = d[0]
            
            data = int(data)
            #s=d[0]
            #if s.isdigit():
            #    data=int(s)
            #try:
            #    data=float(s)
            #except:
            #    None

            #try:
            #    data =  int((data))  #EXCEPTION!!
            #except: 
            #    print("trouble casting the package received: {0}".format(data))
            
            #print 'data: '
            #print data
        elif(deviceused=='BCI_reader'):                
            d = self.request[0].strip()                
            d = d.split(';')
            mType = int(d[0])
            data = d[1].rstrip('\0')            #remove null bytes at end that matlab loves to send
            data = d[0]
            #print data
                           
        elif(deviceused=='stroke_bot'): 
            print "TODO stroke robot case"
        else: 
            d = self.request[0].strip() 
            d = d.split(';')
            data = str(d)

            
        server_lock.acquire()  
        udpPacket = data
        server_lock.release()
        
        
        
        
        
    # def handle(self):
        # global udpPacket, server_lock, deviceused
        # #data=[]

        # if(deviceused =='two_finger_bot'):                
            # d = self.request[0].strip()                
            # #d = d.split(';')
            # if len(d)>0:
                # data = d[0]
                # data =  int(data)        

        # elif(deviceused=='BCI_reader'):                
            # d = self.request[0].strip()                
            # d = d.split(';')
            # if len(d)>0:
                # mType = int(d[0])
                # data = d[1].rstrip('\0')            #remove null bytes at end that matlab loves to send
                # data = d[0]
                # #print data
                # data =  int(data)                
        # elif(deviceused=='stroke_bot'): 
            # print "TODO stroke robot case"
        # else: 
            # data = self.request[0].strip() 

        # print 'data:'
        # print data
        # server_lock.acquire()  
        # udpPacket = data
        # server_lock.release()
        
        
        #else:
            #print "Unknown type of UDP packet"