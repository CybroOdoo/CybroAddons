# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Busthana Shirin (odoo@cybrosys.com)
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
#############################################################################
import pytz
from datetime import datetime
from odoo import api, fields, models
from odoo.addons.base.models.res_partner import _tz_get


class SystrayWorldClockConfig(models.Model):
    """A model representing the configuration of a world clock in the systray.
    """
    _name = 'systray.world.clock.config'
    _description = 'Systray World Clock Configuration'

    name = fields.Char(string='Location', required=True,
                       help='Location associated with this clock.')
    tz = fields.Selection(_tz_get, required=True, string='Timezone',
                          help='Timezone of the clock.')
    offset = fields.Float(string="Offset",
                          help='The time difference between the timezone and '
                               'UTC, in hours.')

    @api.onchange('tz')
    def _onchange_tz(self):
        """Calculate the time offset between the selected timezone and UTC.
        This method is called automatically whenever the timezone field is
        changed.
        """
        if self.tz:
            utc_dt = pytz.utc.localize(datetime.utcnow())
            tz = pytz.timezone(self.tz)
            local_dt = utc_dt.astimezone(tz)
            self.offset = local_dt.utcoffset().total_seconds() / 3600
