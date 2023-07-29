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
# This program is distributed in the hope that it will be useful,
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


class VehicleDetails(models.Model):
    """Details of a Vehicle"""
    _name = 'vehicle.details'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'vehicle_id'
    _description = 'Vehicle Details'

    vehicle_id = fields.Many2one('fleet.vehicle', string='vehicle',
                                 tracking=True, required=True,
                                 help='Name of vehicle')
    partner_id = fields.Many2one('res.partner', string='Owner',
                                 tracking=True, help=' Name of Partner')
    number_plate = fields.Char(string='Number Plate', tracking=True,
                               required=True, help='Number for the vehicle')
    ownership_type = fields.Selection([('outsider', 'Outsider'), ('member',
                                                                  'Member')],
                                      string='Ownership type', tracking=True,
                                      required=True, help='Type of the owner '
                                                          'of vehicle')
