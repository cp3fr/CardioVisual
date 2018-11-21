#local variable retrieving self.lastvalue from udp_handler: [ip, 'p(0.0, 0.0)']
package = self.udp.getData()
#if valid package received
if len(package)==2:
    #extract string message
    msg = package[1]
    #if non-empty message, push to tobii module
    if len(msg)>0:
        self.tobii.inputMsg = msg


