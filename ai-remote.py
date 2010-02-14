#!/etc/bin/python
import usb
import virtkey
from sys import exit

class KeyMapper():
    def __init__(self):
        self.map_dic = {}
        self.map_dic2 = {}
        self.v = virtkey.virtkey()
        
    def map(self, remotenr, keycode):
        self.map_dic[remotenr] = keycode
    
    def execute(self, remotenr):
        try:
            self.v.press_keycode(self.map_dic[remotenr])
            self.v.release_keycode(self.map_dic[remotenr])
        except KeyError:
            print str(remotenr)+' (not mapped)'

#what busses are availible?
busses = usb.busses()

ai = None

#we only need the ASUS Ai Remote
while not ai:
    for bus in busses:
        for dev in bus.devices:
            if dev.idVendor == 0x0b05 and dev.idProduct == 0x172e:
                print 'ASUS Ai Remote found.'
                ai = dev
        
#if the remote isn't found - exit
if not ai:
    print 'No Device found!'
    exit()

#If we want our RC to to something, we should map its keys.
mapper = KeyMapper()
mapper.map(4,121)   #Mute
mapper.map(7,123)   #VolumeUp
mapper.map(8,173)   #Previous
mapper.map(9,172)   #Play/Pause
mapper.map(10,171)  #Next
mapper.map(11,122)  #VolumeDown

#we're still there so we open the device
handler = ai.open()

#we know that there is only one confoguration
conf = ai.configurations[0]
#only one interface
iface = conf.interfaces[0][0]
#only one endpoint
endp = iface.endpoints[0]

#we don't want the kernel to handle this device
try:
    handler.detachKernelDriver(iface)
except usb.USBError, e:
    print e.args[0]
    if e.args != ('could not detach kernel driver from interface 0: No data available',):
        raise e

#the try...except statement in the next loop is due to a pyusb bug, that raises
#an error ('USBError: no error') where there is none.
while True:
    data = (2,0,0,0,0,0,0,0)
    try:
        data = handler.interruptRead(endp.address, endp.maxPacketSize,10)
    except usb.USBError, e:
        if e.args != ('No error',) and e.args != ('could not detach kernel driver from interface 0: No data available',): # http://bugs.debian.org/476796
            raise e
    
    if data[1] != 0:
        mapper.execute(data[1])
    if data[1] == 4:
        break 