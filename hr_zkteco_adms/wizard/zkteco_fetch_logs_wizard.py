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
from datetime import datetime, time, timedelta

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ZktecoFetchLogsWizard(models.TransientModel):
    """Recover punches for a window that never made it into Odoo.

    A terminal that was offline, reset, or pointed at the wrong server still
    holds its records; this asks for them back. How the window is applied
    depends on the transport - see _fetch().
    """
    _name = 'zkteco.fetch.logs.wizard'
    _description = 'Fetch Missing Punch Logs'

    device_ids = fields.Many2many(
        'zkteco.device', string='Devices', required=True,
        default=lambda self: self._default_devices(),
    )
    date_from = fields.Date(
        string='From', required=True,
        default=lambda self: fields.Date.context_today(self) - timedelta(days=7),
    )
    date_to = fields.Date(
        string='To', required=True, default=fields.Date.context_today,
    )

    @api.model
    def _default_devices(self):
        """Return the default ZKTeco devices for the wizard.
                If the wizard is opened from one or more ZKTeco devices, use those
                devices as the default selection. Otherwise, no devices are selected."""
        if self.env.context.get('active_model') == 'zkteco.device':
            return self.env.context.get('active_ids', [])
        return []

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        """Validate that the fetch date range is in chronological order.
                Raises a UserError when the start date is later than the end date."""
        for wizard in self:
            if wizard.date_from > wizard.date_to:
                raise UserError(_("The start date is after the end date."))

    def _window_device_local(self, device):
        """Convert the requested days into the device's own wall clock.

        The user picks calendar days; a terminal only understands its local
        time, so the window has to be expressed there or a night shift at the
        edge of the range is silently cut off.
        """
        tz = pytz.timezone(device.device_tz or 'UTC')
        start = tz.localize(datetime.combine(self.date_from, time.min))
        end = tz.localize(datetime.combine(self.date_to, time.max))
        return start.replace(tzinfo=None), end.replace(tzinfo=None)

    def action_fetch(self):
        """Fetch attendance logs from the selected ZKTeco devices.
                TCP devices are queried directly and their attendance records are
                imported immediately. ADMS devices cannot be queried synchronously,
                so an attendance-log command is queued for the device's next poll.
                Displays a notification showing the number of imported punches and
                the devices waiting to deliver their records."""
        self.ensure_one()
        pulled = 0
        queued = self.env['zkteco.device']
        for device in self.device_ids:
            local_from, local_to = self._window_device_local(device)
            if device.connection_mode == 'tcp':
                # Odoo dials the device, so the punches are here on return.
                pulled += device._pull_attendance(
                    date_from=local_from, date_to=local_to)
            else:
                # ADMS cannot ask synchronously: queue the range and let the
                # terminal deliver it on its next poll.
                device._check_ready_for_commands()
                device._queue_command(
                    'DATA QUERY ATTLOG StartTime={start}\tEndTime={end}'.format(
                        start=local_from.strftime('%Y-%m-%d %H:%M:%S'),
                        end=local_to.strftime('%Y-%m-%d %H:%M:%S'),
                    ))
                queued |= device

        if queued and not pulled:
            message = _(
                "Requested from %s. The punches arrive on the device's next "
                "poll, usually within seconds.", ', '.join(queued.mapped('display_name')))
            notification_type = 'info'
        elif queued:
            message = _(
                "%(count)s punch(es) imported. %(devices)s will deliver theirs "
                "on the next poll.", count=pulled,
                devices=', '.join(queued.mapped('display_name')))
            notification_type = 'success'
        else:
            message = _("%s punch(es) imported.", pulled)
            notification_type = 'success' if pulled else 'warning'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Fetch Requested"),
                'message': message,
                'type': notification_type,
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
