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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class FlightAerodrome(models.Model):
    """Manage flight aerodromes."""
    _name = 'flight.aerodrome'
    _description = 'Aerodrome'
    _order = 'name'

    name = fields.Char(string='Name', required=True, help='Name of the aerodrome')
    icao_code = fields.Char(string='ICAO Code', size=4, help='Four-letter ICAO location indicator')
    iata_code = fields.Char(string='IATA Code', size=3, help='Three-letter IATA airport code')
    city = fields.Char(string='City', help='City where the aerodrome is located')
    country_id = fields.Many2one('res.country', string='Country', help='Country where the aerodrome is located')
    timezone = fields.Selection(
        selection='_get_timezone_selection',
        string='Timezone',
        help='Timezone of the aerodrome',
    )
    latitude = fields.Float(string='Latitude', digits=(10, 6), help='Geographical latitude of the aerodrome')
    longitude = fields.Float(string='Longitude', digits=(10, 6), help='Geographical longitude of the aerodrome')
    active = fields.Boolean(default=True, help='Set active to false to hide the aerodrome')
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True, help='Display name of the aerodrome')

    @api.model
    def _get_timezone_selection(self):
        """Return the available timezone selections."""
        import pytz
        return [(tz, tz) for tz in sorted(pytz.all_timezones)]

    @api.depends('name', 'icao_code')
    def _compute_display_name(self):
        """Compute the aerodrome display name."""
        for aerodrome in self:
            aerodrome.display_name = (
                f"[{aerodrome.icao_code}] {aerodrome.name}" if aerodrome.icao_code else aerodrome.name
            )

    _sql_icao_unique = models.Constraint(
        'unique(icao_code)',
        'An aerodrome with this ICAO code already exists.',
    )