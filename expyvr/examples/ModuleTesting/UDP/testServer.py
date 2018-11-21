import SocketServer
import socket

#######
# SETUP

HOST = "localhost"
PORT = 21566
iface = "eth0"


def get_ip_address(ifname):
    return socket.gethostbyname(socket.gethostname())


class MyUDPHandler(SocketServer.DatagramRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        socket = self.request[1]
        print "%s sent: " %self.client_address[0] + data
        socket.sendto(data.upper(), self.client_address)


print "SERVER STARTING ON PORT " + str(PORT)
server = SocketServer.UDPServer((HOST, PORT), MyUDPHandler)
server.serve_forever()

    
#sock = socket.socket( socket.AF_INET, # Internet
#                      socket.SOCK_DGRAM ) # UDP
#
#sock.bind( (HOST,PORT) )
# 
#while True:
#    data, addr = sock.recvfrom( 1024 ) # buffer size is 1024 bytes
#    print "received message: ", data


#s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#s.bind((HOST, PORT))
#s.listen(1)
#conn, addr = s.accept()
#print 'Connected by', addr
#conn.settimeout(0.2)
#total = 0
#while 1:
#    data = conn.recv(1)
#    total += len(data)
#    print "rx:",len(data)
#    if not data: break
#    conn.close()
#
#print total
