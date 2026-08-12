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

from odoo import fields, models


class FleetVehicleFeature(models.Model):
    """Vehicle Rental Feature."""
    _name = 'fleet.vehicle.feature'
    _description = 'Vehicle Rental Feature'

    name = fields.Char(string="Feature Name", required=True, translate=True,
                       help='Name of the feature.')
    icon = fields.Char(string="FontAwesome Icon",
                       help="e.g. fa-wifi, fa-snowflake")
    color = fields.Integer(string="Color Index", default=0,
                           help='Color code index.')

