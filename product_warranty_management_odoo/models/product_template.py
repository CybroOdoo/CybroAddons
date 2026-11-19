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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    """Add the warranty settings to products."""
    _inherit = 'product.template'

    is_warranty_available = fields.Boolean(
        string='Warranty Available',
        help='Enable if this product is sold with a warranty.')
    warranty_duration = fields.Integer(
        string='Warranty Duration (Months)',
        help='Number of months the warranty is valid from the order date.')

    @api.constrains('is_warranty_available', 'warranty_duration')
    def _check_warranty_duration(self):
        """Require a positive duration for products with a warranty."""
        for product in self:
            if product.warranty_duration < 0 or (
                    product.is_warranty_available
                    and not product.warranty_duration):
                raise ValidationError(self.env._(
                    'The warranty duration of %(product)s must be greater '
                    'than zero.', product=product.display_name))
