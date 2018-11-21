"""
Ascension Tech Reactor Motion capture device driver
Implementation of the UDP connection with FusionCORE v1.2.0.614 Packet Format

@author : Bruno.Herbelin@epfl.ch

Example usage :
import ReactorHandler as mocap
mocap.connect("172.16.222.128", 6001, "vmnet8")
mocap.start()
[..]
sensordata = mocap.getAllSensors()
for s in sensordata:
    (x,y,z) = sensordata[s]
    [.. do something with x,y,z ..]
[..]
mocap.stop()
mocap.disconnect()#from socket import *
"""
from struct import *
from socket import *
import threading
import platform, time
if platform.system() == "Linux":
    import fcntl
import numpy as np
import SocketServer

reactorVocabulary = { }
## Mode
reactorVocabulary["m_Request"] = 1000         ## Request/Reponse Type
reactorVocabulary["m_Sending"] = 1001         ## Send Information Packet (data/marker/etc)
## Types
reactorVocabulary["m_ReqClose"] = 1010        ## Request Close Connection
reactorVocabulary["m_ReqMarkerInfo"] = 1011   ## Request Marker Info
reactorVocabulary["m_ReqData"] = 1012         ## Request Data Tansmit
reactorVocabulary["m_ReqNoData"] = 1013       ## Request Data Stop Transmit
reactorVocabulary["m_ReqStartCap"] = 1014     ## Request Start Capture
reactorVocabulary["m_ReqStopCap"] = 1015      ## Request Stop Capture
reactorVocabulary["m_ReqConnect"] = 1017      ## Request Connection
reactorVocabulary["m_ReqConnectAck"] = 1018   ## Respond Acknowledge of connection      
reactorVocabulary["m_ReqIsAlive"] = 1019      ## Request Are Still Alive
reactorVocabulary["m_ReqIsAliveAck"] = 1120   ## Respond Are Still Alive Ack!
reactorVocabulary["m_ReqStatus"] = 1121       ## Request Status
reactorVocabulary["m_SendMarkerInfo"] = 1020  ## Sending Marker Info
reactorVocabulary["m_SendData"] = 1021        ## Sending Data Packet
reactorVocabulary["m_SendStatus"] = 1023      ## Sending Status
reactorVocabulary["m_ReqUnknown"] = 1099      ## Error/Unknown Command
## Format
reactorVocabulary["m_FormatHV"] = 1100        ## HyperVision Packet Format
## Computer Type
reactorVocabulary["m_CompMocap"] = 1201       ## Capturer!
reactorVocabulary["m_CompViewer"] = 1202      ## Client : Viewer
reactorVocabulary["m_CompFilmBox"] = 1203     ## Client : Filmbox
reactorVocabulary["m_CompCustom"] = 1204      ## Client : Custom

## utility protocol methods  
def get_ip_address(ifname):
    if platform.system() == "Linux":
        s = socket(AF_INET, SOCK_DGRAM)
        return inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, # SIOCGIFADDR
                                     pack('256s', ifname[:15]))[20:24])
    elif platform.system() == "Windows":
        return gethostbyname(gethostname())
  
def Format_RequestPkt(nReqType):
    msg = pack("hhhhhhhhh", reactorVocabulary["m_Request"], reactorVocabulary[nReqType], reactorVocabulary["m_FormatHV"],
                   0,0,0,0, reactorVocabulary["m_CompCustom"], 0  )
    return msg

def Read_Pkt_Type(packet):
    msg = unpack("hhhhhhhhh", packet)
    return msg[1]


class MocapUDPHandler(SocketServer.DatagramRequestHandler):
    """
    The packet handler class
    """
    def handle(self):
        global sensorpos, sensortime, server_lock
        data = self.request[0].strip()
        fmt = "h" * (len(data) / 2)
        
        if calcsize(fmt) == len(data) :
            # unpack the packet with as many 'h' as SHORT values we got
            msg = unpack(fmt , data)
            
            if msg[1] == reactorVocabulary["m_SendData"]:
            
                # we got a data packet ; how many sensors ?
                nbsensors = msg[9]
                server_lock.acquire()
                # compute time from seconds and mili-seconds
                sensortime = float(msg[10]) + (float(msg[11]) / 1000.0)
                # for every trio of XYZ coordinate, for each sensor 
                s = 0
                
                imax = 12 + 3 * nbsensors
                
                #the sensorpos is a matrix whose columns are the
                #3D-coordinates of the mocap sensors
                if len(msg) >= imax :
                
                    sensorpos = np.zeros((3, nbsensors))
                    
                    for index in range(12, 12 + 3 * nbsensors, 3):
                        sensorpos[0, s] = float(msg[index]) / 1000.0
                        sensorpos[1, s] = float(msg[index + 1]) / 1000.0
                        sensorpos[2, s] = float(msg[index + 2]) / 1000.0
                        s += 1
                    
                server_lock.release()
                


def connect(serverIP, serverPORT, interface):
    global server_thread, fusioncoreUDP, isstreaming, isopen, fusioncoreServerIP, fusioncoreServerPort, msgStartUp, reactorVocabulary, msgDataStreamingOff, msgCaptureOff
    # disconnect previous connection if already connected
    if isopen or fusioncoreUDP is not None:
        disconnect()
    # configure new connection
    fusioncoreServerIP = serverIP
    fusioncoreServerPort = serverPORT
    netiface = interface
    try:
        fusioncoreUDP = SocketServer.UDPServer((get_ip_address(netiface), 0), MocapUDPHandler)
        server_thread = threading.Thread(target=fusioncoreUDP.serve_forever)
        server_thread.setDaemon(True)
        
        fusioncoreUDP.socket.settimeout(1.0)
        fusioncoreUDP.socket.connect((fusioncoreServerIP, fusioncoreServerPort))
        fusioncoreUDP.socket.sendall(msgStartUp)
        # check server response
        response = fusioncoreUDP.socket.recv(18)
        if Read_Pkt_Type(response) == reactorVocabulary["m_ReqConnectAck"]:
            print "Reactor Mocap Connected to", fusioncoreServerIP
            isopen = True
            
    except error, msg:
        raise RuntimeError("Reactor Mocap cannot Connect (%s)"%msg)   
    
    
def start():
    global  fusioncoreUDP, isstreaming, isopen, msgDataStreamingOn
    if not isopen:
        print "Reactor Mocap cannot start: connect first!"
        return
    
    fusioncoreUDP.socket.sendall(msgDataStreamingOn)
    isstreaming = True
    print "Reactor Mocap started "
  
  
def startCapture():
    global  fusioncoreUDP, isopen, msgCaptureOn, server_thread
    if not isopen:
        print "Reactor Mocap cannot start capture: connect first!"
        return
    server_thread.start()
    fusioncoreUDP.socket.sendall(msgCaptureOn)
    print "Reactor Mocap requested Capture to start"
  
  
def stopCapture():
    global  isopen, fusioncoreUDP, msgCaptureOff
    if not isopen:
        print "Reactor Mocap cannot stop capture: connect first!"
        return
    fusioncoreUDP.shutdown()
    time.sleep(0.1)
    print Read_Pkt_Type(msgCaptureOff)
    fusioncoreUDP.socket.sendall(msgCaptureOff)
    print "Reactor Mocap requested capture to stop"


def stop():
    global fusioncoreUDP, isstreaming, msgDataStreamingOff
    if isstreaming:
        fusioncoreUDP.socket.sendall(msgDataStreamingOff)
        isstreaming = False
        print "Reactor Mocap stopped"
    
def disconnect():
    global isstreaming, isopen, fusioncoreUDP, msgStop
    if isstreaming:
        stop()
    if isopen:
        fusioncoreUDP.socket.sendall(msgStop)
        isopen = False
        fusioncoreUDP.socket.close()
        print "Reactor Mocap disconnected"
    del fusioncoreUDP
    fusioncoreUDP = None
   
def getAllSensors():
    server_lock.acquire()
    data = sensorpos.copy()
    #time = sensortime
    server_lock.release()
    return data


# GLOBAL data
fusioncoreUDP = None
server_thread = 0
server_lock = threading.Lock()
sensorpos = np.zeros((0, 0))
sensortime = 0.0
isopen = False
isstreaming = False
fusioncoreServerIP = "192.168.0.7"
fusioncoreServerPort = 6001
netiface = "eth0"

# create a set of messages for later use during communication with fusion Core server
msgStartUp = Format_RequestPkt("m_ReqConnect")
msgDataStreamingOn = Format_RequestPkt("m_ReqData")
msgDataStreamingOff = Format_RequestPkt("m_ReqNoData")
msgStop = Format_RequestPkt("m_ReqClose") 
msgCaptureOn = Format_RequestPkt("m_ReqStartCap")
msgCaptureOff = Format_RequestPkt("m_ReqStopCap")

