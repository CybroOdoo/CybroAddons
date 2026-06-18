# -*- coding: utf-8 -*-
################################################################################
#
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from struct import pack, unpack
from lxml.builder import unicode
from .zkconst import *

xrange = range


def getSizeUser(self):
    """Checks a returned packet to see if it returned CMD_PREPARE_DATA,
    indicating that data packets are to be sent
    Returns the amount of bytes that are going to be sent"""
    command = unpack('HHHH', self.data_recv[:8])[0]
    if command == CMD_PREPARE_DATA:
        size = unpack('I', self.data_recv[8:12])[0]
        return size
    else:
        return False


def zksetuser(self, uid, userid, name, password, role):
    """Start a connection with the time clock"""
    command = CMD_SET_USER
    command_string = pack(
        'sxs8s28ss7sx8s16s',
        bytes([uid]),
        bytes([role]),
        password.encode() if isinstance(password, str) else password,
        name.encode() if isinstance(name, str) else name,
        bytes([1]),
        b'',
        userid.encode() if isinstance(userid, str) else userid,
        b'',
    )
    chksum = 0
    session_id = self.session_id
    reply_id = unpack('HHHH', self.data_recv[:8])[3]
    buf = self.createHeader(command, chksum, session_id,
                            reply_id, command_string)
    self.zkclient.sendto(buf, self.address)
    try:
        self.data_recv, addr = self.zkclient.recvfrom(1024)
        self.session_id = unpack('HHHH', self.data_recv[:8])[2]
        return self.data_recv[8:]
    except:
        return False


def zkgetuser(self):
    """Start a connection with the time clock"""
    command = CMD_USERTEMP_RRQ
    command_string = '\x05'
    chksum = 0
    session_id = self.session_id
    reply_id = unpack('HHHH', self.data_recv[:8])[3]
    buf = self.createHeader(command, chksum, session_id,
                            reply_id, command_string)
    self.zkclient.sendto(buf, self.address)
    try:
        self.data_recv, addr = self.zkclient.recvfrom(1024)
        if getSizeUser(self):
            bytes = getSizeUser(self)
            while bytes > 0:
                data_recv, addr = self.zkclient.recvfrom(1032)
                self.userdata.append(data_recv)
                bytes -= 1024
            self.session_id = unpack('HHHH', self.data_recv[:8])[2]
            data_recv = self.zkclient.recvfrom(8)
        users = {}
        if len(self.userdata) > 0:
            # The first 4 bytes don't seem to be related to the user
            for x in range(len(self.userdata)):
                if x > 0:
                    self.userdata[x] = self.userdata[x][8:]
            userdata = b''.join(self.userdata)
            userdata = userdata[11:]
            while len(userdata) > 72:
                uid, role, password, name, userid = unpack(
                    '2s2s8s28sx31s', userdata.ljust(72)[:72])
                uid = int(uid.hex(), 16)
                # Clean up some messy characters from the user name
                password = password.split(b'\x00', 1)[0]
                password = unicode(password.strip(b'\x00|\x01\x10x'),
                                   errors='ignore')
                userid = unicode(userid.strip(b'\x00|\x01\x10x'),
                                 errors='ignore')
                name = name.split(b'\x00', 1)[0]
                if name.strip() == b"":
                    name = uid
                users[uid] = (userid, name, int(role.hex(), 16),
                              password)
                userdata = userdata[72:]
        return users
    except:
        return False


def zkclearuser(self):
    """Start a connection with the time clock"""
    command = CMD_CLEAR_DATA
    command_string = ''
    chksum = 0
    session_id = self.session_id
    reply_id = unpack('HHHH', self.data_recv[:8])[3]
    buf = self.createHeader(command, chksum, session_id,
                            reply_id, command_string)
    self.zkclient.sendto(buf, self.address)
    try:
        self.data_recv, addr = self.zkclient.recvfrom(1024)
        self.session_id = unpack('HHHH', self.data_recv[:8])[2]
        return self.data_recv[8:]
    except:
        return False


def zkclearadmin(self):
    """Start a connection with the time clock"""
    command = CMD_CLEAR_ADMIN
    command_string = ''
    chksum = 0
    session_id = self.session_id
    reply_id = unpack('HHHH', self.data_recv[:8])[3]
    buf = self.createHeader(command, chksum, session_id,
                            reply_id, command_string)
    self.zkclient.sendto(buf, self.address)
    try:
        self.data_recv, addr = self.zkclient.recvfrom(1024)
        self.session_id = unpack('HHHH', self.data_recv[:8])[2]
        return self.data_recv[8:]
    except:
        return False
