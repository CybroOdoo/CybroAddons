# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
import base64
import binascii
import datetime
import logging
import threading
from threading import Thread
import time
import pytz
from zk.exception import ZKErrorResponse
from odoo import api, fields, models, registry, _
from odoo.exceptions import UserError, ValidationError
live_capture_thread = None
_logger = logging.getLogger(__name__)
try:
    from zk import const, ZK
    from zk.finger import Finger
except ImportError:
    _logger.error("Please Install pyzk library.")


class BiometricDeviceDetails(models.Model):
    """Model for configuring and connect the biometric device with odoo"""
    _name = 'biometric.device.details'
    _description = 'Biometric Device Details'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, help='Record Name')
    device_ip = fields.Char(string='Device IP', required=True,
                            help='The IP address of the Device')
    port_number = fields.Integer(string='Port Number', required=True,
                                 help="The Port Number of the Device")
    address_id = fields.Many2one('res.partner', string='Working Address',
                                 help='Working address of the partner')
    is_live_capture = fields.Boolean('Live Capturing',
                                     help="if enabled, gets the live capture "
                                          "from the device",
                                     readonly=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda
                                     self: self.env.user.company_id.id,
                                 help='Current Company')
    stopwatch_time = fields.Float('Stopwatch timer',
                                  help='Time from Live capture enabled')
    device_name = fields.Char(String='Device Name', readonly=True,
                              help='Device Name')
    device_firmware = fields.Char(String='Device Firmware Version',
                                  readonly=True, help='Device Firmware')
    device_serial_no = fields.Char(String='Device Serial No', readonly=True,
                                   help='Device serial No')
    device_platform = fields.Char(String='Device Platform', readonly=True,
                                  help='Device platform')
    device_mac = fields.Char(String='Device Mac ID', readonly=True,
                             help='Device Mac')
    live_capture_start_time = fields.Datetime('Live Capture Time',
                                              help='The Time When Live '
                                                   'Capture Enabled')

    def device_connect(self, zk):
        """Function for connecting the device with Odoo"""
        try:
            conn = zk.connect()
            return conn
        except Exception:
            return False

    def action_test_connection(self):
        """Checking the connection status"""
        zk = ZK(self.device_ip, port=self.port_number, timeout=30,
                password=False, ommit_ping=False)
        try:
            if zk.connect():
                zk.test_voice(index=0)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': 'Successfully Connected',
                        'type': 'success',
                        'sticky': False
                    }
                }

        except Exception as error:
            raise ValidationError(f'{error}')

    def action_clear_attendance(self):
        """Methode to clear record from the zk.machine.attendance model and
        from the device"""
        for info in self:
            try:
                machine_ip = info.device_ip
                zk_port = info.port_number
                try:
                    # Connecting with the device
                    zk = ZK(machine_ip, port=zk_port, timeout=30,
                            password=0, force_udp=False, ommit_ping=False)
                except NameError:
                    raise UserError(_(
                        "Please install it with 'pip3 install pyzk'."))
                conn = self.device_connect(zk)
                if conn:
                    conn.enable_device()
                    clear_data = zk.get_attendance()
                    if clear_data:
                        # Clearing data in the device
                        conn.clear_attendance()
                        # Clearing data from attendance log
                        self._cr.execute(
                            """delete from zk_machine_attendance""")
                        current_time = fields.datetime.now().strftime(
                            '%Y-%m-%d %H:%M:%S')
                        message = (f'Attendances Are cleared from the Device on'
                                   f' {current_time} By {self.env.user.name}')
                        self.message_post(body=message)
                        conn.disconnect()
                    else:
                        raise UserError(
                            _('Unable to clear Attendance log.Are you sure '
                              'attendance log is not empty.'))
                else:
                    raise UserError(
                        _('Unable to connect to Attendance Device. Please use '
                          'Test Connection button to verify.'))
            except Exception as error:
                raise ValidationError(f'{error}')

    def action_download_attendance(self):
        """Function to download attendance records from the device"""
        _logger.info("++++++++++++Cron Executed++++++++++++++++++++++")
        zk_attendance = self.env['zk.machine.attendance']
        hr_attendance = self.env['hr.attendance']
        for info in self:
            machine_ip = info.device_ip
            zk_port = info.port_number
            try:
                # Connecting with the device with the ip and port provided
                zk = ZK(machine_ip, port=zk_port, timeout=15,
                        password=0,
                        force_udp=False, ommit_ping=False)
            except NameError:
                raise UserError(
                    _("Pyzk module not Found. Please install it"
                      "with 'pip3 install pyzk'."))
            conn = self.device_connect(zk)
            self.get_device_information()
            if conn:
                conn.disable_device()
                self.get_all_users()
                self.action_set_timezone()
                user = conn.get_users()
                # get All Fingerprints
                fingers = conn.get_templates()
                for use in user:
                    for finger in fingers:
                        if finger.uid == use.uid:
                            templates = conn.get_user_template(uid=use.uid,
                                                               temp_id=finger.fid,
                                                               user_id=use.user_id)
                            hex_data = templates.template.hex()
                            # Convert hex data to binary
                            binary_data = binascii.unhexlify(hex_data)
                            base64_data = base64.b64encode(binary_data).decode(
                                'utf-8')
                            employee = self.env['hr.employee'].search(
                                [('device_id_num', '=', use.user_id)])
                            employee.write({
                                'device_id': self.id,
                            })
                            if str(finger.fid) in employee.fingerprint_ids.mapped(
                                    'finger_id'):
                                employee.fingerprint_ids.search(
                                    [('finger_id', '=', finger.fid)]).update({
                                    'finger_template': base64_data,
                                })
                            else:
                                employee.fingerprint_ids.create({
                                    'finger_template': base64_data,
                                    'finger_id': finger.fid,
                                    'employee_id': employee.id,
                                    'filename': f'{employee.name}-finger-{finger.fid}'
                                })
                # get all attendances
                attendance = conn.get_attendance()
                if attendance:
                    for each in attendance:
                        atten_time = each.timestamp
                        local_tz = pytz.timezone(
                            self.env.user.partner_id.tz or 'GMT')
                        local_dt = local_tz.localize(atten_time, is_dst=None)
                        utc_dt = local_dt.astimezone(pytz.utc)
                        utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                        atten_time = datetime.datetime.strptime(
                            utc_dt, "%Y-%m-%d %H:%M:%S")
                        atten_time = fields.Datetime.to_string(atten_time)
                        for uid in user:
                            if uid.user_id == each.user_id:
                                get_user_id = self.env['hr.employee'].search(
                                    [('device_id_num', '=', each.user_id)])
                                if get_user_id:
                                    duplicate_atten_ids = zk_attendance.search(
                                        [('device_id_num', '=', each.user_id),
                                         ('punching_time', '=', atten_time)])
                                    if not duplicate_atten_ids:
                                        zk_attendance.create({
                                            'employee_id': get_user_id.id,
                                            'device_id_num': each.user_id,
                                            'attendance_type': str(each.status),
                                            'punch_type': str(each.punch),
                                            'punching_time': atten_time,
                                            'address_id': info.address_id.id
                                        })
                                        att_var = hr_attendance.search([(
                                            'employee_id', '=', get_user_id.id),
                                            ('check_out', '=', False)])
                                        if each.punch == 0:  # check-in
                                            if not att_var:
                                                hr_attendance.create({
                                                    'employee_id':
                                                        get_user_id.id,
                                                    'check_in': atten_time
                                                })
                                        if each.punch == 1:  # check-out
                                            if len(att_var) == 1:
                                                att_var.write({
                                                    'check_out': atten_time
                                                })
                                            else:
                                                att_var1 = hr_attendance.search(
                                                    [('employee_id', '=',
                                                      get_user_id.id)])
                                                if att_var1:
                                                    att_var1[-1].write({
                                                        'check_out': atten_time
                                                    })
                                else:
                                    employee = self.env['hr.employee'].create({
                                        'device_id_num': each.user_id,
                                        'device_id': self.id,
                                        'name': uid.name
                                    })
                                    zk_attendance.create({
                                        'employee_id': employee.id,
                                        'device_id_num': each.user_id,
                                        'attendance_type': str(each.status),
                                        'punch_type': str(each.punch),
                                        'punching_time': atten_time,
                                        'address_id': info.address_id.id
                                    })
                                    hr_attendance.create({
                                        'employee_id': employee.id,
                                        'check_in': atten_time
                                    })
                    if not self.is_live_capture:
                        current_time = fields.datetime.now().strftime(
                            '%Y-%m-%d %H:%M:%S')
                        message = (f'Downloaded data from the device on '
                                   f'{current_time} by {self.env.user.name}')
                        self.message_post(body=message)
                    conn.disconnect()
                    return True
                else:
                    zk.test_voice(index=4)
                    raise UserError(_('Unable to get the attendance log, please'
                                      'try again later.'))
            else:
                raise UserError(_('Unable to connect, please check the'
                                  'parameters and network connections.'))

    def action_restart_device(self):
        """For restarting the device"""
        zk = ZK(self.device_ip, port=self.port_number, timeout=15,
                password=0,
                force_udp=False, ommit_ping=False)
        if self.device_connect(zk):
            if self.is_live_capture:
                self.action_stop_live_capture()
            self.device_connect(zk).restart()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Successfully Device Restarted',
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            raise UserError(_(
                "Please Check the Connection"))

    def schedule_attendance(self):
        """Schedule action for attendance downloading"""
        for record in self.search([]):
            if record.is_live_capture:
                record.action_stop_live_capture()
                record.action_download_attendance()
                record.action_live_capture()
            else:
                record.action_download_attendance()

    def action_live_capture(self):
        """ Enable Live capture With Thread"""
        for info in self:
            machine_ip = info.device_ip
            zk_port = info.port_number
            try:
                self.is_live_capture = True
                self.action_set_timezone()
                instance = ZKBioAttendance(machine_ip, zk_port, info)
                global live_capture_thread
                live_capture_thread = instance
                live_capture_thread.start()
                self.live_capture_start_time = fields.datetime.now()
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
            except NameError:
                raise UserError(_(
                    "Please install it with 'pip3 install pyzk'."))

    def action_stop_live_capture(self):
        """Function to stop Live capture"""
        try:
            self.is_live_capture = False
            if live_capture_thread:
                live_capture_thread.stop()
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        except NameError:
            raise UserError(_(
                "Please install it with 'pip3 install pyzk'."))

    def action_set_timezone(self):
        """Function to set user's timezone to device"""
        for info in self:
            machine_ip = info.device_ip
            zk_port = info.port_number
            try:
                # Connecting with the device with the ip and port provided
                zk = ZK(machine_ip, port=zk_port, timeout=15,
                        password=0,
                        force_udp=False, ommit_ping=False)
            except NameError:
                raise UserError(
                    _("Pyzk module not Found. Please install it"
                      "with 'pip3 install pyzk'."))
            conn = self.device_connect(zk)
            if conn:
                user_tz = self.env.context.get(
                    'tz') or self.env.user.tz or 'UTC'
                user_timezone_time = pytz.utc.localize(fields.Datetime.now())
                user_timezone_time = user_timezone_time.astimezone(
                    pytz.timezone(user_tz))
                conn.set_time(user_timezone_time)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': 'Successfully Set the Time',
                        'type': 'success',
                        'sticky': False
                    }
                }
            else:
                raise UserError(_(
                    "Please Check the Connection"))

    def get_all_users(self):
        """Function to get all user's details"""
        for info in self:
            machine_ip = info.device_ip
            zk_port = info.port_number
            try:
                # Connecting with the device with the ip and port provided
                zk = ZK(machine_ip, port=zk_port, timeout=15,
                        password=0,
                        force_udp=False, ommit_ping=False)
            except NameError:
                raise UserError(
                    _("Pyzk module not Found. Please install it"
                      "with 'pip3 install pyzk'."))
            conn = self.device_connect(zk)
            if conn:
                users = conn.get_users()
                for user in users:
                    employee = self.env['hr.employee'].search(
                        [('device_id_num', '=', user.user_id),
                         ('device_id', '=', self.id)])
                    if employee:
                        employee.write({
                            'name': user.name,
                        })
                    else:
                        self.env['hr.employee'].create({
                            'name': user.name,
                            'device_id_num': user.user_id,
                            'device_id': self.id,
                        })
            else:
                raise UserError(_(
                    "Please Check the Connection"))

    def set_user(self, employee_id):
        """Function to create or update users"""
        for info in self:
            machine_ip = info.device_ip
            zk_port = info.port_number
            employee = self.env['hr.employee'].browse(int(employee_id))
            try:
                # Connecting with the device with the ip and port provided
                zk = ZK(machine_ip, port=zk_port, timeout=15,
                        password=0,
                        force_udp=False, ommit_ping=False)
            except NameError:
                raise UserError(
                    _("Pyzk module not Found. Please install it"
                      "with 'pip3 install pyzk'."))
            conn = self.device_connect(zk)
            if conn:
                last_user = conn.get_users()[-1]
                privilege = 0
                password = ''
                group_id = ''
                user_id = ''
                card = 0
                try:
                    uids = [user.uid for user in conn.get_users()]
                    candidate_uid = last_user.uid + 1
                    while candidate_uid in uids:
                        candidate_uid += 1
                    conn.set_user(candidate_uid, employee.name, privilege,
                                  password, group_id, user_id, card)
                except ZKErrorResponse as e:
                    _logger.error("Failed to set user on the device: %s",
                                  str(e))
                if conn.get_users()[-1].name == employee.name:
                    employee.write({
                        'device_id': self.id,
                        'device_id_num': conn.get_users()[-1].user_id
                    })
                    current_time = fields.datetime.now().strftime(
                        '%Y-%m-%d %H:%M:%S')
                    message = (f'New User {employee.name} Created on '
                               f'{current_time} by {self.env.user.name}')
                    self.message_post(body=message)
            else:
                raise UserError(_(
                    "Please Check the Connection"))

    def delete_user(self, employee_id, delete_user_selection):
        """Function to Delete a user"""
        for info in self:
            machine_ip = info.device_ip
            zk_port = info.port_number
            try:
                # Connecting with the device with the ip and port provided
                zk = ZK(machine_ip, port=zk_port, timeout=15,
                        password=0,
                        force_udp=False, ommit_ping=False)
            except NameError:
                raise UserError(
                    _("Pyzk module not Found. Please install it"
                      "with 'pip3 install pyzk'."))
            conn = self.device_connect(zk)
            if conn:
                employee = self.env['hr.employee'].browse(int(employee_id))
                employee_name = employee.name
                conn.delete_user(uid=None, user_id=employee.device_id_num)
                employee.write({
                    'device_id_num': False,
                    'device_id': False
                })
                employee.fingerprint_ids.unlink()
                if delete_user_selection == 'both_device':
                    employee.unlink()
                current_time = fields.datetime.now().strftime(
                    '%Y-%m-%d %H:%M:%S')
                message = (f'Deleted User {employee_name} on '
                           f'{current_time} by {self.env.user.name}')
                self.message_post(body=message)
            else:
                raise UserError(_(
                    "Please Check the Connection"))

    def update_user(self, employee_id):
        """Function to Update a user"""
        for info in self:
            machine_ip = info.device_ip
            zk_port = info.port_number
            try:
                # Connecting with the device with the ip and port provided
                zk = ZK(machine_ip, port=zk_port, timeout=15,
                        password=0,
                        force_udp=False, ommit_ping=False)
            except NameError:
                raise UserError(
                    _("Pyzk module not Found. Please install it"
                      "with 'pip3 install pyzk'."))
            conn = self.device_connect(zk)
            if conn:
                employee = self.env['hr.employee'].browse(int(employee_id))
                for line in conn.get_users():
                    if line.user_id == employee.device_id_num:
                        privilege = 0
                        password = ''
                        group_id = ''
                        user_id = employee.device_id_num
                        card = 0
                        conn.set_user(line.uid, employee.name, privilege,
                                      password, group_id, user_id, card)
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'message': 'Successfully Updated User',
                                'type': 'success',
                                'sticky': False
                            }
                        }
                else:
                    raise UserError(_(
                        "Please Check the Connection"))

    def get_device_information(self):
        """Gets device Information"""
        for info in self:
            machine_ip = info.device_ip
            zk_port = info.port_number
            try:
                # Connecting with the device with the ip and port provided
                zk = ZK(machine_ip, port=zk_port, timeout=15,
                        password=0,
                        force_udp=False, ommit_ping=False)
            except NameError:
                raise UserError(
                    _("Pyzk module not Found. Please install it"
                      "with 'pip3 install pyzk'."))
            conn = self.device_connect(zk)
            if conn:
                self.device_name = conn.get_device_name()
                self.device_firmware = conn.get_firmware_version()
                self.device_serial_no = conn.get_serialnumber()
                self.device_platform = conn.get_platform()
                self.device_mac = conn.get_mac()
            else:
                raise UserError(_(
                    "Please Check the Connection"))


class ZKBioAttendance(Thread):
    """
    Represents a thread for capturing live attendance data from a ZKTeco
    biometric device.

    Attributes: - machine_ip: The IP address of the ZKTeco biometric device.
    - port_no: The port number for communication with the ZKTeco biometric
    device. - conn: The connection object to the ZKTeco biometric device.

    Methods: - run(): Overrides the run method of the Thread class to capture
    live attendance data.
    """

    def __init__(self, machine_ip, port_no, record):
        """Function to Initialize the thread"""
        Thread.__init__(self)
        self.machine_ip = machine_ip
        self.port_no = port_no
        self.record = record
        self.env = record.env
        self.stop_event = threading.Event()

        zk_device = ZK(
            machine_ip,
            port=port_no,
            timeout=5,
            password=0,
            force_udp=False,
            ommit_ping=False,
        )
        conn = zk_device.connect()
        if conn:
            self.conn = conn
        else:
            raise UserError(_(
                "Please Check the Connection"))

    def run(self):
        """Function to run the Thread"""
        while not self.stop_event.is_set():
            try:
                if not self.conn.end_live_capture:
                    for attendance in self.conn.live_capture(2000):
                        self._data_live_capture()
                time.sleep(10)
            except Exception as e:
                self.env.cr.rollback()  # Rollback the current transaction
                time.sleep(1)

    def stop(self):
        """Stops the live capture and stops the thread"""
        if self.conn:
            self.conn.end_live_capture = True
        self.stop_event.set()

    def _data_live_capture(self):
        """Updated the Live Capture real time"""
        with registry(self.env.cr.dbname).cursor() as new_cr:
            new_env = api.Environment(new_cr, self.env.uid, self.env.context)
            if self.conn.get_attendance():
                self.record.with_env(new_env).action_download_attendance()
            new_cr.commit()
