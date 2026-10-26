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
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FleetVehicleModel(models.Model):
    """Inherit fleet.vehicle.model to add a vehicle type"""
    _inherit = 'fleet.vehicle.model'

    vehicle_type = fields.Selection(selection_add=[('truck', 'Truck')],
                                    ondelete={'truck': 'set default'},
                                    help='Select the type of the vehicle.'
                                         ' For trucks, choose "Truck".')
    truck_type_id = fields.Many2one('truck.type',
                                    help='Select truck type.')

    @api.constrains('vehicle_type', 'truck_type_id')
    def _check_truck_type(self):
        """Validate truck type when vehicle type is truck"""
        for record in self:
            if record.vehicle_type == 'truck' and not record.truck_type_id:
                raise ValidationError(self.env._("Truck Type is required when vehicle type is 'Truck'."))
