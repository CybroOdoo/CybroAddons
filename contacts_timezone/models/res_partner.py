# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
###############################################################################

import logging
import pytz
from odoo import api, fields, models
from datetime import datetime
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder


_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    contact_local_time_tz = fields.Char(
        string="Local Time",readonly=True,
        help="Local Time based on address"
    )
    contact_local_tz = fields.Selection(
        lambda self: [(tz, tz) for tz in
                      sorted(pytz.all_timezones, key=lambda tz: tz if not tz.startswith('Etc/') else '_')],
        string='Timezone',
        compute='_get_timezone_from_address',
        store=True,
        help="Timezone based on address"
    )

    def action_compute_contact_local_time_tz(self):
        """Compute the local time based on the contact's timezone."""
        for record in self:
            if record.contact_local_tz:
                try:
                    # Get the timezone and compute the local time
                    tz = pytz.timezone(record.contact_local_tz)
                    local_time = datetime.now(tz)
                    local_time_naive = local_time.replace(tzinfo=None)
                    record.contact_local_time_tz = local_time_naive
                except Exception as e:
                    record.contact_local_time_tz = False
                    _logger.exception(f"Error computing local time for {record.name}: {e}")

            else:
                record.contact_local_time_tz = False

    @api.depends('country_id', 'state_id', 'street', 'city')
    def _get_timezone_from_address(self):
        """Compute the timezone based on the partner's address."""
        for record in self:
            record.contact_local_tz = False
            # Prepare address for geolocation
            address = f"{record.state_id.name or ''}, {record.country_id.name or ''}"
            geolocator = Nominatim(user_agent="odoo_timezone_app")
            tz_finder = TimezoneFinder()
            try:
                # Get location from address
                location = geolocator.geocode(address)
                if location:
                    # Get timezone based on latitude and longitude
                    tz_str = tz_finder.timezone_at(lat=location.latitude, lng=location.longitude)
                    if tz_str:
                        record.contact_local_tz = tz_str
            except Exception as e:
                _logger.exception(f"Error retrieving timezone for {record.name}: {e}")
                record.contact_local_tz = False
