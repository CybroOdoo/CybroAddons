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


class PropelleCity(models.Model):
    """City covered by the brokerage, used to locate the listings."""
    _name = 'propelle.city'
    _description = 'Property City'
    _order = 'sequence, name'

    name = fields.Char(
        string='City', required=True, translate=True,
        help='Name of the city, shown in the search and the filters.')
    state_code = fields.Char(
        string='State or Region Code',
        help='Short code of the state or region, shown after the city name '
             '(for example CA).')
    sequence = fields.Integer(
        string='Display Order', default=10,
        help='Order of the city in the search and the filters.')
    active = fields.Boolean(
        string='Active City', default=True,
        help='Archived cities are hidden from the website.')
    property_ids = fields.One2many(
        'propelle.property', 'city_id', string='Properties',
        help='Listings located in this city.')
    property_count = fields.Integer(
        string='Number of Listings', compute='_compute_property_count',
        help='Number of listings located in this city.')

    @api.depends('name', 'state_code')
    def _compute_display_name(self):
        """Show the state code after the city name, as on the website."""
        for city in self:
            city.display_name = ', '.join(
                part for part in (city.name, city.state_code) if part)

    @api.depends('property_ids')
    def _compute_property_count(self):
        """Count the listings of each city."""
        for city in self:
            city.property_count = len(city.property_ids)
