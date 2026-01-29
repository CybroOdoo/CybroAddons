# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class CarTypes(models.Model):
    """Car types model"""
    _name = "car.types"
    _description = "Car Types"

    name = fields.Char(
        string="Name",
        help="Enter the type or category of the car,"
             " e.g., Sedan, SUV, Coupe, etc.")
    image = fields.Image(
        string="Image",
        help="Upload an image representing the car type. "
             "This could be an icon or a picture.")
    car_count = fields.Integer(
        string="Car count",
        help="This field displays the total count of cars "
             "associated with this car type.",
        compute='_compute_car_count')

    def _compute_car_count(self):
        """Product count fetching based on car type"""
        for record in self:
            record.car_count = self.env['product.template'].search_count(
                [('car_type', '=', record.id)])

    def action_view_products(self):
        """Product smart button"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Products',
            'view_mode': 'tree',
            'res_model': 'product.template',
            'domain': [('car_type', '=', self.id)],
            'context': "{'create': False}"
        }
