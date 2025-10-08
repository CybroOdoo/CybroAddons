# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models


class PropertyNearbyConnectivity(models.Model):
    """A class for the model property.nearby.connectivity to represent
    the nearby connectives for a property"""
    _name = 'property.nearby.connectivity'
    _description = 'Property Nearby Connectivity'

    name = fields.Char(string="Name", required=True,
                       help='Name of the nearby connectivity for the property')
    direction = fields.Selection([('north', 'North'), ('south', 'South'),
                                  ('east', 'East'), ('west', 'West')],
                                 string='Direction',
                                 help='To which direction is the nearby '
                                      'connectivity')
    kilometer = fields.Float(string="Kilometer", required=True,
                             help='The distance between the property and '
                                  'nearby connectivity in kilometers')
    property_id = fields.Many2one('property.property',
                                  string="Property Name",
                                  help='The related property')
