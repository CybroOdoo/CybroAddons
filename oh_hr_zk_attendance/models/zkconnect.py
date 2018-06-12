# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: cybrosys(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################
from struct import pack, unpack
from .zkconst import *


def zkconnect(self):
    """Start a connection with the time clock"""
    command = CMD_CONNECT
    command_string = ''
    chksum = 0
    session_id = 0
    reply_id = -1 + USHRT_MAX

    buf = self.createHeader(command, chksum, session_id,
        reply_id, command_string)
    
    self.zkclient.sendto(buf, self.address)
    
    try:
        self.data_recv, addr = self.zkclient.recvfrom(1024)
        self.session_id = unpack('HHHH', self.data_recv[:8])[2]
        
        return self.checkValid( self.data_recv )
    except:
        return False
    

def zkdisconnect(self):
    """Disconnect from the clock"""
    command = CMD_EXIT
    command_string = ''
    chksum = 0
    session_id = self.session_id
    
    reply_id = unpack('HHHH', self.data_recv[:8])[3]
    
    buf = self.createHeader(command, chksum, session_id,
        reply_id, command_string)

    self.zkclient.sendto(buf, self.address)
    
    self.data_recv, addr = self.zkclient.recvfrom(1024)
    return self.checkValid( self.data_recv )
    
