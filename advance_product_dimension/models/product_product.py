# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    """
    Extension of product.product to support dimension-based pricing.

    Features:
    ----------
    - Allows products to be priced based on quantity or dimensions.
    - Supports enabling/disabling dimensional values (Length, Width, Height).
    - Defines minimum and maximum allowed values for dimensions.
    """
    _inherit = 'product.product'

    price_calculation_based_on = fields.Selection(
        [
            ('based_on_quantity', 'Price Calculation Based on Quantity'),
            ('based_on_dimension', 'Price Calculation Based on Dimension'),
        ],
        string="Price Calculation Based On",
        default="based_on_quantity",
        required=True,
        help="Choose whether the product price is calculated based on quantity or dimensions."
    )
    use_dimensional_values = fields.Boolean(
        string='Use Dimensional Values',
        default=False,
        help="Enable to use Length, Width, and Height for price calculation."
    )
    uom_prompt_id = fields.Many2one(
        string="UOM Prompt",
        comodel_name="uom.uom",
        help="Select the Unit of Measure used for dimension validation."
    )

    length = fields.Boolean(
        string='Length',
        default=True,
        help="Enable if Length should be used for dimension-based pricing."
    )
    width = fields.Boolean(
        string='Width',
        default=True,
        help="Enable if Width should be used for dimension-based pricing."
    )
    height = fields.Boolean(
        string='Height',
        default=True,
        help="Enable if Height should be used for dimension-based pricing."
    )

    min_length = fields.Float(
        string="Minimum Length",
        default=0.0,
        help="The minimum allowed value for Length."
    )
    max_length = fields.Float(
        string="Maximum Length",
        default=0.0,
        help="The maximum allowed value for Length."
    )
    min_width = fields.Float(
        string="Minimum Width",
        default=0.0,
        help="The minimum allowed value for Width."
    )
    max_width = fields.Float(
        string="Maximum Width",
        default=0.0,
        help="The maximum allowed value for Width."
    )
    min_height = fields.Float(
        string="Minimum Height",
        default=0.0,
        help="The minimum allowed value for Height."
    )
    max_height = fields.Float(
        string="Maximum Height",
        default=0.0,
        help="The maximum allowed value for Height."
    )

    @api.onchange('price_calculation_based_on')
    def _onchange_price_calculation_based_on(self):
        """
        On change of price calculation method:
        - If based on dimensions → enable dimensional values.
        - Otherwise → disable dimensional values.
        """
        if self.price_calculation_based_on == 'based_on_dimension':
            self.use_dimensional_values = True
        else:
            self.use_dimensional_values = False

    @api.constrains(
        'price_calculation_based_on',
        'uom_prompt_id',
        'min_length',
        'max_length',
        'min_width',
        'max_width',
        'min_height',
        'max_height',
    )
    def _check_dimension_configuration(self):
        """Validate dimensional configuration only for dimension-based products."""
        for product in self:
            if product.price_calculation_based_on != 'based_on_dimension':
                continue
            if not product.uom_prompt_id:
                raise ValidationError("UOM Prompt is required for dimension-based pricing.")
            if product.min_length > product.max_length:
                raise ValidationError("Minimum Length cannot be greater than Maximum Length.")
            if product.min_width > product.max_width:
                raise ValidationError("Minimum Width cannot be greater than Maximum Width.")
            if product.min_height > product.max_height:
                raise ValidationError("Minimum Height cannot be greater than Maximum Height.")
