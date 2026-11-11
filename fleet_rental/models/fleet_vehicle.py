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
from odoo import fields, models


class EmployeeFleet(models.Model):
    """Inherit fleet.vehicle"""
    _inherit = 'fleet.vehicle'

    rental_check_availability = fields.Boolean(
        default=True, copy=False, help="Rental availability of the fleet.",
    )
    color = fields.Char(default='#FFFFFF', help="Color of the fleet")
    rental_reserved_time = fields.One2many(
        comodel_name='rental.fleet.reserved',
        inverse_name='reserved_obj_id',
        string='Reserved Time',
        help='Reserved rental time',
        readonly=True,
    )
    fuel_type = fields.Selection(
        selection_add=[('petrol', 'Petrol')],
        help='Fuel Used by the vehicle',
    )

    _vin_sn_unique = models.Constraint(
        'unique (vin_sn)',
        "Chassis Number already exists!",
    )
    _license_plate_unique = models.Constraint(
        'unique (license_plate)',
        "License plate already exists!",
    )
