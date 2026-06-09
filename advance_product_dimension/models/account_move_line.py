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


class AccountMoveLine(models.Model):
    """Extension of `account.move.line` to support dimension-based pricing
    (length × width × height) alongside standard quantity-based pricing."""
    _inherit = 'account.move.line'

    length = fields.Float(
        string='Length',
        digits='Product Unit of Measure',
        help="Length of the product line. Used in dimension-based pricing."
    )
    width = fields.Float(
        string='Width',
        digits='Product Unit of Measure',
        help="Width of the product line. Used in dimension-based pricing."
    )
    height = fields.Float(
        string='Height',
        digits='Product Unit of Measure',
        help="Height of the product line. Used in dimension-based pricing."
    )
    dimension_qty = fields.Float(
        string="Dimension Quantity",
        compute="_compute_dimension_qty",
        store=True,
        help="Automatically calculated as Length × Width × Height. "
             "Represents the effective quantity for dimension-based products."
    )

    @api.depends('product_id', 'product_id.price_calculation_based_on', 'length', 'width', 'height')
    def _compute_dimension_qty(self):
        """Compute the dimension quantity as the product of length, width, and height."""
        for record in self:
            if not record.product_id or record.product_id.price_calculation_based_on != 'based_on_dimension':
                record.dimension_qty = 0
                continue
            if not any((record.length, record.width, record.height)):
                record.dimension_qty = 0
                continue
            length = record.length if record.length != 0 else 1
            width = record.width if record.width != 0 else 1
            height = record.height if record.height != 0 else 1
            record.dimension_qty = length * width * height

    @api.depends(
        'product_id',
        'product_id.price_calculation_based_on',
        'quantity',
        'discount',
        'price_unit',
        'tax_ids',
        'currency_id',
        'dimension_qty',
    )
    def _compute_totals(self):
        """
        Compute the amounts of the invoice line based on dimension quantities and ensure proper tax-inclusive handling.
        """
        for line in self:
            if line.display_type != 'product':
                line.price_total = False
                line.price_subtotal = False
                continue

            if line.product_id and line.product_id.price_calculation_based_on == 'based_on_dimension':
                base_price = line.dimension_qty * line.price_unit
            else:
                base_price = line.price_unit

            discounted_price = base_price * (1 - (line.discount / 100.0))
            subtotal = line.quantity * discounted_price

            if line.tax_ids:
                tax_results = line.tax_ids.compute_all(
                    discounted_price,
                    quantity=line.quantity,
                    currency=line.currency_id,
                    product=line.product_id,
                    partner=line.partner_id,
                    is_refund=line.is_refund,
                )
                line.price_subtotal = tax_results['total_excluded']
                line.price_total = tax_results['total_included']
            else:
                line.price_total = subtotal
                line.price_subtotal = subtotal

    @api.onchange('length', 'width', 'height')
    def _onchange_validate_dimensions(self):
        """On-change validation for dimensions when editing invoice lines."""
        for record in self:
            if record.product_id:
                product = record.product_id

                if product.price_calculation_based_on == "based_on_quantity":
                    if record.length or record.width or record.height:
                        raise ValidationError(
                            "Dimensions cannot be set for this product as its price is calculated based on quantity.")

                if product.price_calculation_based_on == "based_on_dimension":
                    # Check Length
                    if product.min_length == 0 and product.max_length == 0:
                        if record.length != 0:
                            raise ValidationError("Length must be 0 as the allowed range is 0 to 0.")
                    elif record.length and (record.length < product.min_length or record.length > product.max_length):
                        uom_name = product.uom_prompt_id.name if product.uom_prompt_id else 'units'
                        raise ValidationError(
                            f"Length must be between {product.min_length} and {product.max_length} {uom_name}."
                        )
                    # Check Width
                    if product.min_width == 0 and product.max_width == 0:
                        if record.width != 0:
                            raise ValidationError("Width must be 0 as the allowed range is 0 to 0.")
                    elif record.width and (record.width < product.min_width or record.width > product.max_width):
                        uom_name = product.uom_prompt_id.name if product.uom_prompt_id else 'units'
                        raise ValidationError(
                            f"Width must be between {product.min_width} and {product.max_width} {uom_name}."
                        )
                    # Check Height
                    if product.min_height == 0 and product.max_height == 0:
                        if record.height != 0:
                            raise ValidationError("Height must be 0 as the allowed range is 0 to 0.")
                    elif record.height and (record.height < product.min_height or record.height > product.max_height):
                        uom_name = product.uom_prompt_id.name if product.uom_prompt_id else 'units'
                        raise ValidationError(
                            f"Height must be between {product.min_height} and {product.max_height} {uom_name}."
                        )

    @api.constrains('length', 'width', 'height')
    def _validate_dimensions_on_save(self):
        """Constraint validation on record save.

        Ensures that dimension-based products cannot have
        zero values for length, width, or height when
        the product defines non-zero min/max rules."""
        for record in self:
            if record.product_id:
                product = record.product_id
                # Check if the product is dimension-based
                if product.price_calculation_based_on == "based_on_dimension":
                    # Validate Length
                    if record.length == 0:
                        raise ValidationError(
                            "For dimension-based products, Length must be set and cannot be zero.")
                    # Validate Width
                    if record.width == 0:
                        raise ValidationError(
                            "For dimension-based products, Width must be set and cannot be zero.")
                    # Validate Height
                    if record.height == 0:
                        raise ValidationError(
                            "For dimension-based products, Height must be set and cannot be zero.")
