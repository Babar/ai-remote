#!/usr/bin/python
import usb
import virtkey
from sys import exit
import gtk
from gtk.gdk import keyval_from_name

class KeyMapper():
    def __init__(self):
        self.map_dic = {}
        self.map_dic2 = {}
        self.v = virtkey.virtkey()
        
    def map(self, remotenr, keycode):
        self.map_dic[remotenr] = keycode
    
    def execute(self, remotenr):
        try:
            #print str(remotenr)+' (pressed) mapped to '+str(self.map_dic[remotenr])
            self.simulate_key(self.map_dic[remotenr])
        except KeyError:
            print str(remotenr)+' (not mapped)'

    def simulate_key(self, keypressed):
        """ simulate the key using python-virtkey
            :param key: sent to keystroke_to_X11
        """
        if type(keypressed) == type(1):
            self.v.press_keycode(keypressed)
            self.v.release_keycode(keypressed)
        else:
            modifiers, key = self.keystroke_to_X11(keypressed)
            if key:
                if modifiers:
                    self.v.lock_mod(modifiers)
                try:
                    self.v.press_keysym(key)
                    self.v.release_keysym(key)
                finally:
                    if modifiers:
                        self.v.unlock_mod(modifiers)
            else:
                    print "Could not decode keycode: "+keypressed
    
    def keystroke_to_X11(self, keystroke):
        """ convert "CTRL+Shift+T" to (1<<2 | 1<<0, 28)
            :param keystroke: The keystroke string.
                             - can handle at least one 'real' key
                             - only ctrl, shift and alt supported yet (case-insensitive)
            :returns: tuple: (modifiers, keysym)
        """
        modifiers = 0
        key = ""
        splitted = keystroke.split("+")
        for stroke in splitted:
            lstroke = stroke.lower()
            if lstroke == "ctrl" or lstroke == "control":
                modifiers |= (1 << 2)
            elif lstroke == "shift":
                modifiers |= (1 << 0)
            elif lstroke == "alt":
                modifiers |= (1 << 3) # TODO: right?
            else: # is a ordinary key (Only one)
                key = gtk.gdk.keyval_from_name(stroke)
        	if not key:
                    print "Could not decode keycode: "+stroke
        return (modifiers, key)

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
# 1
# 6  -  3 - 4
# 12 - 13 - 5
#
#      7
#  8 - 9 - 10
#     11
mapper = KeyMapper()
mapper.map(1,124)   #Power # XF86PowerOff

mapper.map(6,'Alt+Tab')   #Switch window
mapper.map(3,'Left')   #AI gear # 15 s back
mapper.map(4,121)   #Mute - snooze # XF86AudioMute

mapper.map(12,'Shift+Left')  #AP-1 Trigger # 5 s back
mapper.map(13,'Shift+Right')  #AP-2 Trigger # 5 s forward
mapper.map(5,'Right')   #AP Menu # 1 min forward

mapper.map(7,123)   #VolumeUp # XF86AudioRaiseVolume

mapper.map(8,173)   #Previous # XF86AudioPrev
mapper.map(9,172)   #Play/Pause # XF86AudioPlay
mapper.map(10,171)  #Next # XF86AudioNext

mapper.map(11,122)  #VolumeDown # XF86AudioLowerVolume

#we're still there so we open the device
handler = ai.open()

#we know that there is only one configuration
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
