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


class PurchaseOrderLine(models.Model):
    """
        Inherit Purchase Order Line to support dimension-based pricing.

        This extension allows products to be priced based on dimensions
        (Length, Width, Height) instead of only quantity.
        It validates dimension constraints (min/max), computes a
        dimension quantity (volume/area/length), and integrates
        this into Odoo's purchase order line price calculation.
    """
    _inherit = 'purchase.order.line'

    length = fields.Float(
        string='Length',
        digits='Product Unit of Measure',
        help="Length of the product in the unit of measure. "
             "Used for dimension-based price calculation."
    )
    width = fields.Float(
        string='Width',
        digits='Product Unit of Measure',
        help="Width of the product in the unit of measure. "
             "Used for dimension-based price calculation."
    )
    height = fields.Float(
        string='Height',
        digits='Product Unit of Measure',
        help="Height of the product in the unit of measure. "
             "Used for dimension-based price calculation."
    )
    dimension_qty = fields.Float(
        string="Dimension Qty",
        compute="_compute_dimension_qty",
        store=True,
        help="Computed dimension quantity based on length × width × height. "
             "If any dimension is zero, it is treated as 1."
    )

    def _get_dimension_values_from_procurement(self, values):
        """Extract dimension values from procurement values."""
        return {
            'length': values.get('length', 0.0),
            'width': values.get('width', 0.0),
            'height': values.get('height', 0.0),
            'dimension_qty': values.get('dimension_qty', 0.0),
        }

    @api.depends('product_id', 'product_id.price_calculation_based_on', 'length', 'width', 'height')
    def _compute_dimension_qty(self):
        """
                Compute the dimension quantity as the product of length, width, and height.
                If any dimension is 0, treat it as 1 for the calculation.
                """
        for record in self:
            product = record.product_id
            if not product or product.price_calculation_based_on != 'based_on_dimension':
                record.dimension_qty = 0
            elif not any((record.length, record.width, record.height)):
                record.dimension_qty = 0
            else:
                length = record.length if record.length != 0 else 1
                width = record.width if record.width != 0 else 1
                height = record.height if record.height != 0 else 1

                record.dimension_qty = length * width * height

    @api.depends(
        'product_id',
        'product_id.price_calculation_based_on',
        'product_qty',
        'price_unit',
        'taxes_id',
        'discount',
        'dimension_qty',
    )
    def _compute_amount(self):
        """
        Compute the amounts of the PO line based on dimension quantities and include proper tax calculations.
        """
        for line in self:
            if line.display_type:
                line.price_subtotal = 0.0
                line.price_tax = 0.0
                line.price_total = 0.0
                continue

            if line.product_id and line.product_id.price_calculation_based_on == 'based_on_dimension':
                base_price = line.dimension_qty * line.price_unit
            else:
                base_price = line.price_unit
            discounted_price = base_price * (1 - line.discount / 100.0)

            taxes = line.taxes_id.compute_all(
                discounted_price,
                line.order_id.currency_id,
                line.product_qty,
                product=line.product_id,
                partner=line.partner_id,
            ) if line.taxes_id else False

            if taxes:
                line.price_subtotal = taxes['total_excluded']
                line.price_tax = taxes['total_included'] - taxes['total_excluded']
                line.price_total = taxes['total_included']
            else:
                line.price_subtotal = line.product_qty * discounted_price
                line.price_tax = 0.0
                line.price_total = line.price_subtotal

    @api.onchange('length', 'width', 'height')
    def _onchange_validate_dimensions(self):
        """
            Validate dimensions when modified in the form:
            - Prevent entering dimensions for quantity-based products.
            - Enforce min/max constraints for dimension-based products.
        """
        for record in self:
            product = record.product_id
            if not product:
                continue

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
        """
            Validate dimension values when saving:
            - For dimension-based products, all dimensions must be set (non-zero)
            if product has min/max constraints.
        """
        for record in self:
            product = record.product_id
            if not product or product.price_calculation_based_on != "based_on_dimension":
                continue
            if record.length == 0:
                raise ValidationError("For dimension-based products, Length must be set and cannot be zero.")
            if record.width == 0:
                raise ValidationError("For dimension-based products, Width must be set and cannot be zero.")
            if record.height == 0:
                raise ValidationError("For dimension-based products, Height must be set and cannot be zero.")

    def _prepare_account_move_line(self, move=False):
        """Carry dimensions to vendor bills created from purchase orders."""
        values = super()._prepare_account_move_line(move=move)
        values.update({
            'length': self.length,
            'width': self.width,
            'height': self.height,
            'dimension_qty': self.dimension_qty,
        })
        return values

    @api.model
    def _prepare_purchase_order_line_from_procurement(self, product_id, product_qty, product_uom, company_id, values, po):
        """Copy dimensions from procurement values to generated purchase lines."""
        line_values = super()._prepare_purchase_order_line_from_procurement(
            product_id, product_qty, product_uom, company_id, values, po
        )
        line_values.update(self._get_dimension_values_from_procurement(values))
        return line_values

    def _find_candidate(self, product_id, product_qty, product_uom, location_id, name, origin, company_id, values):
        """Avoid merging procurements that carry different dimension values."""
        lines = self
        if any(key in values for key in ('length', 'width', 'height', 'dimension_qty')):
            lines = lines.filtered(
                lambda line: line.length == values.get('length', 0.0)
                and line.width == values.get('width', 0.0)
                and line.height == values.get('height', 0.0)
                and line.dimension_qty == values.get('dimension_qty', 0.0)
            )
        return super(PurchaseOrderLine, lines)._find_candidate(
            product_id, product_qty, product_uom, location_id, name, origin, company_id, values
        )
