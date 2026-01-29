# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies (<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER General Public License (LGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER General Public License for more details.
#
#    You should have received a copy of the GNU LESSER General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherit the configuration settings to add fields."""
    _inherit = 'res.config.settings'

    pro_internal_ref = fields.Boolean(
        string='Product Internal Ref', help="Internal reference of products",
        config_parameter='product_internal_ref_generator.pro_internal_ref')
    auto_generate_internal_ref = fields.Boolean(
        string='Auto Generate Product Internal Ref',
        help="To auto generate the product internal reference.",
        config_parameter='product_internal_ref_generator.auto_generate_'
                         'internal_ref')
    product_name_config = fields.Boolean(
        string='Product Name Config', help="Name of the product config",
        config_parameter='product_internal_ref_generator.product_name_config')
    pro_name_digit = fields.Integer(
        string='Product Name Digit', help="Number of digit of product name",
        config_parameter='product_internal_ref_generator.pro_name_digit')
    pro_name_separator = fields.Char(
        string='Product Name Separator', help="Separator for product name",
        config_parameter='product_internal_ref_generator.pro_name_separator')
    pro_template_config = fields.Boolean(
        string='Product Attribute Config',
        help="To add the product attribute config",
        config_parameter='product_internal_ref_generator.pro_template_config')
    pro_template_digit = fields.Integer(
        string='Product Attribute Digit',
        help="Number of digit of product attribute",
        config_parameter='product_internal_ref_generator.pro_template_digit')
    pro_template_separator = fields.Char(
        string='Product Attribute Separator',
        help="Separator for product attribute",
        config_parameter="product_internal_ref_generator.pro_template_"
                         "separator")
    pro_categ_config = fields.Boolean(
        string='Product Category Config', help="To add product category",
        config_parameter="product_internal_ref_generator.pro_categ_config")
    pro_categ_digit = fields.Integer(
        string='Product Category Digit',
        help="Number of product category digit",
        config_parameter='product_internal_ref_generator.pro_categ_digit')
    pro_categ_separator = fields.Char(
        string='Product Category Separator',
        help="Separator for product category",
        config_parameter='product_internal_ref_generator.pro_categ_separator')
