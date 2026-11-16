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
"""Settings of the product internal reference generator."""
from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .product_product import DEFAULT_DIGIT, DEFAULT_SEPARATOR


class ResConfigSettings(models.TransientModel):  # pylint: disable=abstract-method
    """Add the product internal reference options to the settings."""
    _inherit = 'res.config.settings'

    auto_generate_internal_ref = fields.Boolean(
        string='Auto Generate Product Internal Ref',
        help="Automatically generate the internal reference of new "
             "products and variants.",
        config_parameter='product_internal_ref_generator.'
                         'auto_generate_internal_ref')
    product_name_config = fields.Boolean(
        help="Add the first characters of the product name to the "
             "internal reference.",
        config_parameter='product_internal_ref_generator.product_name_config')
    pro_name_digit = fields.Integer(
        string='Product Name Digit', default=DEFAULT_DIGIT,
        help="Number of characters taken from the product name.",
        config_parameter='product_internal_ref_generator.pro_name_digit')
    pro_name_separator = fields.Char(
        string='Product Name Separator', default=DEFAULT_SEPARATOR,
        help="Separator added after the product name part.",
        config_parameter='product_internal_ref_generator.pro_name_separator')
    pro_template_config = fields.Boolean(
        string='Product Attribute Config',
        help="Add the first characters of the attribute values to the "
             "internal reference.",
        config_parameter='product_internal_ref_generator.pro_template_config')
    pro_template_digit = fields.Integer(
        string='Product Attribute Digit', default=DEFAULT_DIGIT,
        help="Number of characters taken from each attribute value.",
        config_parameter='product_internal_ref_generator.pro_template_digit')
    pro_template_separator = fields.Char(
        string='Product Attribute Separator', default=DEFAULT_SEPARATOR,
        help="Separator added after each attribute value part.",
        config_parameter='product_internal_ref_generator.'
                         'pro_template_separator')
    pro_categ_config = fields.Boolean(
        string='Product Category Config',
        help="Add the first characters of the product category to the "
             "internal reference.",
        config_parameter='product_internal_ref_generator.pro_categ_config')
    pro_categ_digit = fields.Integer(
        string='Product Category Digit', default=DEFAULT_DIGIT,
        help="Number of characters taken from the product category name.",
        config_parameter='product_internal_ref_generator.pro_categ_digit')
    pro_categ_separator = fields.Char(
        string='Product Category Separator', default=DEFAULT_SEPARATOR,
        help="Separator added after the product category part.",
        config_parameter='product_internal_ref_generator.pro_categ_separator')

    @api.constrains('product_name_config', 'pro_name_digit',
                    'pro_categ_config', 'pro_categ_digit',
                    'pro_template_config', 'pro_template_digit')
    def _check_internal_ref_digits(self):
        """An enabled part must take at least one character."""
        for rec in self:
            for enabled, digit, label in (
                    (rec.product_name_config, rec.pro_name_digit,
                     self.env._("Product Name Digit")),
                    (rec.pro_categ_config, rec.pro_categ_digit,
                     self.env._("Product Category Name Digit")),
                    (rec.pro_template_config, rec.pro_template_digit,
                     self.env._("Attribute Name Digit"))):
                if enabled and digit < 1:
                    raise ValidationError(self.env._(
                        "%(label)s must be at least 1.", label=label))
