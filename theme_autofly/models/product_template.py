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


class ProductTemplate(models.Model):
    """Inherits the products"""
    _inherit = "product.template"

    popular_product = fields.Boolean(
        string="Popular Product",
        help="Check this box if the product is considered popular.")
    car_type = fields.Many2one(
        'car.types',
        string="Car Type",
        help="Select the type or category of "
             "the car associated with this product.")
    car_brand = fields.Many2one(
        'car.brand',
        string="Car Brand",
        help="Select the brand of the car associated with this product.")
    car_model = fields.Char(
        string="Model",
        help="Enter the model or variant of "
             "the car associated with this product.")
    location = fields.Char(
        string="Location",
        help="Enter the location information related to this product. "
             "This could be a showroom or warehouse location.")
