# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class ProductTemplate(models.Model):
    """Inheriting product_product model to add new fields."""
    _inherit = "product.template"

    popular_product = fields.Boolean(string="Popular Product",
                                     help="Please enable this field to make the"
                                          "product as popular product.")
    car_type_id = fields.Many2one('car.types', string="Car Type",
                                  help="Add your car type.")
    car_brand_id = fields.Many2one('car.brand', string="Car Brand",
                                   help="Add your car brand.")
    car_model = fields.Integer(string="Model", help="Add your car model.")
    location = fields.Char(help="Add your car location.")
