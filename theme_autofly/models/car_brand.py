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
from odoo import api, fields, models


class CarBrand(models.Model):
    """Creating the new car brand"""
    _name = "car.brand"
    _description = "Car brand"

    name = fields.Char(
        string="Name",
        help="Enter the name of the car brand. "
             "For example, 'Toyota', 'Ford', etc.",)
    image = fields.Image(
        string="Image",
        help="Upload the image of the car brand. "
             "This can be the brand logo or any relevant image.")

    @api.model
    def get_brands(self):
        """RPC function returning car details"""
        brands = self.sudo().search([])
        types = self.env['car.types'].sudo().search([])
        car_brands = [{'brand_name': brand.name, 'brand_id': brand.id} for brand in brands]
        car_types = [{'car_type': type.name, 'type_id': type.id} for type in types]
        return {'brand': car_brands, 'type': car_types}
