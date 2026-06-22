# -*- coding: utf-8 -*-
#############################################################################
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
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class EmployeeFleet(models.Model):
    """
    Inherits fleet.vehicle to add availability tracking and reservation history.
    """
    _inherit = 'fleet.vehicle'

    is_rental_check_availability = fields.Boolean(
        string='Is Available', default=True, copy=False,
        help="Whether the vehicle is available for rental")
    color = fields.Char(string='Color', default='#FFFFFF',
                        help="Color of the vehicle")
    rental_reserved_time = fields.One2many('rental.fleet.reserved',
                                           'reserved_obj_id',
                                           string='Reserved Time',
                                           help='Reserved rental time',
                                           readonly=True)
    fuel_type = fields.Selection([('gasoline', 'Gasoline'),
                                  ('diesel', 'Diesel'),
                                  ('electric', 'Electric'),
                                  ('hybrid', 'Hybrid'),
                                  ('petrol', 'Petrol')],
                                 string='Fuel Type',
                                 help='Fuel Used by the vehicle')
    _sql_constraints = [('vin_sn_unique', 'unique (vin_sn)',
                         "Chassis Number already exists !"),
                        ('license_plate_unique', 'unique (license_plate)',
                         "License plate already exists !")]
