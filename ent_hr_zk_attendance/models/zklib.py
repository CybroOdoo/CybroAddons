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
from socket import *
from .zkconnect import *
from .zkversion import *
from .zkos import *
from .zkextendfmt import *
from .zkextendoplog import *
from .zkplatform import *
from .zkworkcode import *
from .zkssr import *
from .zkpin import *
from .zkface import *
from .zkserialnumber import *
from .zkdevice import *
from .zkuser import *
from .zkattendance import *
from .zktime import *


class ZKLib:

    def __init__(self, ip, port):
        """Initialize the UDP client and device connection state."""
        self.address = (ip, port)
        self.zkclient = socket(AF_INET, SOCK_DGRAM)
        self.zkclient.settimeout(3)
        self.session_id = 0
        self.userdata = []
        self.attendancedata = []

    def createChkSum(self, p):
        """This function calculates the chksum of the packet to be sent to the 
        time clock
        Copied from zkemsdk.c"""
        length = len(p)
        chksum = 0
        while length > 1:
            chksum += unpack('H', pack('BB', p[0], p[1]))[0]

            p = p[2:]
            if chksum > USHRT_MAX:
                chksum -= USHRT_MAX
            length -= 2

        if length:
            chksum = chksum + p[-1]

        while chksum > USHRT_MAX:
            chksum -= USHRT_MAX

        chksum = ~chksum

        while chksum < 0:
            chksum += USHRT_MAX

        return pack('H', chksum)

    def createHeader(self, command, chksum, session_id, reply_id,
                     command_string):
        """This function puts a parts that make up a packet together and
        packs them into a byte string"""
        command_bytes = command_string if isinstance(command_string, bytes) else command_string.encode(
            encoding='utf_8', errors='strict'
        )
        buf = pack('HHHH', command, chksum, session_id, reply_id) + command_bytes
        buf = unpack('8B' + '%sB' % len(command_bytes), buf)
        chksum = unpack('H', self.createChkSum(buf))[0]
        reply_id += 1
        if reply_id >= USHRT_MAX:
            reply_id -= USHRT_MAX
        buf = pack('HHHH', command, chksum, session_id, reply_id)
        return buf + command_bytes

    def checkValid(self, reply):
        """Checks a returned packet to see if it returned CMD_ACK_OK,
        indicating success"""
        command = unpack('HHHH', reply[:8])[0]
        if command == CMD_ACK_OK:
            return True
        else:
            return False

    def connect(self):
        """Connect to the biometric device."""
        return zkconnect(self)

    def disconnect(self):
        """Disconnect from the biometric device."""
        return zkdisconnect(self)

    def version(self):
        """Return the device firmware version."""
        return zkversion(self)

    def osversion(self):
        """Return the device operating system version."""
        return zkos(self)

    def extendFormat(self):
        """Request the device extended format information."""
        return zkextendfmt(self)

    def extendOPLog(self, index=0):
        """Request extended operation log information from the device."""
        return zkextendoplog(self, index)

    def platform(self):
        """Return the device platform information."""
        return zkplatform(self)

    def fmVersion(self):
        """Return the device platform firmware version."""
        return zkplatformVersion(self)

    def workCode(self):
        """Return the device work code information."""
        return zkworkcode(self)

    def ssr(self):
        """Return the device SSR information."""
        return zkssr(self)

    def pinWidth(self):
        """Return the configured PIN width from the device."""
        return zkpinwidth(self)

    def faceFunctionOn(self):
        """Return whether face recognition is enabled on the device."""
        return zkfaceon(self)

    def serialNumber(self):
        """Return the device serial number."""
        return zkserialnumber(self)

    def deviceName(self):
        """Return the biometric device name."""
        return zkdevicename(self)

    def disableDevice(self):
        """Disable the biometric device for maintenance operations."""
        return zkdisabledevice(self)

    def enableDevice(self):
        """Enable the biometric device after maintenance operations."""
        return zkenabledevice(self)

    def getUser(self):
        """Fetch users stored on the biometric device."""
        return zkgetuser(self)

    def setUser(self, uid, userid, name, password, role):
        """Create or update a user on the biometric device."""
        return zksetuser(self, uid, userid, name, password, role)

    def clearUser(self):
        """Remove users from the biometric device."""
        return zkclearuser(self)

    def clearAdmin(self):
        """Clear administrator privileges on the biometric device."""
        return zkclearadmin(self)

    def getAttendance(self):
        """Fetch attendance logs from the biometric device."""
        return zkgetattendance(self)

    def clearAttendance(self):
        """Clear attendance logs from the biometric device."""
        return zkclearattendance(self)

    def setTime(self, t):
        """Set the biometric device time."""
        return zksettime(self, t)

    def getTime(self):
        """Return the biometric device time."""
        return zkgettime(self)
