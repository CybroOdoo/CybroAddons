# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import logging
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse

import pytz
import requests
from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

ONLINE_THRESHOLD_MINUTES = 10

# Serial numbers arrive on an unauthenticated route: keep them to what a
# ZKTeco terminal can actually report before they reach the database.
SERIAL_RE = re.compile(r'^[A-Za-z0-9_:\-]{1,64}$')

# "Enable Domain Name" must be OFF when the terminal is given a bare IP.
_IP_RE = re.compile(r'^\d{1,3}(\.\d{1,3}){3}$')

# An unapproved device costs a row per unknown serial; cap how many a
# stranger can create by pointing terminals at a public Odoo.
MAX_PENDING_DEVICES = 50


class ZktecoDevice(models.Model):
    _name = 'zkteco.device'
    _description = 'ZKTeco Biometric Device'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'zkteco.device.tcp']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    connection_mode = fields.Selection([
        ('adms', 'ADMS Push (device connects to Odoo)'),
        ('tcp', 'Direct IP (Odoo connects to device)'),
    ], required=True, default='adms', tracking=True, help=(
        "ADMS Push: the terminal dials Odoo over HTTP. No static IP, works "
        "through NAT and on Odoo.sh.\n"
        "Direct IP: Odoo dials the terminal on port 4370. Needs a reachable, "
        "stable device IP and the pyzk package on the server."
    ))
    serial_number = fields.Char(
        index=True, copy=False, tracking=True,
        help='Serial number the device sends as SN in every ADMS request. '
             'Required in ADMS mode; read from the terminal in Direct IP mode.',
    )

    # Direct IP (pull) connection settings.
    ip_address = fields.Char(string='Device IP Address', tracking=True)
    port = fields.Integer(default=4370)
    comm_password = fields.Char(
        string='Communication Key',
        help="The device's COMM key (Menu -> Comm. -> Security). 0 when unset.",
    )
    tcp_timeout = fields.Integer(string='Timeout (s)', default=10)
    force_udp = fields.Boolean(
        help='Older terminals only answer over UDP. Try this when TCP times out.',
    )
    ommit_ping = fields.Boolean(
        string='Skip Ping Check',
        help='Skip the reachability probe when ICMP is blocked on your network.',
    )
    auto_pull = fields.Boolean(
        string='Scheduled Pull', default=True,
        help='Let the scheduled action fetch punches from this device.',
    )

    check_option = fields.Selection([
        ('both', 'Check In and Check Out'),
        ('in', 'Check In only'),
        ('out', 'Check Out only'),
    ], required=True, default='both', tracking=True, help=(
        "Terminals installed at a single door often send only one direction. "
        "Forcing it here stops an entry-only reader from closing attendances."
    ))
    model_name = fields.Char(
        string='Device Model',
        help='Reported by the device on handshake when available '
             '(e.g. uFace800, K40, SpeedFace-V5L).',
    )
    firmware_version = fields.Char(readonly=True)
    device_tz = fields.Selection(
        selection=lambda self: [(tz, tz) for tz in pytz.all_timezones],
        string='Device Timezone', required=True, default='UTC', tracking=True,
        help='Timezone configured on the physical device. Punch times sent '
             'by the device are local to this timezone and are converted to '
             'UTC before being stored.',
    )
    active = fields.Boolean(
        default=True, tracking=True,
        help='Devices that register themselves are created inactive and '
             'must be activated by an attendance officer before their '
             'punches are accepted.',
    )
    company_id = fields.Many2one(
        'res.company', string='Company', index=True,
        default=lambda self: self.env.company,
    )
    last_seen = fields.Datetime(readonly=True, copy=False)
    is_online = fields.Boolean(compute='_compute_is_online', search='_search_is_online')
    attlog_stamp = fields.Char(default='None', copy=False, readonly=True,
                               help='Last ATTLOG stamp reported by the device.')
    operlog_stamp = fields.Char(default='None', copy=False, readonly=True)

    # Reported by the device in its OPTIONS payload.
    device_user_count = fields.Integer(string='Users on Device', readonly=True)
    device_fp_count = fields.Integer(string='Fingerprints on Device', readonly=True)
    device_face_count = fields.Integer(string='Faces on Device', readonly=True)
    device_log_count = fields.Integer(string='Punches on Device', readonly=True)
    device_ip = fields.Char(string='Device IP', readonly=True)

    log_ids = fields.One2many('zkteco.attendance.log', 'device_id', string='Punch Logs')
    user_ids = fields.One2many('zkteco.device.user', 'device_id', string='Device Users')
    command_ids = fields.One2many('zkteco.device.command', 'device_id', string='Commands')

    log_count = fields.Integer(compute='_compute_counts')
    punch_count_today = fields.Integer(compute='_compute_counts')
    user_count = fields.Integer(compute='_compute_counts')
    unmapped_user_count = fields.Integer(compute='_compute_counts')
    pending_command_count = fields.Integer(compute='_compute_counts')

    biometric_template_ids = fields.One2many(
        'zkteco.biometric.template', 'device_id', string='Biometric Data')
    template_count = fields.Integer(compute='_compute_counts')

    _serial_uniq = models.Constraint(
        'unique (serial_number)',
        'A device with this serial number already exists.',
    )

    @api.constrains('connection_mode', 'serial_number', 'ip_address')
    def _check_connection_settings(self):
        """Validate the connection settings for the ZKTeco device.
               Ensures that ADMS push mode has a serial number configured and that
               Direct IP mode has a device IP address configured."""
        for device in self:
            if device.connection_mode == 'adms' and not device.serial_number:
                raise ValidationError(_(
                    "%s uses ADMS push mode, which identifies the terminal by "
                    "its serial number. Fill in the Serial Number, or switch "
                    "to Direct IP.", device.display_name))
            if device.connection_mode == 'tcp' and not device.ip_address:
                raise ValidationError(_(
                    "%s uses Direct IP mode. Fill in the Device IP Address, or "
                    "switch to ADMS push.", device.display_name))

    # -------------------------------------------------------------
    # Computes
    # -------------------------------------------------------------
    @api.depends('last_seen')
    def _compute_is_online(self):
        """Compute whether the device is currently online.
                A device is considered online when its last communication time falls
                within the configured online threshold."""
        threshold = fields.Datetime.now() - timedelta(minutes=ONLINE_THRESHOLD_MINUTES)
        for device in self:
            device.is_online = bool(device.last_seen and device.last_seen >= threshold)

    def _search_is_online(self, operator, value):
        """Search devices based on their current online status.
                Converts the computed ``is_online`` condition into a domain based on
                the device's ``last_seen`` timestamp and the configured online threshold.
                :param operator: Search operator, such as ``=`` or ``!=``.
                :param value: Boolean value used to filter the online status.
                :return: Odoo search domain matching the requested online status."""
        threshold = fields.Datetime.now() - timedelta(minutes=ONLINE_THRESHOLD_MINUTES)
        online = (operator == '=' and value) or (operator == '!=' and not value)
        if online:
            return [('last_seen', '>=', threshold)]
        return ['|', ('last_seen', '=', False), ('last_seen', '<', threshold)]

    @api.depends('log_ids', 'user_ids', 'command_ids', 'biometric_template_ids')
    def _compute_counts(self):
        """Compute related record counts for each ZKTeco device.
                Calculates the total number of attendance logs, today's punch logs,
                device users, unmapped users, pending commands, and biometric templates
                associated with each device."""
        today_start = self._user_today_start()
        logs = dict(self.env['zkteco.attendance.log']._read_group(
            [('device_id', 'in', self.ids)], ['device_id'], ['__count'],
        ))
        logs_today = dict(self.env['zkteco.attendance.log']._read_group(
            [('device_id', 'in', self.ids), ('punch_time', '>=', today_start)],
            ['device_id'], ['__count'],
        ))
        users = dict(self.env['zkteco.device.user']._read_group(
            [('device_id', 'in', self.ids)], ['device_id'], ['__count'],
        ))
        unmapped = dict(self.env['zkteco.device.user']._read_group(
            [('device_id', 'in', self.ids), ('employee_id', '=', False)],
            ['device_id'], ['__count'],
        ))
        commands = dict(self.env['zkteco.device.command']._read_group(
            [('device_id', 'in', self.ids), ('state', '=', 'pending')],
            ['device_id'], ['__count'],
        ))
        templates = dict(self.env['zkteco.biometric.template']._read_group(
            [('device_id', 'in', self.ids)], ['device_id'], ['__count'],
        ))
        for device in self:
            device.template_count = templates.get(device, 0)
            device.log_count = logs.get(device, 0)
            device.punch_count_today = logs_today.get(device, 0)
            device.user_count = users.get(device, 0)
            device.unmapped_user_count = unmapped.get(device, 0)
            device.pending_command_count = commands.get(device, 0)

    def _user_today_start(self):
        """Midnight of the current user's day, as naive UTC."""
        user_tz = pytz.timezone(self.env.user.tz or 'UTC')
        now_local = pytz.utc.localize(fields.Datetime.now()).astimezone(user_tz)
        midnight = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        return midnight.astimezone(pytz.utc).replace(tzinfo=None)

    # -------------------------------------------------------------
    # Registration (called by the /iclock controller)
    # -------------------------------------------------------------
    @api.model
    def _get_or_register(self, serial_number):
        """Return the device for this serial, registering it if unknown.

        Returns None for a malformed serial or when the pending-approval
        quota is exhausted, so the controller can answer without touching
        the database any further.
        """
        if not serial_number or not SERIAL_RE.match(serial_number):
            return None
        Device = self.sudo().with_context(active_test=False)
        device = Device.search([('serial_number', '=', serial_number)], limit=1)
        if not device:
            pending = Device.search_count([('active', '=', False)])
            if pending >= MAX_PENDING_DEVICES:
                _logger.warning(
                    "ZKTeco ADMS: refusing to register %s, %s devices already "
                    "await approval", serial_number, pending)
                return None
            device = Device.create({
                'name': serial_number,
                'serial_number': serial_number,
                'active': False,
            })
            _logger.info("ZKTeco ADMS: auto-registered new device %s (inactive, "
                         "waiting for approval)", serial_number)
        return device

    def action_approve(self):
        """Activate a self-registered device and ask it for its user list."""
        for device in self.filtered(lambda d: not d.active):
            device.active = True
            device.message_post(body=_('Device approved; punches are now accepted.'))
            device._queue_command('DATA QUERY USERINFO')

    # -------------------------------------------------------------
    # ADMS protocol helpers
    # -------------------------------------------------------------
    def _device_time_to_utc(self, time_str):
        """Convert a device-local 'YYYY-MM-DD HH:MM:SS' string to naive UTC."""
        self.ensure_one()
        tz = pytz.timezone(self.device_tz or 'UTC')
        naive_local = datetime.strptime(time_str.strip(), '%Y-%m-%d %H:%M:%S')
        # is_dst=None would raise on ambiguous local times (the hour that
        # repeats when DST ends); prefer the standard-time reading instead
        # of dropping the punch.
        return tz.localize(naive_local, is_dst=False).astimezone(pytz.utc).replace(tzinfo=None)

    def _tz_offset_hours(self):
        """Device UTC offset in whole hours, for the TimeZone= option."""
        self.ensure_one()
        tz = pytz.timezone(self.device_tz or 'UTC')
        offset = pytz.utc.localize(fields.Datetime.now()).astimezone(tz).utcoffset()
        return int(offset.total_seconds() // 3600)

    def _handshake_response(self):
        """Configuration block returned to the device on GET /iclock/cdata."""
        self.ensure_one()
        return (
            f"GET OPTION FROM: {self.serial_number}\r\n"
            f"ATTLOGStamp={self.attlog_stamp or 'None'}\r\n"
            f"OPERLOGStamp={self.operlog_stamp or 'None'}\r\n"
            "ATTPHOTOStamp=None\r\n"
            "ErrorDelay=30\r\n"
            "Delay=10\r\n"
            "TransTimes=00:00;14:05\r\n"
            "TransInterval=1\r\n"
            "TransFlag=1111000000\r\n"
            f"TimeZone={self._tz_offset_hours()}\r\n"
            "Realtime=1\r\n"
            "Encrypt=None\r\n"
        )

    def _process_attlog(self, raw, stamp=None):
        """Parse an ATTLOG payload into raw punch logs.

        Each line is tab-separated:
        device_user_id  YYYY-MM-DD HH:MM:SS  status  verify_mode  [...]
        Returns the number of accepted (non-duplicate) lines.
        """
        self.ensure_one()
        Log = self.env['zkteco.attendance.log'].sudo()
        vals_list = []
        for line in (raw or '').splitlines():
            parts = self._split_attlog_line(line)
            if len(parts) < 2 or not parts[0]:
                continue
            try:
                punch_time = self._device_time_to_utc(parts[1])
            except ValueError:
                _logger.warning("ZKTeco %s: unparseable ATTLOG line %r", self.serial_number, line)
                continue
            vals_list.append({
                'device_id': self.id,
                'device_user_id': parts[0],
                'punch_time': punch_time,
                'status': parts[2] if len(parts) > 2 else '255',
                'verify_mode': parts[3] if len(parts) > 3 else False,
            })
        count = len(Log._create_deduplicated(vals_list))
        if stamp:
            self.attlog_stamp = stamp
        return count

    @staticmethod
    def _split_attlog_line(line):
        """Split one ATTLOG line into fields.

        Tabs are the documented separator, but several firmwares emit
        space-padded columns instead. The timestamp itself contains a space,
        so a plain whitespace split has to glue the date and time back
        together.
        """
        line = (line or '').strip()
        if not line:
            return []
        if '\t' in line:
            return [part.strip() for part in line.split('\t')]
        parts = line.split()
        if len(parts) >= 3:
            parts = [parts[0], f"{parts[1]} {parts[2]}"] + parts[3:]
        return parts

    def _process_operlog(self, raw, stamp=None):
        """Parse an OPERLOG payload; only USER lines are of interest.

        USER PIN=123\tName=John Doe\tPri=0\tPasswd=\tCard=123456\tGrp=1\t...
        """
        self.ensure_one()
        DeviceUser = self.env['zkteco.device.user'].sudo()
        count = 0
        for line in (raw or '').splitlines():
            line = line.strip()
            if not line.startswith('USER '):
                continue
            values = self._parse_kv_line(line[len('USER '):])
            pin = values.get('pin')
            if not pin:
                continue
            DeviceUser._register_from_device(self, pin, values)
            count += 1
        if stamp:
            self.operlog_stamp = stamp
        return count

    @staticmethod
    def _parse_kv_line(payload):
        """Parse a tab-separated 'Key=Value' ADMS chunk into a lowercase dict."""
        values = {}
        for chunk in payload.replace('\r', '\t').replace('\n', '\t').split('\t'):
            if '=' in chunk:
                key, val = chunk.split('=', 1)
                values[key.strip().lower()] = val.strip()
        return values

    def _process_options(self, raw):
        """Store the capability block a device posts as table=options.

        Sent on connect by most firmwares:
        ~DeviceName=uFace800\tFWVersion=Ver 6.60\tUserCount=42\t...
        """
        self.ensure_one()
        values = self._parse_kv_line((raw or '').replace('~', ''))
        if not values:
            return 0
        vals = {}
        model_name = values.get('devicename') or values.get('~devicename')
        if model_name and not self.model_name:
            vals['model_name'] = model_name[:64]
        firmware = values.get('fwversion') or values.get('firmware')
        if firmware:
            vals['firmware_version'] = firmware[:64]
        for key, field_name in (
            ('usercount', 'device_user_count'),
            ('fpcount', 'device_fp_count'),
            ('facecount', 'device_face_count'),
            ('transactioncount', 'device_log_count'),
        ):
            if values.get(key, '').isdigit():
                vals[field_name] = int(values[key])
        if values.get('ipaddress'):
            vals['device_ip'] = values['ipaddress'][:64]
        if vals:
            self.write(vals)
        return len(vals)

    def _pop_next_command(self):
        """Return the next pending command and mark it sent."""
        self.ensure_one()
        command = self.env['zkteco.device.command'].sudo().search([
            ('device_id', '=', self.id), ('state', '=', 'pending'),
        ], order='id', limit=1)
        if command:
            command.write({'state': 'sent', 'sent_at': fields.Datetime.now()})
        return command

    # -------------------------------------------------------------
    # Command queue actions
    # -------------------------------------------------------------
    def _queue_command(self, command):
        """Queue a command for the ZKTeco device.
                Creates a pending device command associated with the current device.
                :param command: Command string to be sent to the device.
                :return: Newly created ZKTeco device command record."""
        self.ensure_one()
        return self.env['zkteco.device.command'].sudo().create({
            'device_id': self.id,
            'command': command,
        })

    def _check_ready_for_commands(self):
        """Validate that devices are ready to receive queued commands.
                Ensures that selected devices use ADMS mode, where devices poll the
                server for queued commands, and verifies that all devices are active.
                Direct IP devices and inactive devices cannot process queued commands."""
        # The command queue only exists because ADMS devices poll for work.
        # A Direct IP device is driven synchronously and would never collect.
        pull_mode = self.filtered(lambda d: d.connection_mode != 'adms')
        if pull_mode:
            raise UserError(_(
                "These devices are in Direct IP mode and never poll for "
                "queued commands. Use the Direct IP buttons instead: %s",
                ', '.join(pull_mode.mapped('display_name'))))
        inactive = self.filtered(lambda d: not d.active)
        if inactive:
            raise UserError(_(
                "These devices are not approved yet, they will not poll for "
                "commands: %s", ', '.join(inactive.mapped('serial_number'))))

    def action_cmd_fetch_logs(self):
        """Queue a command to fetch attendance logs from the selected devices.
                Validates that the selected devices are ready to receive queued
                commands, then adds an attendance log retrieval command for each
                device."""
        self._check_ready_for_commands()
        for device in self:
            device._queue_command('DATA QUERY ATTLOG')

    def action_cmd_fetch_users(self):
        """Queue a command to fetch user information from the selected devices.
                Validates that the selected devices are ready to receive queued
                commands, then adds a user information retrieval command for each
                device."""
        self._check_ready_for_commands()
        for device in self:
            device._queue_command('DATA QUERY USERINFO')

    def action_cmd_device_info(self):
        """Queue a command to retrieve device information.
                Validates that the selected devices are ready to receive queued
                commands, then adds a device information retrieval command for each
                device."""
        self._check_ready_for_commands()
        for device in self:
            device._queue_command('INFO')

    def action_cmd_clear_attlog(self):
        """Queue a command to clear attendance logs from the selected devices.
                Validates that the selected devices are ready to receive queued
                commands, then adds a command to clear the attendance logs for each
                device."""
        self._check_ready_for_commands()
        for device in self:
            device._queue_command('CLEAR LOG')

    def action_cmd_reboot(self):
        """Queue a reboot command for the selected ZKTeco devices.
                Validates that the selected devices are ready to receive queued
                commands, then adds a reboot command for each device."""
        self._check_ready_for_commands()
        for device in self:
            device._queue_command('REBOOT')

    def action_cmd_sync_time(self):
        """Push the current time to the device clock."""
        self._check_ready_for_commands()
        for device in self:
            tz = pytz.timezone(device.device_tz or 'UTC')
            local = pytz.utc.localize(fields.Datetime.now()).astimezone(tz)
            device._queue_command(
                'SET OPTION DateTime=%d' % device._encode_datetime(local))

    def action_check_adms_setup(self):
        """Diagnose an ADMS device that is not reporting.

        Odoo cannot dial an ADMS terminal, so there is nothing to "test" in
        the Direct IP sense. What can be checked is the half Odoo owns: what
        the device has ever sent, and whether the /iclock route is reachable
        the way a terminal would reach it. The common failure is a site that
        only answers HTTPS, or redirects to it - ZKTeco firmware follows
        neither.
        """
        self.ensure_one()
        report = self._adms_diagnostics()
        self.message_post(body=Markup('<br/>').join(
            Markup('%s %s') % (line['icon'], line['text']) for line in report['lines']))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': report['title'],
                'message': '\n'.join(
                    f"{line['icon']} {line['text']}" for line in report['lines']),
                'type': report['level'],
                'sticky': True,
            },
        }

    def _adms_diagnostics(self):
        """Run diagnostics for the ADMS connection configuration.
                Checks whether the device has contacted Odoo, determines the server
                address and port configured through ``web.base.url``, provides the
                connection details required on the device, probes the ADMS endpoint,
                and detects potential HTTPS redirection issues.
                :return: Dictionary containing the diagnostic title, severity level,
                and detailed diagnostic messages."""
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or ''
        parsed = urlparse(base_url)
        host = parsed.hostname or ''
        is_https = parsed.scheme == 'https'
        port = parsed.port or (443 if is_https else 80)
        lines = []
        level = 'success'

        # 1. Has the terminal ever reached us?
        if not self.last_seen:
            lines.append({'icon': '❌', 'text': _(
                "This device has never contacted Odoo. Everything below is "
                "about why.")})
            level = 'danger'
        elif self.is_online:
            lines.append({'icon': '✅', 'text': _(
                "Device reported %s ago and is online.",
                fields.Datetime.now() - self.last_seen)})
        else:
            lines.append({'icon': '⚠️', 'text': _(
                "Last contact was %s. The device has stopped reporting.",
                self.last_seen)})
            level = 'warning'

        # 2. What to type on the keypad.
        if host in ('localhost', '127.0.0.1', '0.0.0.0', '::1'):
            # web.base.url defaults to whatever an admin last browsed from; a
            # loopback value means no device on the network can ever reach it.
            lines.append({'icon': '❌', 'text': _(
                "web.base.url is %(url)s, a loopback address. That only works "
                "on the Odoo server itself - a terminal on the network cannot "
                "reach it. Set the parameter to this server's LAN address "
                "(Settings -> Technical -> System Parameters -> web.base.url), "
                "and add web.base.url.freeze = True so Odoo stops overwriting "
                "it.", url=base_url)})
            level = 'danger'
        else:
            lines.append({'icon': '⚙️', 'text': _(
                "Set on the terminal (Comm. -> Cloud Server Setting): "
                "Server Address = %(host)s, Port = %(port)s, "
                "Enable Domain Name = %(domain)s.",
                host=host or _('<not configured>'), port=port,
                domain=_('OFF') if _IP_RE.match(host) else _('ON'))})

        # 3. Can a device actually speak to that address?
        probe = self._probe_iclock(base_url)
        lines.append(probe)
        if probe['level'] == 'danger':
            level = 'danger'
        elif probe['level'] == 'warning' and level != 'danger':
            level = 'warning'

        # 4. The HTTPS trap.
        if is_https:
            redirect = self._probe_iclock(f"http://{host}", expect_plain=True)
            lines.append(redirect)
            if redirect['level'] == 'danger':
                level = 'danger'

        titles = {'success': _("ADMS Setup OK"),
                  'warning': _("ADMS Setup Needs Attention"),
                  'danger': _("ADMS Setup Broken")}
        return {'title': titles[level], 'level': level, 'lines': lines}

    def _probe_iclock(self, base, expect_plain=False):
        """Ask our own /iclock endpoint the way a terminal would."""
        if not base:
            return {'icon': '❌', 'level': 'danger', 'text': _(
                "web.base.url is not set, so there is no address to give the "
                "device.")}
        url = f"{base.rstrip('/')}/iclock/cdata"
        try:
            response = requests.get(url, timeout=10, allow_redirects=False)
        except Exception as exc:  # noqa: BLE001 - any transport failure
            return {'icon': '❌', 'level': 'danger', 'text': _(
                "%(url)s is unreachable from the Odoo server itself "
                "(%(error)s).", url=url, error=exc)}

        if response.status_code in (301, 302, 303, 307, 308):
            target = response.headers.get('Location', '')
            return {'icon': '❌', 'level': 'danger', 'text': _(
                "%(url)s answers %(code)s redirect to %(target)s. ZKTeco "
                "firmware does not follow redirects, so the device gives up "
                "here. Serve /iclock/ over plain HTTP without a redirect, or "
                "put a plain-HTTP relay on the device's network.",
                url=url, code=response.status_code, target=target)}

        if response.status_code == 404:
            # A session-less request cannot pick a database on its own. With
            # several databases and no dbfilter, Odoo has nothing to route to
            # and drops public routes - which is indistinguishable from the
            # module not being installed until you look at both.
            return {'icon': '❌', 'level': 'danger', 'text': _(
                "%(url)s answers HTTP 404, so no controller matched. Usual "
                "causes, in order: this Odoo serves several databases and has "
                "no dbfilter/db_name set, so a device request (which carries "
                "no session) cannot be routed to a database; or the module is "
                "not installed on the database being served; or the server "
                "was not restarted after the module was added.", url=url)}

        if response.status_code != 200:
            return {'icon': '❌', 'level': 'danger', 'text': _(
                "%(url)s answers HTTP %(code)s. The device expects 200.",
                url=url, code=response.status_code)}

        if 'SN' not in (response.text or ''):
            return {'icon': '⚠️', 'level': 'warning', 'text': _(
                "%(url)s answers 200 but not with this module's reply. "
                "Something else is serving that path.", url=url)}

        if expect_plain:
            return {'icon': '✅', 'level': 'success', 'text': _(
                "Plain HTTP works on %s - point the device there.", url)}
        if url.startswith('https://'):
            return {'icon': '⚠️', 'level': 'warning', 'text': _(
                "%s answers correctly, but only over HTTPS. Most ZKTeco "
                "firmwares cannot do TLS; check for an HTTPS toggle on the "
                "terminal, and if there is none, put a plain-HTTP relay on "
                "the device's network.", url)}
        return {'icon': '✅', 'level': 'success', 'text': _(
            "%s is reachable and answering correctly.", url)}

    def action_reset_stamps(self):
        """Forget the resume markers so the device re-uploads everything.

        The terminal only sends records newer than the stamp it was last
        acknowledged with; clearing them is the way to pull history back after
        a timezone fix or a lost database. Re-sent punches are deduplicated.
        """
        self.write({'attlog_stamp': 'None', 'operlog_stamp': 'None'})
        for device in self:
            device.message_post(body=_('Sync stamps reset; the device will '
                                       're-upload its stored records.'))

    @staticmethod
    def _encode_datetime(dt):
        """ZKTeco packed timestamp used by 'SET OPTION DateTime='."""
        return ((((dt.year - 2000) * 12 * 31)
                 + ((dt.month - 1) * 31) + dt.day - 1)
                * (24 * 60 * 60)) + ((dt.hour * 60 + dt.minute) * 60) + dt.second

    # -------------------------------------------------------------
    # Crons
    # -------------------------------------------------------------
    @api.model
    def _cron_check_offline(self):
        """Log a note on devices that stopped reporting.

        Only devices that were seen at least once are considered, and only
        the transition is posted, so a device that stays offline over a
        weekend does not flood its chatter.
        """
        threshold = fields.Datetime.now() - timedelta(hours=1)
        devices = self.search([
            ('last_seen', '!=', False), ('last_seen', '<', threshold),
        ])
        for device in devices:
            last_note = self.env['mail.message'].search([
                ('model', '=', 'zkteco.device'), ('res_id', '=', device.id),
                ('body', 'like', 'ZKTECO_OFFLINE_NOTICE'),
            ], order='id desc', limit=1)
            if last_note and last_note.date >= device.last_seen:
                continue
            device.message_post(body=_(
                "<!-- ZKTECO_OFFLINE_NOTICE -->Device has not contacted the "
                "server since %s.", device.last_seen))

    # -------------------------------------------------------------
    # Smart button actions
    # -------------------------------------------------------------
    def action_view_logs(self):
        """Open the attendance punch logs associated with the device.
                 Returns an Odoo window action that displays the device's attendance
                 logs in list and form views."""
        self.ensure_one()
        return {
            'name': _('Punch Logs'),
            'type': 'ir.actions.act_window',
            'res_model': 'zkteco.attendance.log',
            'view_mode': 'list,form',
            'domain': [('device_id', '=', self.id)],
            'context': {'default_device_id': self.id},
        }

    def action_view_users(self):
        """Open the device users associated with the selected device.
                Returns an Odoo window action that displays the device users in
                list and form views."""
        self.ensure_one()
        return {
            'name': _('Device Users'),
            'type': 'ir.actions.act_window',
            'res_model': 'zkteco.device.user',
            'view_mode': 'list,form',
            'domain': [('device_id', '=', self.id)],
            'context': {'default_device_id': self.id},
        }

    def action_view_templates(self):
        """Open the biometric data associated with the selected device.
                Returns an Odoo window action that displays the device's biometric
                templates in list and form views."""
        self.ensure_one()
        return {
            'name': _('Biometric Data'),
            'type': 'ir.actions.act_window',
            'res_model': 'zkteco.biometric.template',
            'view_mode': 'list,form',
            'domain': [('device_id', '=', self.id)],
            'context': {'default_device_id': self.id},
        }

    def action_view_commands(self):
        """Open the commands associated with the selected device.
                Returns an Odoo window action that displays the device commands in
                list and form views."""
        self.ensure_one()
        return {
            'name': _('Commands'),
            'type': 'ir.actions.act_window',
            'res_model': 'zkteco.device.command',
            'view_mode': 'list,form',
            'domain': [('device_id', '=', self.id)],
            'context': {'default_device_id': self.id},
        }
