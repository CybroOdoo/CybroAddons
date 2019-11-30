from struct import pack, unpack
from .zkconst import *


def reverseHex(hexstr):
    tmp = ''
    for i in reversed(range(len(hexstr)/2)):
        tmp += hexstr[i*2:(i*2)+2]
    
    return tmp


def zksettime(self, t):
    """Start a connection with the time clock"""
    command = CMD_SET_TIME
    command_string = pack('I',encode_time(t))
    chksum = 0
    session_id = self.session_id
    reply_id = unpack('HHHH', self.data_recv[:8])[3]

    buf = self.createHeader(command, chksum, session_id,
        reply_id, command_string)
    self.zkclient.sendto(buf, self.address)
    #print buf.encode("hex")
    try:
        self.data_recv, addr = self.zkclient.recvfrom(1024)
        self.session_id = unpack('HHHH', self.data_recv[:8])[2]
        return self.data_recv[8:]
    except:
        return False
    

def zkgettime(self):
    """Start a connection with the time clock"""
    command = CMD_GET_TIME
    command_string = ''
    chksum = 0
    session_id = self.session_id
    reply_id = unpack('HHHH', self.data_recv[:8])[3]

    buf = self.createHeader(command, chksum, session_id,
        reply_id, command_string)
    self.zkclient.sendto(buf, self.address)
    #print buf.encode("hex")
    try:
        self.data_recv, addr = self.zkclient.recvfrom(1024)
        self.session_id = unpack('HHHH', self.data_recv[:8])[2]
        return decode_time( int( reverseHex( self.data_recv[8:].encode("hex") ), 16 ) )
    except:
        return False
