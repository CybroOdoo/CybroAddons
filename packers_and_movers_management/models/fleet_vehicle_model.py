# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
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


class FleetVehicle(models.Model):
    """Inherit fleet.vehicle.model to add a vehicle type"""
    _inherit = 'fleet.vehicle.model'

    vehicle_type = fields.Selection(selection_add=[('truck', 'Truck')],
                                    ondelete={'truck': 'cascade'},
                                    help='Select the type of the vehicle.'
                                         ' For trucks, choose "Truck".')
    truck_type_id = fields.Many2one('truck.type', string='Truck Type',
                                    required=True, help='Select truck type')
