import socket
import sys
import time
import random
import platform


def get_ip_address(ifname):
    if platform.system() == "Linux":
        s = socket(AF_INET, SOCK_DGRAM)
        return inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, # SIOCGIFADDR
                                 pack('256s', ifname[:15]))[20:24])
    else:
        return socket.gethostbyname(socket.gethostname())
    
#######
# SETUP

HOST = get_ip_address("eth0")
PORT = 5555
FREQ = 5
DURATION = 30

######
protocolVocab = { }
protocolVocab["decision"] = 1000         ## Request/Reponse Type





class Sender():
    def __init__(self):
        self.stime = 0    
    
    def start(self):
        self.stime = time.time()
            
    def sendData(self):
        r = 1 - 2*(random.random())
                
        data = str(protocolVocab["decision"]) + ";" + str(r)
        
        # Instead, data is directly sent to the recipient via sendto().
        sock.sendto(data + "\n", (HOST, PORT))
        #received = sock.recv(1024)      #1024 buffer size
        
        #print "Sent:     %s" % data
        #print "Received: %s" % received

    def getSTime(self):
        return self.stime


# SOCK_DGRAM is the socket type to use for UDP sockets
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s = Sender()
s.start()

while time.time() - s.getSTime() < DURATION:
    s.sendData()
    time.sleep(1/FREQ)
