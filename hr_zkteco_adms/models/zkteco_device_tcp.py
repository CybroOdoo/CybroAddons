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
"""Direct IP (pull) transport.

The ADMS side of this module never dials the terminal: the device pushes and
Odoo answers. That fails when a terminal has no route out - an isolated
factory VLAN, a firmware whose Cloud Server menu is missing, or a site that
simply wants attendance on demand instead of on a poll.

This mixin adds the other direction, over ZKTeco's binary TCP/UDP protocol
(port 4370) via pyzk. It needs the device to hold a reachable, stable IP and
Odoo to sit on the same network - the exact tradeoff ADMS exists to avoid,
which is why both modes live side by side on one device record.
"""
import base64
import logging
from contextlib import contextmanager
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from zk import ZK
except ImportError:  # pragma: no cover - optional dependency
    ZK = None


class ZktecoDeviceTcp(models.AbstractModel):
    _name = 'zkteco.device.tcp'
    _description = 'ZKTeco Direct IP Transport'

    # -------------------------------------------------------------
    # Connection
    # -------------------------------------------------------------
    def _check_tcp_ready(self):
        """Validate that the device is ready for Direct IP communication.
                Ensures that the ``pyzk`` package is installed, the device is configured
                for Direct IP (TCP) mode, and a valid IP address has been provided.
                Raises a user error if any required configuration is missing."""
        self.ensure_one()
        if ZK is None:
            raise UserError(_(
                "Direct IP mode needs the 'pyzk' python package.\n\n"
                "Install it on the Odoo server:  pip install pyzk"))
        if self.connection_mode != 'tcp':
            raise UserError(_(
                "%s is configured for ADMS push mode. Switch its Connection "
                "Mode to Direct IP to talk to it over TCP.", self.display_name))
        if not self.ip_address:
            raise UserError(_("Set the IP address of %s first.", self.display_name))

    @contextmanager
    def _zk_session(self, disable_device=False):
        """Open a pyzk connection, always releasing the terminal afterwards.

        `disable_device` freezes the keypad for the duration. It is what the
        vendor SDK does around bulk reads, and it is why the disconnect must
        happen even when the body raises: a terminal left disabled stops
        accepting punches until someone reboots it.
        """
        self._check_tcp_ready()
        zk = ZK(
            self.ip_address,
            port=self.port or 4370,
            timeout=self.tcp_timeout or 10,
            password=int(self.comm_password or 0),
            force_udp=self.force_udp,
            ommit_ping=self.ommit_ping,
        )
        connection = None
        try:
            connection = zk.connect()
            if disable_device:
                connection.disable_device()
            yield connection
        except UserError:
            raise
        except Exception as exc:  # noqa: BLE001 - pyzk raises bare exceptions
            _logger.warning("ZKTeco %s: TCP session failed: %s", self.display_name, exc)
            raise UserError(_(
                "Could not talk to %(device)s at %(host)s:%(port)s.\n\n%(error)s",
                device=self.display_name, host=self.ip_address,
                port=self.port or 4370, error=exc)) from exc
        finally:
            if connection:
                try:
                    if disable_device:
                        connection.enable_device()
                    connection.disconnect()
                except Exception:  # noqa: BLE001
                    _logger.warning("ZKTeco %s: unclean disconnect",
                                    self.display_name, exc_info=True)

    def action_test_connection(self):
        """Ping the terminal and adopt whatever it tells us about itself."""
        self.ensure_one()
        with self._zk_session() as connection:
            serial = connection.get_serialnumber()
            vals = {
                'firmware_version': (connection.get_firmware_version() or '')[:64],
                'model_name': self.model_name or (connection.get_device_name() or '')[:64],
                'last_seen': fields.Datetime.now(),
            }
            if serial and not self.serial_number:
                vals['serial_number'] = serial[:64]
            try:
                vals['device_user_count'] = connection.users or 0
                vals['device_log_count'] = connection.records or 0
                vals['device_fp_count'] = connection.fingers or 0
            except Exception:  # noqa: BLE001 - counters are best effort
                pass
            self.write(vals)
            device_time = connection.get_time()

        self.message_post(body=_(
            "Connection tested: firmware %(firmware)s, device clock %(clock)s.",
            firmware=self.firmware_version or _('unknown'),
            clock=device_time or _('unknown')))
        return self._notify(
            _("Connected"),
            _("%(device)s answered at %(host)s.",
              device=self.display_name, host=self.ip_address),
            'success')

    def _notify(self, title, message, notification_type='info'):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': notification_type,
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    # -------------------------------------------------------------
    # Pulling
    # -------------------------------------------------------------
    def action_pull_users(self):
        """Fetch and synchronize users from the selected ZKTeco devices.
                Pulls the latest device user information for each selected device and
                displays a success notification after the synchronization is completed.
                :return: Odoo client action displaying a success notification."""
        for device in self:
            device._pull_users()
        return self._notify(_("Users Fetched"), _("Device users are up to date."), 'success')

    def _pull_users(self):
        """Fetch and synchronize users from the ZKTeco device.
                Connects to the device through a ZKTeco session, retrieves the registered
                users, and creates or updates the corresponding device user records in
                Odoo. The device user count is also updated after synchronization.
                :return: Number of users retrieved from the device."""
        self.ensure_one()
        DeviceUser = self.env['zkteco.device.user'].sudo()
        with self._zk_session(disable_device=True) as connection:
            users = connection.get_users()
        for user in users:
            DeviceUser._register_from_device(self, str(user.user_id), {
                'name': user.name or '',
                'card': str(user.card) if user.card else '',
                'pri': str(user.privilege),
                'uid': user.uid,
            })
        self.device_user_count = len(users)
        return len(users)

    def action_pull_attendance(self):
        """Fetch and import attendance punches from the selected ZKTeco devices.
                Retrieves attendance records from each selected device, imports the
                punches into Odoo, and displays a notification with the total number
                of imported punches.
                :return: Odoo client action displaying the import result."""
        total = 0
        for device in self:
            total += device._pull_attendance()
        return self._notify(
            _("Punches Fetched"),
            _("%s new punch(es) imported.", total),
            'success' if total else 'info')

    def _pull_attendance(self, date_from=None, date_to=None):
        """Read the terminal's stored punches into raw logs.

        pyzk hands back every record the device holds; the date window is
        applied here rather than on the wire because the protocol has no
        server-side filter. Deduplication makes a repeated full read cheap
        in rows, if not in transfer.
        """
        self.ensure_one()
        with self._zk_session(disable_device=True) as connection:
            records = connection.get_attendance() or []

        vals_list = []
        for record in records:
            timestamp = record.timestamp
            if not isinstance(timestamp, datetime):
                continue
            if date_from and timestamp < date_from:
                continue
            if date_to and timestamp > date_to:
                continue
            vals_list.append({
                'device_id': self.id,
                'device_user_id': str(record.user_id),
                # The terminal reports its own wall clock, same as ATTLOG.
                'punch_time': self._device_time_to_utc(
                    timestamp.strftime('%Y-%m-%d %H:%M:%S')),
                'status': str(record.punch),
                'verify_mode': str(record.status),
            })
        created = self.env['zkteco.attendance.log'].sudo()._create_deduplicated(vals_list)
        self.last_seen = fields.Datetime.now()
        return len(created)

    def action_pull_biometrics(self):
        """Fetch and synchronize biometric data from the selected devices.
                Retrieves fingerprint, face, and card biometric data from each selected
                ZKTeco device and imports the data into Odoo. Displays a success
                notification after the synchronization is completed.
                :return: Odoo client action displaying a success notification."""
        for device in self:
            device._pull_biometrics()
        return self._notify(
            _("Biometric Data Fetched"),
            _("Fingerprint, face and card data imported."), 'success')

    def _pull_biometrics(self):
        """Store enrolment blobs so a replacement terminal can be reseeded."""
        self.ensure_one()
        Template = self.env['zkteco.biometric.template'].sudo()
        DeviceUser = self.env['zkteco.device.user'].sudo()

        with self._zk_session(disable_device=True) as connection:
            users = connection.get_users()
            templates = connection.get_templates() or []

        users_by_pin = {}
        for user in users:
            users_by_pin[str(user.user_id)] = DeviceUser._register_from_device(
                self, str(user.user_id), {
                    'name': user.name or '',
                    'card': str(user.card) if user.card else '',
                    'pri': str(user.privilege),
                    'uid': user.uid,
                })

        count = 0
        for template in templates:
            device_user = users_by_pin.get(str(template.uid)) or \
                DeviceUser.search([('device_id', '=', self.id),
                                   ('device_uid', '=', template.uid)], limit=1)
            if not device_user:
                continue
            payload = template.template
            vals = {
                'device_id': self.id,
                'device_user_id': device_user.id,
                'template_type': 'finger',
                'finger_index': template.fid,
                'template_data': base64.b64encode(payload).decode() if payload else False,
                'size': len(payload or b''),
                'valid': bool(template.valid),
            }
            existing = Template.search([
                ('device_user_id', '=', device_user.id),
                ('template_type', '=', 'finger'),
                ('finger_index', '=', template.fid),
            ], limit=1)
            if existing:
                existing.write(vals)
            else:
                Template.create(vals)
            count += 1

        # Cards live on the user record, not in the template list.
        for pin, device_user in users_by_pin.items():
            if not device_user.card:
                continue
            existing = Template.search([
                ('device_user_id', '=', device_user.id),
                ('template_type', '=', 'card'),
                ('finger_index', '=', -1),
            ], limit=1)
            vals = {
                'device_id': self.id,
                'device_user_id': device_user.id,
                'template_type': 'card',
                'finger_index': -1,
                'card_number': device_user.card,
            }
            if existing:
                existing.write(vals)
            else:
                Template.create(vals)
        return count

    def action_sync_now(self):
        """Users then punches, the order a fresh terminal needs."""
        for device in self:
            device._pull_users()
            device._pull_attendance()
        return self._notify(_("Synchronised"), _("Users and punches imported."), 'success')

    # -------------------------------------------------------------
    # Pushing
    # -------------------------------------------------------------
    def action_tcp_sync_time(self):
        """Synchronize the device clock with the server time.
                Connects to each selected Direct IP device and updates its clock using
                the current server date and time. Displays a success notification after
                the synchronization is completed.
                :return: Odoo client action displaying a success notification."""
        for device in self:
            with device._zk_session() as connection:
                connection.set_time(datetime.now())
        return self._notify(_("Clock Synced"), _("Device clock set from the server."), 'success')

    def _tcp_set_user(self, device_user):
        """Create or update one user on the terminal."""
        self.ensure_one()
        name = (device_user.employee_id.name or device_user.name or '')[:24]
        with self._zk_session(disable_device=True) as connection:
            connection.set_user(
                uid=device_user.device_uid or None,
                name=name,
                privilege=int(device_user.privilege or 0),
                password='',
                group_id='',
                user_id=str(device_user.user_pin),
                card=int(device_user.card) if (device_user.card or '').isdigit() else 0,
            )

    def _tcp_delete_user(self, device_user):
        """Delete a user from the ZKTeco device using Direct IP mode.
                Connects to the device and removes the specified device user using
                the user's PIN.
                :param device_user: Device user record to be deleted.
                :return: None."""
        self.ensure_one()
        with self._zk_session(disable_device=True) as connection:
            connection.delete_user(user_id=str(device_user.user_pin))

    def action_tcp_reboot(self):
        """Reboot the selected ZKTeco devices through Direct IP mode.
                Establishes a connection to each selected device and sends a restart
                command. Displays a success notification after the reboot command is
                sent.
                :return: Odoo client action displaying a success notification."""
        for device in self:
            with device._zk_session() as connection:
                connection.restart()
        return self._notify(_("Rebooting"), _("Restart sent to the device."), 'success')

    def action_tcp_clear_attendance(self):
        """Clear attendance logs stored on the selected ZKTeco devices.
                Connects to each device using Direct IP mode, clears the attendance
                records stored on the device, and posts a message on the device record.
                Attendance punches that have already been imported into Odoo are not
                affected.
                :return: Odoo client action displaying a warning notification."""
        for device in self:
            with device._zk_session(disable_device=True) as connection:
                connection.clear_attendance()
            device.message_post(body=_('Attendance storage cleared on the device.'))
        return self._notify(
            _("Device Logs Cleared"),
            _("Punches already imported into Odoo are untouched."), 'warning')

    # -------------------------------------------------------------
    # Cron
    # -------------------------------------------------------------
    @api.model
    def _cron_pull_tcp_devices(self):
        """Poll every Direct IP device; one bad terminal must not stop the rest."""
        devices = self.env['zkteco.device'].search([
            ('connection_mode', '=', 'tcp'),
            ('auto_pull', '=', True),
            ('ip_address', '!=', False),
        ])
        for device in devices:
            try:
                with self.env.cr.savepoint():
                    device._pull_attendance()
            except Exception as exc:  # noqa: BLE001
                _logger.warning("ZKTeco %s: scheduled pull failed: %s",
                                device.display_name, exc)
