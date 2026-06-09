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

from odoo import Command, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    """Extend sale order lines with dimension fields and dimension pricing."""
    _inherit = 'sale.order.line'

    length = fields.Float(string='Length', digits='Product Unit of Measure')
    width = fields.Float(string='Width', digits='Product Unit of Measure')
    height = fields.Float(string='Height', digits='Product Unit of Measure')
    dimension_qty = fields.Float(
        string="Dimension Qty",
        compute="_compute_dimension_qty",
        store=True
    )

    def _get_dimension_method(self):
        """Infer the active dimension method from entered values."""
        self.ensure_one()
        active_dimensions = [
            name for name in ('length', 'width', 'height')
            if getattr(self, name) > 0
        ]
        methods = {
            ('length',): 'length',
            ('width',): 'width',
            ('height',): 'height',
            ('length', 'width'): 'length_width',
            ('width', 'height'): 'width_height',
            ('length', 'height'): 'length_height',
            ('length', 'width', 'height'): 'length_width_height',
        }
        return methods.get(tuple(active_dimensions), False)

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
        'product_uom_qty',
        'discount',
        'price_unit',
        'tax_id',
        'dimension_qty',
    )
    def _compute_amount(self):
        """
        Compute the amounts of the SO line based on dimension quantities and ensure proper tax-inclusive handling.
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

            if line.tax_id:
                taxes = line.tax_id.compute_all(
                    discounted_price,
                    currency=line.order_id.currency_id,
                    quantity=line.product_uom_qty,
                    product=line.product_id,
                    partner=line.order_id.partner_shipping_id,
                )
                line.price_subtotal = taxes['total_excluded']
                line.price_tax = taxes['total_included'] - taxes['total_excluded']
                line.price_total = taxes['total_included']
            else:
                line.price_subtotal = line.product_uom_qty * discounted_price
                line.price_tax = 0.0
                line.price_total = line.price_subtotal

    @api.onchange('length', 'width', 'height')
    def _onchange_validate_dimensions(self):
        """Validate dimension entry while editing the sale order line."""
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
        """Validate dimension values when saving a sale order line."""
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

    def _prepare_invoice_line(self, **optional_values):
        """Prepare the values to create the new invoice line for a sales order line.

        :param optional_values: any parameter that should be added to the returned invoice line
        :rtype: dict
        """
        self.ensure_one()
        res = {
            'display_type': self.display_type or 'product',
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'length': self.length,
            'width': self.width,
            'height': self.height,
            'dimension_qty': self.dimension_qty,
            'quantity': self.qty_to_invoice,
            'discount': self.discount,
            'price_unit': self.price_unit,
            'tax_ids': [Command.set(self.tax_id.ids)],
            'sale_line_ids': [Command.link(self.id)],
            'is_downpayment': self.is_downpayment,
        }
        self._set_analytic_distribution(res, **optional_values)
        if optional_values:
            res.update(optional_values)
        if self.display_type:
            res['account_id'] = False
        return res

    def _prepare_procurement_values(self, group_id=False):
        """Propagate dimensions to downstream purchase/manufacturing procurements."""
        values = super()._prepare_procurement_values(group_id=group_id)
        self.ensure_one()
        values.update({
            'length': self.length,
            'width': self.width,
            'height': self.height,
            'dimension_qty': self.dimension_qty,
            'dimension_method': self._get_dimension_method(),
        })
        return values
