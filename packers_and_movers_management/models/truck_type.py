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


class TruckType(models.Model):
    """Add new menu truck_type model in the fleet model to select truck type"""
    _name = 'truck.type'
    _description = 'Truck Type'

    name = fields.Char(string='Truck Type', required=True,
                       help='Truck type name')
    length = fields.Float(string='Length', help='Length of the container')
    width = fields.Float(string='Width', help='Width of the container')
    height = fields.Float(string='Height', help='Height of the container')
    capacity = fields.Float(string='House Hold Capacity', required=True,
                            help='Suitable for house size')
    weight = fields.Float(string='Max Weight', required=True,
                          help='Max Load of container')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.user.company_id.id,
        help='Select the company to which this record belongs.')
    unit = fields.Selection(selection=[('kg', 'KG'), ('tons', 'Tons')],
                            default='kg', help='Select unit', string="Unit")
