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
#   This program is distributed in the hope that it will be useful,
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


class SlotType(models.Model):
    """Details of slot type"""
    _name = 'slot.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'vehicle_type'
    _description = 'Slot Type'

    vehicle_type = fields.Char(string='Name', required=True,
                               tracking=True, help='Name of vehicle')
    code = fields.Char(string='Code', tracking=True,
                       help='Unique identifier for vehicle')
    allowed_park_duration = fields.Float(string='Allowed Parking Time',
                                         help='Time allowed for the vehicle')
