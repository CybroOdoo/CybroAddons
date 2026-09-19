# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import base64
import datetime
import logging
import threading
from threading import Thread
import time
import pytz
from odoo.modules.registry import Registry
from odoo import _, api, fields, models
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

    name = fields.Char(required=True, help='Name of the Biometric Device')
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
                                 help="Name of the Company",
                                 default=lambda self: self.env.company)
    stopwatch_time = fields.Float('Stopwatch timer',
                                  help='Time from Live capture enabled')
    device_name = fields.Char(string='Device Name', readonly=True,
                              help='Name of the Device')
    device_firmware = fields.Char(string='Device Firmware Version',
                                  readonly=True, help='Device Firmware')
    device_serial_no = fields.Char(string='Device Serial No', readonly=True,
                                   help='Serial No of the Device')
    device_platform = fields.Char(string='Device Platform', readonly=True,
                                  help='Platform of the Device')
    device_mac = fields.Char(string='Device Mac ID', readonly=True,
                             help='Mac ID of the Device')
    live_capture_start_time = fields.Datetime('Live Capture Time',
                                              help='The Time When Live '
                                                   'Capture Enabled')
    device_password = fields.Integer(string='Password',
                                     help='Enter the device password')
    ommit_ping = fields.Boolean(string='Omit Ping', default=True,
                                help='Omit ICMP ping check before TCP connection')

    device_timezone = fields.Selection(
        selection='_get_timezone_list',
        string='Device Timezone',
        default='Asia/Calcutta',
        required=True,
        help='Timezone where the biometric device is physically located. '
             'This ensures consistent time conversion regardless of who downloads the attendance.'
    )

    @api.model
    def _get_timezone_list(self):
        """Return list of timezones"""
        return [(tz, tz) for tz in pytz.all_timezones]

    def device_connect(self, zk):
        """Function for connecting the device with Odoo"""
        try:
            conn = zk.connect()
            return conn
        except Exception:
            return False

    def action_test_connection(self):
        """Checking the connection status"""

        zk = ZK(
            self.device_ip,
            port=self.port_number,
            timeout=30,
            password=self.device_password,
            ommit_ping=self.ommit_ping
        )
        try:
            connection = zk.connect()

            if connection:
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
            _logger.exception("ZK connection error: %s", error)

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
                            password=info.device_password, force_udp=False,
                            ommit_ping=info.ommit_ping)
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
                        # Get current time in user's timezone
                        user_tz = pytz.timezone(self.env.user.tz or 'UTC')
                        current_time_utc = fields.Datetime.now()
                        current_time_local = pytz.utc.localize(
                            current_time_utc).astimezone(user_tz)
                        formatted_time = current_time_local.strftime(
                            '%Y-%m-%d %H:%M:%S %Z')
                        message = (
                            f'Attendances Are cleared from the Device on '
                            f'{formatted_time} by {self.env.user.name}')
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
        zk_attendance = self.env['zk.machine.attendance']
        hr_attendance = self.env['hr.attendance']

        # Get valid selection keys for punch_type to avoid ValueError
        valid_punch_types = [x[0] for x in zk_attendance._fields['punch_type'].selection]

        for info in self:
            machine_ip = info.device_ip
            zk_port = info.port_number
            try:
                zk = ZK(machine_ip, port=zk_port, timeout=30,
                        password=info.device_password,
                        force_udp=False, ommit_ping=info.ommit_ping)
            except NameError:
                raise UserError(_("Pyzk module not Found. Please install it with 'pip3 install pyzk'."))

            conn = self.device_connect(zk)
            if conn:
                try:
                    conn.disable_device()
                    self.get_device_information()
                    self.get_all_users()
                    self.action_set_timezone()

                    users = conn.get_users()
                    fingers = conn.get_templates()

                    # --- PART 1: Sync Fingerprints ---
                    for use in users:
                        employee = self.env['hr.employee'].search([
                            ('device_id_num', '=', use.user_id),
                            ('company_id', '=', self.env.company.id)
                        ], limit=1)  # FIX: limit=1 avoids "Expected singleton"

                        if employee:
                            employee.write({'device_id': self.id})
                            for finger in fingers:
                                if finger.uid == use.uid:
                                    template_obj = conn.get_user_template(
                                        uid=use.uid, temp_id=finger.fid, user_id=use.user_id)
                                    if template_obj:
                                        base64_data = base64.b64encode(template_obj.template).decode('utf-8')

                                        # Check if this specific finger exists
                                        existing_finger = employee.fingerprint_ids.filtered(
                                            lambda r: r.finger_id == str(finger.fid))

                                        if existing_finger:
                                            existing_finger[0].write({'finger_template': base64_data})
                                        else:
                                            employee.fingerprint_ids.create({
                                                'finger_template': base64_data,
                                                'finger_id': finger.fid,
                                                'employee_id': employee.id,
                                                'filename': f'{employee.name}-finger-{finger.fid}'
                                            })

                    # --- PART 2: Sync Attendance ---
                    attendance = conn.get_attendance()
                    if attendance:
                        for each in attendance:
                            # Timezone conversion
                            atten_time = each.timestamp
                            local_tz = pytz.timezone(info.device_timezone or 'Asia/Calcutta')
                            local_dt = local_tz.localize(atten_time, is_dst=None)
                            utc_dt = local_dt.astimezone(pytz.utc)
                            atten_time_str = fields.Datetime.to_string(utc_dt)

                            # Identify Employee
                            get_user_id = self.env['hr.employee'].search([
                                ('device_id_num', '=', each.user_id),
                                ('company_id', '=', self.env.company.id)
                            ], limit=1)  # FIX: limit=1 avoids "Expected singleton"

                            if get_user_id:
                                # Validate Punch Type (Fixes the '255' error)
                                punch_val = str(each.punch)
                                if punch_val not in valid_punch_types:
                                    _logger.warning(f"Device sent invalid punch type {punch_val}. Defaulting to '0'")
                                    punch_val = '0'

                                # Check for duplicates
                                duplicate = zk_attendance.search([
                                    ('device_id_num', '=', each.user_id),
                                    ('punching_time', '=', atten_time_str),
                                    ('company_id', '=', self.env.company.id)
                                ], limit=1)

                                if not duplicate:
                                    # Create ZK Log
                                    zk_attendance.create({
                                        'employee_id': get_user_id.id,
                                        'device_id_num': each.user_id,
                                        'attendance_type': str(each.status),
                                        'punch_type': punch_val,
                                        'punching_time': atten_time_str,
                                        'address_id': info.address_id.id,
                                        'company_id': self.env.company.id
                                    })

                                    # Update HR Attendance
                                    # Find latest open attendance for this employee
                                    open_attendance = hr_attendance.search([
                                        ('employee_id', '=', get_user_id.id),
                                        ('check_out', '=', False)
                                    ], order='check_in desc', limit=1)

                                    if punch_val == '0':  # Check-in
                                        if not open_attendance:
                                            hr_attendance.create({
                                                'employee_id': get_user_id.id,
                                                'check_in': atten_time_str
                                            })
                                    elif punch_val == '1':  # Check-out
                                        if open_attendance:
                                            open_attendance.write({'check_out': atten_time_str})
                                        else:
                                            # Optional: If checkout found without checkin,
                                            # create a record with checkin=checkout or ignore
                                            pass
                            else:
                                # Logic to create employee if not found
                                new_emp = self.env['hr.employee'].create({
                                    'device_id_num': each.user_id,
                                    'device_id': self.id,
                                    'name': next((u.name for u in users if u.user_id == each.user_id), each.user_id),
                                    'company_id': self.env.company.id,
                                })
                                hr_attendance.create({
                                    'employee_id': new_emp.id,
                                    'check_in': atten_time_str
                                })

                    if not self.is_live_capture:
                        user_tz = pytz.timezone(self.env.user.tz or 'UTC')
                        formatted_time = pytz.utc.localize(datetime.datetime.now()).astimezone(user_tz).strftime(
                            '%Y-%m-%d %H:%M:%S %Z')
                        self.message_post(
                            body=f'Downloaded data from device on {formatted_time} by {self.env.user.name}')

                    conn.enable_device()
                    conn.disconnect()
                except Exception as e:
                    _logger.error(f"Error during download: {str(e)}")
                    conn.enable_device()
                    conn.disconnect()
                    raise UserError(_("Communication error: %s") % str(e))

                return True
            else:
                raise UserError(_('Unable to connect, please check the parameters and network connections.'))

    def action_restart_device(self):
        """For restarting the device"""
        zk = ZK(self.device_ip, port=self.port_number, timeout=30,
                password=self.device_password,
                force_udp=False, ommit_ping=self.ommit_ping)
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
            password = info.device_password
            try:
                self.is_live_capture = True
                self.action_set_timezone()
                instance = ZKBioAttendance(machine_ip, zk_port, password, info)
                global live_capture_thread
                live_capture_thread = instance
                live_capture_thread.start()
                self.live_capture_start_time = fields.Datetime.now()
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
                zk = ZK(machine_ip, port=zk_port, timeout=30,
                        password=info.device_password,
                        force_udp=False, ommit_ping=info.ommit_ping)
            except NameError:
                raise UserError(
                    _("Pyzk module not Found. Please install it"
                      "with 'pip3 install pyzk'."))
            conn = self.device_connect(zk)
            if conn:
                # ⭐ Use device timezone instead of user timezone
                device_tz = info.device_timezone or 'UTC'
                device_timezone_time = pytz.utc.localize(fields.Datetime.now())
                device_timezone_time = device_timezone_time.astimezone(
                    pytz.timezone(device_tz))
                conn.set_time(device_timezone_time)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': f'Successfully Set the Time to {device_tz}',
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
                zk = ZK(machine_ip, port=zk_port, timeout=30,
                        password=info.device_password,
                        force_udp=False, ommit_ping=info.ommit_ping)
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
                zk = ZK(machine_ip, port=zk_port, timeout=30,
                        password=info.device_password,
                        force_udp=False, ommit_ping=info.ommit_ping)
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
                card = 0
                conn.enable_device()
                conn.disable_device()
                try:
                    uids = [user.uid for user in conn.get_users()]
                    candidate_uid = last_user.uid + 1
                    while candidate_uid in uids:
                        candidate_uid += 1
                    conn.set_user(candidate_uid, employee.name, privilege,
                                  password, group_id, str(candidate_uid), card)
                except Exception as e:
                    _logger.info(e)
                    raise ValidationError(
                        _(" Here is the user information:\n"
                          "uid: %s\n"
                          "name: %s\n"
                          "privilege: %s\n"
                          "password: %s\n"
                          "group_id: %s\n"
                          "user_id: %s\n"
                          "Here is the debugging information:\n%s\n"
                          "Try Restarting the device")
                        % (candidate_uid, employee.name, privilege, password,
                           group_id, str(candidate_uid), e))
                conn.enable_device()
                if conn.get_users()[-1].name in employee.name:
                    employee.write({
                        'device_id': self.id,
                        'device_id_num': conn.get_users()[-1].user_id
                    })
                    # Get current time in user's timezone
                    user_tz = pytz.timezone(self.env.user.tz or 'UTC')
                    current_time_utc = fields.Datetime.now()
                    current_time_local = pytz.utc.localize(
                        current_time_utc).astimezone(user_tz)
                    formatted_time = current_time_local.strftime(
                        '%Y-%m-%d %H:%M:%S %Z')
                    message = (f'New User {employee.name} Created on '
                               f'{formatted_time} by {self.env.user.name}')
                    self.message_post(body=message)
            else:
                raise UserError(_(
                    "Please Check the Connection"))

    def delete_user(self, employee_id, employee_user_selection):
        """Function to Delete a user"""
        for info in self:
            machine_ip = info.device_ip
            zk_port = info.port_number
            try:
                # Connecting with the device with the ip and port provided
                zk = ZK(machine_ip, port=zk_port, timeout=30,
                        password=info.device_password,
                        force_udp=False, ommit_ping=info.ommit_ping)
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
                if employee_user_selection == 'both_device':
                    employee.unlink()
                # Get current time in user's timezone
                user_tz = pytz.timezone(self.env.user.tz or 'UTC')
                current_time_utc = fields.Datetime.now()
                current_time_local = pytz.utc.localize(
                    current_time_utc).astimezone(user_tz)
                formatted_time = current_time_local.strftime(
                    '%Y-%m-%d %H:%M:%S %Z')
                message = (f'New User {employee.name} Created on '
                           f'{formatted_time} by {self.env.user.name}')
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
                zk = ZK(machine_ip, port=zk_port, timeout=30,
                        password=info.device_password,
                        force_udp=False, ommit_ping=info.ommit_ping)
            except NameError:
                raise UserError(
                    _("Pyzk module not Found. Please install it"
                      "with 'pip3 install pyzk'."))
            conn = self.device_connect(zk)
            if conn:
                conn.enable_device()
                conn.disable_device()
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
                        conn.enable_device()
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
                zk = ZK(machine_ip, port=zk_port, timeout=30,
                        password=info.device_password,
                        force_udp=False, ommit_ping=info.ommit_ping)
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
    Thread for capturing live attendance data from ZKTeco biometric device.
    Periodically downloads all attendance from device.
    """

    def __init__(self, machine_ip, port_no, password, record):
        """Function to Initialize the thread"""
        Thread.__init__(self)
        self.daemon = True
        self.machine_ip = machine_ip
        self.port_no = port_no
        self.password = password
        self.record = record
        self.env = record.env
        self.stop_event = threading.Event()

        _logger.info(f"Initializing live capture thread for {machine_ip}")

        zk_device = ZK(
            machine_ip,
            port=port_no,
            timeout=30,
            password=password,
            force_udp=False,
            ommit_ping=True,
        )
        conn = zk_device.connect()
        if conn:
            self.conn = conn
            conn.disable_device()
            _logger.info(f"Live capture connected to {machine_ip}")
        else:
            raise UserError(_("Unable to connect to device"))

    def run(self):
        """Function to run the Thread - continuously monitors for new attendance"""
        _logger.info(f"Live capture thread started for {self.machine_ip}")

        while not self.stop_event.is_set():
            try:
                if not self.conn.end_live_capture:
                    for attendance in self.conn.live_capture():
                        if self.stop_event.is_set():
                            break

                        if attendance:
                            _logger.info(
                                f"Live event detected: User {attendance.user_id if hasattr(attendance, 'user_id') else 'Unknown'}")
                            self._data_live_capture()

                time.sleep(2)

            except Exception as e:
                _logger.error(f"Live capture error: {str(e)}")
                time.sleep(5)

        _logger.info(f"Live capture thread stopped for {self.machine_ip}")

    def stop(self):
        """Stops the live capture and stops the thread"""
        _logger.info(f"Stopping live capture for {self.machine_ip}")
        if self.conn:
            self.conn.end_live_capture = True
            try:
                self.conn.enable_device()
                self.conn.disconnect()
            except:
                pass
        self.stop_event.set()

    def _data_live_capture(self):
        """Download all attendance data when live event detected"""
        with Registry(self.env.cr.dbname).cursor() as new_cr:
            try:
                new_env = api.Environment(new_cr, self.env.uid,
                                          self.env.context)

                if self.conn.get_attendance():
                    _logger.info("Downloading attendance from device...")
                    self.record.with_env(new_env).action_download_attendance()
                    _logger.info("✓ Live capture download completed")

                new_cr.commit()
            except Exception as e:
                _logger.error(f"Error in live capture download: {str(e)}")
                new_cr.rollback()
