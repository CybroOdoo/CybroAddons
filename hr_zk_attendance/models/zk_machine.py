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
import pytz
import sys
import datetime
import logging
import binascii

from . import zklib
from .zkconst import *
from struct import unpack
from odoo import api, fields, models
from odoo import _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    device_id = fields.Char(string='Biometric Device ID')


class ZkMachine(models.Model):
    _name = 'zk.machine'
    
    name = fields.Char(string='Machine IP', required=True)
    port_no = fields.Integer(string='Port No', required=True)
    address_id = fields.Many2one('res.partner', string='Working Address')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id)

    @api.multi
    def device_connect(self, zk):
        command = CMD_CONNECT
        command_string = ''
        chksum = 0
        session_id = 0
        reply_id = -1 + USHRT_MAX
        buf = zk.createHeader(command, chksum, session_id,
                              reply_id, command_string)
        zk.zkclient.sendto(buf, zk.address)
        try:
            zk.data_recv, addr = zk.zkclient.recvfrom(1024)
            zk.session_id = unpack('HHHH', zk.data_recv[:8])[2]
            command = unpack('HHHH', zk.data_recv[:8])[0]
            if command == 2005:
                conn = True
            else:
                conn = False
        except:
            conn = False
        return conn
    
    @api.multi
    def clear_attendance(self):
        for info in self:
            try:
                machine_ip = info.name
                port = info.port_no
                zk = zklib.ZKLib(machine_ip, port)
                conn = self.device_connect(zk)
                if conn:
                    zk.enableDevice()
                    clear_data = zk.getAttendance()
                    if clear_data:
                        zk.clearAttendance()
                        self._cr.execute("""delete from zk_machine_attendance""")
                    else:
                        raise UserError(_('Unable to get the attendance log, please try again later.'))
                else:
                    raise UserError(_('Unable to connect, please check the parameters and network connections.'))
            except:
                raise ValidationError('Warning !!! Machine is not connected')

    def getSizeUser(self, zk):
        """Checks a returned packet to see if it returned CMD_PREPARE_DATA,
        indicating that data packets are to be sent

        Returns the amount of bytes that are going to be sent"""
        command = unpack('HHHH', zk.data_recv[:8])[0]
        if command == CMD_PREPARE_DATA:
            size = unpack('I', zk.data_recv[8:12])[0]
            return size
        else:
            return False

    def zkgetuser(self, zk):
        """Start a connection with the time clock"""
        command = CMD_USERTEMP_RRQ
        command_string = '\x05'
        chksum = 0
        session_id = zk.session_id
        reply_id = unpack('HHHH', zk.data_recv[:8])[3]

        buf = zk.createHeader(command, chksum, session_id, reply_id, command_string)
        zk.zkclient.sendto(buf, zk.address)
        try:
            zk.data_recv, addr = zk.zkclient.recvfrom(1024)

            if self.getSizeUser(zk):
                bytes = self.getSizeUser(zk)

                while bytes > 0:
                    data_recv, addr = zk.zkclient.recvfrom(1032)
                    zk.userdata.append(data_recv)
                    bytes -= 1024

                zk.session_id = unpack('HHHH', zk.data_recv[:8])[2]
                data_recv = zk.zkclient.recvfrom(8)

            users = {}
            if len(zk.userdata) > 0:
                for x in range(len(zk.userdata)):
                    if x > 0:
                        zk.userdata[x] = zk.userdata[x][8:]
                userdata = b''.join(zk.userdata)
                userdata = userdata[11:]
                while len(userdata) > 72:
                    uid, role, password, name, userid = unpack('2s2s8s28sx31s', userdata.ljust(72)[:72])
                    uid = int(binascii.hexlify(uid), 16)
                    # Clean up some messy characters from the user name
                    password = password.split(b'\x00', 1)[0]
                    password = str(password.strip(b'\x00|\x01\x10x|\x000').decode('utf-8'))
                    # uid = uid.split('\x00', 1)[0]
                    userid = str(userid.strip(b'\x00|\x01\x10x|\x000|\x9aC').decode('utf-8'))
                    name = name.split(b'\x00', 1)[0].decode('utf-8')
                    if name.strip() == "":
                        name = uid
                    users[uid] = (userid, name, int(binascii.hexlify(role), 16), password)
                    userdata = userdata[72:]
            return users
        except:
            return False

    @api.model
    def cron_download(self):
        machines = self.env['zk.machine'].search([])
        for machine in machines :
            machine.download_attendance()
        
    @api.multi
    def download_attendance(self):
        _logger.info("++++++++++++Cron Executed++++++++++++++++++++++")
        zk_attendance = self.env['zk.machine.attendance']
        att_obj = self.env['hr.attendance']
        for info in self:
            machine_ip = info.name
            port = info.port_no
            zk = zklib.ZKLib(machine_ip, port)
            conn = self.device_connect(zk)
            if conn:
                zk.enableDevice()
                user = self.zkgetuser(zk)
                command = CMD_ATTLOG_RRQ
                command_string = ''
                chksum = 0
                session_id = zk.session_id
                reply_id = unpack('HHHH', zk.data_recv[:8])[3]
                buf = zk.createHeader(command, chksum, session_id,
                                      reply_id, command_string)
                zk.zkclient.sendto(buf, zk.address)
                try:
                    zk.data_recv, addr = zk.zkclient.recvfrom(1024)
                    command = unpack('HHHH', zk.data_recv[:8])[0]
                    if command == CMD_PREPARE_DATA:
                        size = unpack('I', zk.data_recv[8:12])[0]
                        zk_size = size
                    else:
                        zk_size = False
                    if zk_size:
                        bytes = zk_size
                        while bytes > 0:
                            data_recv, addr = zk.zkclient.recvfrom(1032)
                            zk.attendancedata.append(data_recv)
                            bytes -= 1024
                        zk.session_id = unpack('HHHH', zk.data_recv[:8])[2]
                        data_recv = zk.zkclient.recvfrom(8)
                    attendance = []
                    if len(zk.attendancedata) > 0:
                        # The first 4 bytes don't seem to be related to the user
                        for x in xrange(len(zk.attendancedata)):
                            if x > 0:
                                zk.attendancedata[x] = zk.attendancedata[x][8:]
                        attendancedata = b''.join(zk.attendancedata) 
                        attendancedata = attendancedata[14:] 
                        while len(attendancedata) > 0:
                            uid, state, timestamp, space = unpack('24s1s4s11s', attendancedata.ljust(40)[:40])
                            pls = unpack('c', attendancedata[29:30])
                            uid = uid.split(b'\x00', 1)[0].decode('utf-8')
                            tmp = ''
                            for i in reversed(range(int(len(binascii.hexlify(timestamp)) / 2))):
                                tmp += binascii.hexlify(timestamp).decode('utf-8')[i * 2:(i * 2) + 2] 
                            attendance.append((uid, int(binascii.hexlify(state), 16),
                                               decode_time(int(tmp, 16)), unpack('HHHH', space[:8])[0]))
                            
                            attendancedata = attendancedata[40:]
                except Exception as e:
                    _logger.info("++++++++++++Exception++++++++++++++++++++++", e)
                    attendance = False
                if attendance:
                    for each in attendance:
                        atten_time = each[2]
                        atten_time = datetime.strptime(
                            atten_time.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
                        local_tz = pytz.timezone(
                            self.env.user.partner_id.tz or 'GMT')
                        local_dt = local_tz.localize(atten_time, is_dst=None)
                        utc_dt = local_dt.astimezone(pytz.utc)
                        utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                        atten_time = datetime.strptime(
                            utc_dt, "%Y-%m-%d %H:%M:%S")
                        atten_time = fields.Datetime.to_string(atten_time)
                        if user:
                            for uid in user:
                                if user[uid][0] == str(each[0]):
                                    get_user_id = self.env['hr.employee'].search(
                                        [('device_id', '=', str(each[0]))])
                                    if get_user_id:
                                        duplicate_atten_ids = zk_attendance.search(
                                            [('device_id', '=', str(each[0])), ('punching_time', '=', atten_time)])
                                        if duplicate_atten_ids:
                                            continue
                                        else:
                                            zk_attendance.create({'employee_id': get_user_id.id,
                                                                  'device_id': each[0],
                                                                  'attendance_type': str(each[1]),
                                                                  'punch_type': str(each[3]),
                                                                  'punching_time': atten_time,
                                                                  'address_id': info.address_id.id})
                                            att_var = att_obj.search([('employee_id', '=', get_user_id.id),
                                                                      ('check_out', '=', False)])
                                            if each[3] == 0: #check-in
                                                if not att_var:
                                                    att_obj.create({'employee_id': get_user_id.id,
                                                                    'check_in': atten_time})
                                            if each[3] == 1: #check-out
                                                if len(att_var) == 1:
                                                    att_var.write({'check_out': atten_time})
                                                else:
                                                    att_var1 = att_obj.search([('employee_id', '=', get_user_id.id)])
                                                    if att_var1:
                                                        att_var1[-1].write({'check_out': atten_time})

                                    else:
                                        employee = self.env['hr.employee'].create(
                                            {'device_id': str(each[0]), 'name': user[uid][1]})
                                        zk_attendance.create({'employee_id': employee.id,
                                                              'device_id': each[0],
                                                              'attendance_type': str(each[1]),
                                                              'punch_type': str(each[3]),
                                                              'punching_time': atten_time,
                                                              'address_id': info.address_id.id})
                                        att_obj.create({'employee_id': employee.id,
                                                        'check_in': atten_time})
                                else:
                                    pass
                    zk.enableDevice()
                    zk.disconnect()
                    return True
                else:
                    raise UserError(_('Unable to get the attendance log, please try again later.'))
            else:
                raise UserError(_('Unable to connect, please check the parameters and network connections.'))
