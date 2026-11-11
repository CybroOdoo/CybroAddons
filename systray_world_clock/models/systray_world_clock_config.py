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
from datetime import UTC, datetime

import pytz

from odoo import api, fields, models

from odoo.addons.base.models.res_partner import _tz_get


class SystrayWorldClockConfig(models.Model):
    """ A model representing the configuration of a world clock in the systray. """
    _name = 'systray.world.clock.config'
    _description = 'Systray World Clock Configuration'

    name = fields.Char(string='Location', required=True,
                       help='Location associated with this clock.')
    tz = fields.Selection(_tz_get, required=True, string='Timezone',
                          help='Timezone of the clock.')
    offset = fields.Float(
        compute='_compute_offset',
        store=True,
        readonly=False,
        help='The time difference between the timezone and UTC, in hours.',
    )

    @api.depends('tz')
    def _compute_offset(self):
        """Calculate the time offset between the selected timezone and UTC."""
        utc_dt = datetime.now(UTC)
        for record in self:
            if record.tz:
                tz = pytz.timezone(record.tz)
                local_dt = utc_dt.astimezone(tz)
                record.offset = local_dt.utcoffset().total_seconds() / 3600
            else:
                record.offset = 0.0

    @api.onchange('tz')
    def _onchange_tz(self):
        """Calculate the time offset when timezone is modified in the UI."""
        self._compute_offset()
