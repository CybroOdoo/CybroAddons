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
import datetime
import logging
import pytz
from struct import unpack
from .zkconst import *
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)
try:
    from zk import ZK, const
except ImportError:
    _logger.error("Please Install pyzk library.")

_logger = logging.getLogger(__name__)


class ZkMachine(models.Model):
    """Model for configuring and connect the biometric device with odoo"""
    _name = 'zk.machine'
    _description = 'Configure and Connect the Device'

    name = fields.Char(string='Machine IP', required=True,
                       help='Give the IP Address of the machine')
    port_no = fields.Integer(string='Port No', required=True,
                             help='Give the Port Number of the machine')
    address_id = fields.Many2one('res.partner', string='Working Address',
                                 help='Working address of the partner')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.user.company_id.id,
        help='Company Address')
    active = fields.Boolean(string='Is Active', default=True)

    def device_connect(self, zk):
        """Function for connecting the device with odoo """
        try:
            connection = zk.connect()
            return connection
        except:
            return False

    def action_test_connection(self):
        """Test the connection to the configured biometric device."""
        for device in self:
            try:
                ZK
            except NameError:
                raise UserError(_("Please install pyzk library with 'pip3 install pyzk'."))
            zk = ZK(device.name, port=device.port_no, timeout=15, password=0,
                    force_udp=False, ommit_ping=False)
            connection = self.device_connect(zk)
            if not connection:
                raise UserError(_('Connection failed.'))
            connection.disconnect()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Device connection successful.'),
                    'type': 'success',
                    'sticky': False,
                }
            }
        raise UserError(_('No connected devices found.'))

    def action_clear_attendance(self):
        """Function that wipe all the data's in attendance log"""
        for info in self:
            try:
                machine_ip = info.name
                zk_port = info.port_no
                try:
                    zk = ZK(machine_ip, port=zk_port, timeout=30,
                            password=0, force_udp=False, ommit_ping=False)
                except NameError:
                    raise UserError(_(
                        "Please install it with 'pip3 install pyzk'."))
                connection = self.device_connect(zk)
                if connection:
                    connection.enable_device()
                    clear_data = zk.get_attendance()
                    if clear_data:
                        connection.clear_attendance()
                        self.env.cr.execute(
                            """delete from zk_machine_attendance""")
                        connection.disconnect()
                    else:
                        raise UserError(_('Unable to clear Attendance log. '
                                          'Are you sure attendance log is not'
                                          ' empty.'))
                else:
                    raise UserError(
                        _('Unable to connect to Attendance Device. Please use '
                          'Test Connection button to verify.'))
            except Exception as error:
                raise ValidationError(f'{error}')

    def action_restart_device(self):
        """Method to restart the device."""
        zk = ZK(self.name, port=self.port_no, timeout=15, password=0,
                force_udp=False, ommit_ping=False)
        if self.device_connect(zk):
            self.device_connect(zk).restart()
        else:
            raise UserError(
                _('Unable to restart, please check the device is connected.'))

    def action_set_time(self):
        """Function to set user's timezone to device"""
        for info in self:
            machine_ip = info.name
            zk_port = info.port_no
            try:
                zk = ZK(machine_ip, port=zk_port, timeout=15,
                        password=0, force_udp=False, ommit_ping=False)
            except NameError:
                raise UserError(
                    _("Pyzk module not Found. Please install it"
                      "with 'pip3 install pyzk'."))
            connection = self.device_connect(zk)
            if connection:
                user_tz = self.env.context.get(
                    'tz') or self.env.user.tz or 'UTC'
                user_timezone_time = pytz.utc.localize(fields.Datetime.now())
                user_timezone_time = user_timezone_time.astimezone(
                    pytz.timezone(user_tz))
                connection.set_time(user_timezone_time)
                connection.disconnect()
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': _('Successfully Set the Time'),
                        'type': 'success',
                        'sticky': False
                    }
                }
            else:
                raise UserError(_("Please Check the Connection"))

    def getSizeUser(self, zk):
        """Checks a returned packet to see if it returned CMD_PREPARE_DATA,
        indicating that data packets are to be sent.
        Returns the amount of bytes that are going to be sent"""
        command = unpack('HHHH', zk.data_recv[:8])[0]
        if command == CMD_PREPARE_DATA:
            size = unpack('I', zk.data_recv[8:12])[0]
            return size
        else:
            return False

    def zkgetuser(self, zk):
        """Start a connection with the time clock"""
        try:
            users = zk.get_users()
            return users
        except:
            return False

    def action_import_attendance(self):
        """Function that download all the attendance data"""
        _logger.info("++++++++++++Import Executing++++++++++++++++++++++")
        zk_attendance = self.env['zk.machine.attendance']
        att_obj = self.env['hr.attendance']
        for info in self:
            machine_ip = info.name
            zk_port = info.port_no
            timeout = 15
            try:
                zk = ZK(machine_ip, port=zk_port, timeout=timeout, password=0,
                        force_udp=False, ommit_ping=False)
            except NameError:
                raise UserError(_("Pyzk module not Found. Please install it "
                                  "with 'pip3 install pyzk'."))
            connection = self.device_connect(zk)
            if connection:
                try:
                    user = connection.get_users()
                except:
                    user = False
                try:
                    attendance = connection.get_attendance()
                except:
                    attendance = False
                if attendance:
                    for each in attendance:
                        atten_time = each.timestamp
                        atten_time = datetime.strptime(atten_time.strftime(
                            '%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
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
                                if uid.user_id == each.user_id:
                                    get_user_id = self.env[
                                        'hr.employee'].search(
                                        [('device_id_no', '=', each.user_id)])
                                    if get_user_id:
                                        duplicate_atten_ids = (
                                            zk_attendance.search(
                                                [('device_id_no', '=',
                                                  each.user_id), (
                                                     'punching_time', '=',
                                                     atten_time)]))
                                        if duplicate_atten_ids:
                                            continue
                                        else:
                                            record_user_id = get_user_id[0]
                                            zk_attendance.create({'employee_id': record_user_id.id,
                                                                  'device_id_no': each.user_id,
                                                                  'attendance_type': str(each.status),
                                                                  'punch_type': str(each.punch),
                                                                  'punching_time': atten_time,
                                                                  'address_id': info.address_id.id})
                                            att_var = att_obj.search(
                                                [('employee_id', '=', record_user_id.id),
                                                ('check_out', '=', False)])
                                            if each.punch == 0:  # Check-in
                                                if not att_var:
                                                    att_obj.create({
                                                        'employee_id': record_user_id.id,
                                                        'check_in': atten_time,
                                                        'in_mode': 'technical',
                                                    })
                                            if each.punch == 1:  # Check-out
                                                if len(att_var) == 1:
                                                    att_var.write({
                                                        'check_out': atten_time,
                                                        'out_mode': 'technical',
                                                    })
                                                else:
                                                    att_var1 = att_obj.search(
                                                        [('employee_id', '=', record_user_id.id)])
                                                    if att_var1:
                                                        att_var1[-1].write({
                                                            'check_out': atten_time,
                                                            'out_mode': 'technical',
                                                        })
                                    else:
                                        employee = self.env[
                                            'hr.employee'].create(
                                            {'device_id_no': each.user_id,
                                             'name': uid.name})
                                        zk_attendance.create(
                                            {'employee_id': employee.id,
                                             'device_id_no': each.user_id,
                                             'attendance_type': str(
                                                 each.status),
                                             'punch_type': str(each.punch),
                                             'punching_time': atten_time,
                                             'address_id': info.address_id.id})
                                        att_obj.create(
                                            {'employee_id': employee.id,
                                             'check_in': atten_time,
                                             'in_mode': 'technical'})
                                else:
                                    pass
                    _logger.info('Import Completed')
                    return True
                else:
                    raise UserError(_('Unable to get the attendance log or no data to be imported, '
                                      'please try again later.'))
            else:
                raise UserError(_('Unable to connect, please check the '
                                  'parameters and network connections.'))

    @api.model
    def cron_download(self):
        """Download data's to the attendance log"""
        for machine in self.env['zk.machine'].search([]):
            machine.action_import_attendance()
