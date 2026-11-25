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

from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)

# Terminals sold outside the Latin world still ship names in a legacy
# codepage; try the common ones before giving up on the byte stream.
BODY_ENCODINGS = ('utf-8', 'gbk', 'cp1252', 'latin-1')


class ZktecoAdmsController(http.Controller):
    """ZKTeco ADMS (iclock) push protocol endpoints.

    The device is configured with this server's host/port (Comm. -> Cloud
    Server Setting / ADMS) and then talks plain-text HTTP:

    - GET  /iclock/cdata?SN=...&options=all   handshake, server returns config
    - POST /iclock/cdata?SN=...&table=ATTLOG  punch records, one per line
    - POST /iclock/cdata?SN=...&table=OPERLOG operation log + USER records
    - POST /iclock/cdata?SN=...&table=options device capabilities and firmware
    - GET  /iclock/getrequest?SN=...          device polls for queued commands
    - POST /iclock/devicecmd                  device reports command results

    All endpoints are public (the device cannot authenticate) and are gated
    by the device serial number: unknown serials are auto-registered as
    inactive devices and ignored until an attendance officer activates them.
    """

    # -------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------
    def _plain(self, body):
        """Create a plain-text HTTP response.
                :param body: Text content to include in the HTTP response.
                :return: HTTP response with a ``text/plain`` content type."""
        return request.make_response(body, [('Content-Type', 'text/plain')])

    def _get_raw_body(self):
        """Return the raw request body as text.

        Devices send plain-text payloads, but some firmwares label them
        with a form content-type; werkzeug then consumes the body into
        `form` before the controller runs and get_data() comes back empty.
        In that case rebuild the payload from the parsed form pairs (ADMS
        lines contain at most one '=' per key=value chunk, so this is
        lossless for ATTLOG/OPERLOG/devicecmd bodies).
        """
        raw = request.httprequest.get_data()
        if raw:
            for encoding in BODY_ENCODINGS:
                try:
                    return raw.decode(encoding)
                except UnicodeDecodeError:
                    continue
            return raw.decode('utf-8', errors='replace')
        if request.httprequest.form:
            return '\n'.join(
                f"{key}={value}" if value else key
                for key, value in request.httprequest.form.items(multi=True)
            )
        return ''

    def _get_device(self, serial_number):
        """Resolve (and touch) the device behind this request."""
        device = request.env['zkteco.device'].sudo()._get_or_register(serial_number)
        if device:
            device.last_seen = fields.Datetime.now()
        return device

    # -------------------------------------------------------------
    # Endpoints
    # -------------------------------------------------------------
    @http.route('/iclock/cdata', type='http', auth='public', csrf=False,
                methods=['GET', 'POST'], save_session=False)
    def iclock_cdata(self, **kw):
        """Handle attendance data requests from ZKTeco devices.
                Retrieves the device using its serial number (SN), validates whether
                the device exists and is active, and returns an appropriate response.
                Inactive devices receive an ``OK`` response to prevent repeated retries,
                while their data is ignored until the device is approved.
                :param kw: Request parameters, including the device serial number (SN).
                :return: HTTP response indicating the request status."""
        device = self._get_device(kw.get('SN'))
        if not device:
            return self._plain('ERROR: unknown or invalid SN')
        if not device.active:
            # Answer OK so the device does not retry in a tight loop, but
            # ignore its data until an officer approves it.
            return self._plain('OK')

        if request.httprequest.method == 'GET':
            return self._plain(device._handshake_response())

        raw = self._get_raw_body()
        table = (kw.get('table') or '').upper()
        count = 0
        try:
            if table == 'ATTLOG':
                count = device._process_attlog(raw, stamp=kw.get('Stamp'))
            elif table == 'OPERLOG':
                count = device._process_operlog(raw, stamp=kw.get('Stamp'))
            elif table == 'OPTIONS':
                count = device._process_options(raw)
            else:
                # ATTPHOTO, BIODATA, rtdata and friends: acknowledged and
                # dropped, they carry no attendance information.
                _logger.debug("ZKTeco ADMS %s: unhandled table %s",
                              device.serial_number, table)
        except Exception:  # noqa: BLE001
            # Always answer OK: a non-200/err response makes the device
            # retransmit forever. Failures stay visible in the server log.
            _logger.exception("ZKTeco ADMS %s: failed to process %s payload",
                              device.serial_number, table)
        return self._plain(f"OK: {count}")

    @http.route('/iclock/getrequest', type='http', auth='public', csrf=False,
                methods=['GET', 'POST'], save_session=False)
    def iclock_getrequest(self, **kw):
        """Handle command requests from ZKTeco attendance devices.
                Retrieves the device using its serial number (SN), verifies that the
                device is active, updates its firmware information when provided, and
                returns the next pending command queued for the device. If no command
                is available, an ``OK`` response is returned.
                :param kw: Request parameters, including the device serial number (SN)
                and optional firmware information (INFO).
                :return: HTTP response containing the next device command or ``OK``."""
        device = self._get_device(kw.get('SN'))
        if not device or not device.active:
            return self._plain('OK')
        # Device may report info as query params on some firmwares.
        if kw.get('INFO') and not device.firmware_version:
            device.firmware_version = kw['INFO'][:64]
        command = device._pop_next_command()
        if command:
            return self._plain(f"C:{command.id}:{command.command}")
        return self._plain('OK')

    @http.route('/iclock/devicecmd', type='http', auth='public', csrf=False,
                methods=['POST'], save_session=False)
    def iclock_devicecmd(self, **kw):
        """Process command execution responses from ZKTeco attendance devices.
                Retrieves the device using its serial number (SN), parses the raw request
                body for command response data, and updates the corresponding device
                command with its execution status and return code. Invalid, missing, or
                mismatched command records are ignored.
                :param kw: Request parameters, including the device serial number (SN).
                :return: HTTP response indicating successful request processing."""
        device = self._get_device(kw.get('SN'))
        if not device or not device.active:
            return self._plain('OK')
        raw = self._get_raw_body()
        Command = request.env['zkteco.device.command'].sudo()
        # Body lines like: ID=12&Return=0&CMD=DATA
        for line in raw.replace('\r', '\n').split('\n'):
            line = line.strip()
            if not line or 'ID=' not in line:
                continue
            values = dict(
                chunk.split('=', 1) for chunk in line.split('&') if '=' in chunk
            )
            command_id = values.get('ID')
            if not command_id or not command_id.isdigit():
                continue
            command = Command.browse(int(command_id)).exists()
            if not command or command.device_id != device:
                continue
            return_code = values.get('Return', '')
            command.write({
                'state': 'done' if return_code == '0' else 'error',
                'return_code': return_code,
            })
        return self._plain('OK')

    @http.route(['/iclock/registry', '/iclock/ping', '/iclock/push',
                 '/iclock/rtdata', '/iclock/fdata', '/iclock/edata',
                 '/iclock/querydata', '/iclock/getfile'],
                type='http', auth='public', csrf=False,
                methods=['GET', 'POST'], save_session=False)
    def iclock_misc(self, **kw):
        """Auxiliary endpoints some firmwares call; keep them happy.

        They carry template, photo and file transfers that Odoo has no use
        for. Answering OK stops the device from retrying them forever, and
        the SN lookup still refreshes its last-seen timestamp.
        """
        self._get_device(kw.get('SN'))
        return self._plain('OK')
