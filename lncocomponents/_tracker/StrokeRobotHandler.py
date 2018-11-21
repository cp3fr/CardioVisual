"""
Communication device with stroking robot

TCP connection for communication 
UDP connection for data transfer

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
## Mode
protocolVocab["StartData"] = 1000
protocolVocab["StopData"] = 1001



#############
# GLOBAL data
robotUDP = None
tcpClient = None
tcpServer = None
tcpThread = 0
udpThread = 0
server_lock = threading.Lock()
sensorpos = np.zeros(3)
sposhome = np.zeros(3)
firstpos = 1
isstreaming = False


class StrokeRobotHandler():    
    
    def __init__(self,clientIP,tPort,uPort,nIface):
        self.robotServerIP = clientIP
        self.tcpPort = tPort
        self.udpPort = uPort
        self.netiface = nIface
        self.isopen = False
        
        self.connect()
    
    def connect(self):
        """
        Connect to socket, start server threads
        """
        global tcpThread, tcpClient, tcpServer, tcpThread, protocolVocab, robotUDP, udpThread
        
        # disconnect previous connection if already connected
        if self.isopen:
            self.disconnect()
        
        # configure new connection
        try:
            tcpClient = socket(AF_INET, SOCK_STREAM) # Create a socket (SOCK_STREAM means a TCP socket)            
            tcpClient.connect((self.robotServerIP, self.tcpPort))
            print "Connected to TCP server: " + str(tcpClient)
            #TCP Server
#            tcpServer = SocketServer.TCPServer((self.get_ip_address(self.netiface), self.tcpPort), RobotTCPHandler)
#            tcpThread = threading.Thread(target=tcpServer.serve_forever)
#            tcpThread.setDaemon(True)
#            tcpThread.start()
            
            self.isopen = True
    
        except error, msg:
            raise RuntimeError("Stroke Robot Tracker cannot Connect (%s)"%msg)   
    
        if robotUDP is None:
            print "Starting UDP server"
            robotUDP = SocketServer.UDPServer((self.get_ip_address(self.netiface), self.udpPort), RobotUDPHandler)    
            udpThread = threading.Thread(target=robotUDP.serve_forever)
            udpThread.setDaemon(True)
            udpThread.start()
    
        
    def start(self):
        """
        Start data capture -- 
        1) send TCP message to start capture, 
        """
        global	tcpClient, isstreaming, tcpThread
        
        if isstreaming:
            print "Data already streaming, stop first (if you wish to restart stream)"
            return
        
        startMsg = pack("HH",protocolVocab['StartData'],self.tcpPort)
        res = tcpClient.send(startMsg)
        print "SENT MESSAGE: startMsg -- res: " + str(res)
        isstreaming = True
#
#        tcpThread = threading.Thread(target=self.newhandle)
#        tcpThread.setDaemon(True)
#        tcpThread.start()
        
    def newhandle(self):
        global tcpClient
        print "LISTENING FOR INCOMING DATA"
        data = tcpClient.recv(1024)
        print "data: " + str(data)
        string = ""
        i = 0
        while i < 100:
          string = string + data
          data = tcpClient.recv(1024)
          i = i + 1
          
        print string
        
    
    def stop(self):
        """
        Stop data capture -- 
        1) send TCP message to stop capture, 
        2) require confirmation response; 
        """
        global tcpClient, isstreaming
        if isstreaming:
            stopMsg = pack("HH",protocolVocab['StopData'],self.tcpPort)
            res = tcpClient.send(stopMsg)
            print "SENT MESSAGE: stopMsg -- res: " + str(res)
            isstreaming = False
        else:
            print "Data not streaming, start first..."
            return
            
    def disconnect(self):
        global tcpClient, isstreaming, tcpServer, udpThread, robotUDP
        if isstreaming:
            print "Robot Stroker cannot disconnect: stop streaming first!"
            return
        if self.isopen:
            if not tcpClient is None:
                tcpClient.close()
            #if not tcpServer is None:
            #    tcpServer.shutdown()
            if not robotUDP is None:
                robotUDP.shutdown()
            self.isopen = False
            print "Robot Mocap disconnected"
               
    def getAllSensors(self):
        global sensporpos, server_lock
        server_lock.acquire()
        data = sensorpos.copy()
        server_lock.release()

        return data
    
    def get_ip_address(self,ifname):
        if platform.system() == "Linux":
            s = socket(AF_INET, SOCK_DGRAM)
            return inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, # SIOCGIFADDR
                                     pack('256s', ifname[:15]))[20:24])
        else:
            return gethostbyname(gethostname())


#class RobotTCPHandler(SocketServer.DatagramRequestHandler):
#    """
#    Handle incoming TCP packets (position coordinates)
#    """
#    def handle(self):
#        global sensorpos, server_lock
#        data = self.request[0].strip() 
#               
#        fmt = "d" * (len(data) / 8) #Expect 3 doubles        
#        if calcsize(fmt) == len(data) :
#            msg = unpack(fmt , data)    # unpack the packet with the X doubles
#                        
#            sensorpos = np.zeros((3, 1))
#
#            #grab sensor positions
#            server_lock.acquire()
#            sensorpos[0,:] = msg[0]
#            sensorpos[1,:] = msg[1]
#            sensorpos[2,:] = msg[2]
#            server_lock.release()
#            
#        else:
#            print "Incoming TCP packet in wrong format, doing nothing"


class RobotUDPHandler(SocketServer.DatagramRequestHandler):
    """
    Handle incoming UDP packets (position coordinates)
    """
    def handle(self):
        global sensorpos, server_lock, sposhome, firstpos
        data = self.request[0].strip() 
               
        fmt = "d" * (len(data) / 8) #Expect 3 doubles        
        if calcsize(fmt) == len(data) :
            msg = unpack(fmt , data)    # unpack the packet with the X doubles
                        
            sensorpos = np.zeros(3)

            #grab sensor positions
            server_lock.acquire()
            sensorpos[0] = msg[0]
            sensorpos[1] = msg[1]
            sensorpos[2] = msg[2]

            if(firstpos):
                sposhome = sensorpos
                print "sposhome: " + str(sposhome)
                firstpos = 0
                            
            sensorpos = sensorpos - sposhome        #center to home position
            print "sensorpos updated: " + str(sensorpos)
            server_lock.release()
            
        else:
            print "Incoming UDP packet in wrong format, doing nothing"
            
        
