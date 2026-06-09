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


class MrpProduction(models.Model):
    """Extend manufacturing orders with dimensions and dimension-aware costing."""
    _inherit = 'mrp.production'

    # Dimension fields
    length = fields.Float(
        string='Length (Mt.)',
        digits='Product Unit of Measure',
        default=0.0,
        help="Enter the length of the product in meters. Used for dimension-based pricing."
    )

    width = fields.Float(
        string='Width (Mt.)',
        digits='Product Unit of Measure',
        default=0.0,
        help="Enter the width of the product in meters. Used for dimension-based pricing."
    )

    height = fields.Float(
        string='Height (Mt.)',
        digits='Product Unit of Measure',
        default=0.0,
        help="Enter the height of the product in meters. Used for dimension-based pricing."
    )

    dimension_qty = fields.Float(
        string="Mt.12",
        compute="_compute_dimension_qty",
        store=True,
        digits='Product Unit of Measure',
        help="Automatically calculated as Length × Width × Height. "
             "Represents the effective dimension quantity used in pricing."
    )

    dimension_method = fields.Selection([
        ('length', 'Length'),
        ('width', 'Width'),
        ('height', 'Height'),
        ('length_width', 'Length x Width'),
        ('width_height', 'Width x Height'),
        ('length_height', 'Length x Height'),
        ('length_width_height', 'Length x Width x Height')
    ],
        string='Dimension Method',
        default='length_width_height',
        help="Choose how to calculate the dimension quantity (e.g., Length, "
             "Length x Width, or Length x Width x Height)."
    )

    show_dimension_fields = fields.Boolean(
        string="Show Dimension Fields",
        compute="_compute_show_dimension_fields",
        store=False,
        help="Shows or hides Length, Width, and Height fields for this product."
    )

    @api.depends('product_id')
    def _compute_show_dimension_fields(self):
        """Show dimension fields only for dimension-based products."""
        for record in self:
            if record.product_id and record.product_id.price_calculation_based_on == 'based_on_dimension':
                record.show_dimension_fields = True
            else:
                record.show_dimension_fields = False

    @api.depends('product_id', 'product_id.price_calculation_based_on', 'length', 'width', 'height', 'dimension_method')
    def _compute_dimension_qty(self):
        """Compute the dimension quantity based on the selected dimension method."""
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

            if record.dimension_method == 'length':
                record.dimension_qty = length
            elif record.dimension_method == 'width':
                record.dimension_qty = width
            elif record.dimension_method == 'height':
                record.dimension_qty = height
            elif record.dimension_method == 'length_width':
                record.dimension_qty = length * width
            elif record.dimension_method == 'width_height':
                record.dimension_qty = width * height
            elif record.dimension_method == 'length_height':
                record.dimension_qty = length * height
            elif record.dimension_method == 'length_width_height':
                record.dimension_qty = length * width * height
            else:
                record.dimension_qty = length * width * height

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Override to handle dimension-based products when product changes."""
        res = super()._onchange_product_id()

        if self.product_id:
            if (hasattr(self.product_id, 'price_calculation_based_on') and
                    self.product_id.price_calculation_based_on == "based_on_dimension"):
                if not self.dimension_method:
                    self.dimension_method = 'length_width_height'
                if not self.length:
                    self.length = 0.0
                if not self.width:
                    self.width = 0.0
                if not self.height:
                    self.height = 0.0
            else:
                self.length = 0.0
                self.width = 0.0
                self.height = 0.0
                self.dimension_method = False

        return res

    @api.onchange('length', 'width', 'height')
    def _onchange_validate_dimensions(self):
        """Validate dimensions when they are changed."""
        for record in self:
            if record.product_id:
                product = record.product_id

                if not hasattr(product, 'price_calculation_based_on'):
                    continue

                if product.price_calculation_based_on == "based_on_quantity":
                    if record.length or record.width or record.height:
                        raise ValidationError(
                            "Dimensions cannot be set for this product as its price is calculated based on quantity.")

                if product.price_calculation_based_on == "based_on_dimension":
                    if (hasattr(product, 'min_length') and hasattr(product, 'max_length') and
                            product.min_length == 0 and product.max_length == 0):
                        if record.length != 0:
                            raise ValidationError("Length must be 0 as the allowed range is 0 to 0.")
                    elif (record.length and hasattr(product, 'min_length') and hasattr(product, 'max_length') and
                          (record.length < product.min_length or record.length > product.max_length)):
                        uom_name = product.uom_prompt_id.name if hasattr(product,
                                                                         'uom_prompt_id') and product.uom_prompt_id else 'units'
                        raise ValidationError(
                            f"Length must be between {product.min_length} and {product.max_length} {uom_name}."
                        )
                    if (hasattr(product, 'min_width') and hasattr(product, 'max_width') and
                            product.min_width == 0 and product.max_width == 0):
                        if record.width != 0:
                            raise ValidationError("Width must be 0 as the allowed range is 0 to 0.")
                    elif (record.width and hasattr(product, 'min_width') and hasattr(product, 'max_width') and
                          (record.width < product.min_width or record.width > product.max_width)):
                        uom_name = product.uom_prompt_id.name if hasattr(product,
                                                                         'uom_prompt_id') and product.uom_prompt_id else 'units'
                        raise ValidationError(
                            f"Width must be between {product.min_width} and {product.max_width} {uom_name}."
                        )
                    if (hasattr(product, 'min_height') and hasattr(product, 'max_height') and
                            product.min_height == 0 and product.max_height == 0):
                        if record.height != 0:
                            raise ValidationError("Height must be 0 as the allowed range is 0 to 0.")
                    elif (record.height and hasattr(product, 'min_height') and hasattr(product, 'max_height') and
                          (record.height < product.min_height or record.height > product.max_height)):
                        uom_name = product.uom_prompt_id.name if hasattr(product,
                                                                         'uom_prompt_id') and product.uom_prompt_id else 'units'
                        raise ValidationError(
                            f"Height must be between {product.min_height} and {product.max_height} {uom_name}."
                        )

    @api.constrains('length', 'width', 'height')
    def _validate_dimensions_on_save(self):
        """Validate dimensions when the record is saved."""
        for record in self:
            if record.product_id:
                product = record.product_id
                if not hasattr(product, 'price_calculation_based_on'):
                    continue
                if product.price_calculation_based_on == "based_on_dimension":
                    if not record.dimension_method:
                        raise ValidationError("Please select a Dimension Method for dimension-based products.")

                    if record.dimension_method in ['length', 'length_width', 'length_height', 'length_width_height']:
                        if record.length == 0:
                            raise ValidationError(
                                "For dimension-based products, Length must be set and cannot be zero.")
                    if record.dimension_method in ['width', 'length_width', 'width_height', 'length_width_height']:
                        if record.width == 0:
                            raise ValidationError(
                                "For dimension-based products, Width must be set and cannot be zero.")
                    if record.dimension_method in ['height', 'width_height', 'length_height', 'length_width_height']:
                        if record.height == 0:
                            raise ValidationError(
                                "For dimension-based products, Height must be set and cannot be zero.")

    def _get_move_raw_values(self, product_id, product_uom_qty, product_uom, operation_id=False, bom_line=False):
        """
        Override to adjust raw material quantities based on dimensions for dimension-based products.
        """
        values = super()._get_move_raw_values(product_id, product_uom_qty, product_uom, operation_id, bom_line)

        if (self.product_id and
                hasattr(self.product_id, 'price_calculation_based_on') and
                self.product_id.price_calculation_based_on == 'based_on_dimension' and
                self.dimension_qty):
            raw_material_product = product_id if hasattr(product_id, 'price_calculation_based_on') else self.env['product.product'].browse(product_id)
            if (hasattr(raw_material_product, 'price_calculation_based_on') and
                    raw_material_product.price_calculation_based_on == 'based_on_dimension'):
                values['product_uom_qty'] = values['product_uom_qty'] * self.dimension_qty
        return values

    def _cal_price(self, consumed_moves):
        """
        Override to calculate price considering dimension-based products.
        """
        self.ensure_one()
        if not (
            self.product_id
            and hasattr(self.product_id, 'price_calculation_based_on')
            and self.product_id.price_calculation_based_on == 'based_on_dimension'
        ):
            return super()._cal_price(consumed_moves)

        finished_move = self.move_finished_ids.filtered(
            lambda move: move.product_id == self.product_id and move.state not in ('done', 'cancel') and move.quantity > 0
        )
        if not finished_move:
            return True

        finished_move.ensure_one()
        work_center_cost = sum(workorder._cal_cost() for workorder in self.workorder_ids)
        quantity = finished_move.product_uom._compute_quantity(
            finished_move.quantity, finished_move.product_id.uom_id
        )
        effective_quantity = quantity * self.dimension_qty
        if not effective_quantity:
            return True

        extra_cost_total = 0.0
        if 'extra_cost' in self._fields:
            extra_cost_total = self.extra_cost * effective_quantity

        total_cost = -sum(consumed_moves.sudo().stock_valuation_layer_ids.mapped('value')) + work_center_cost + extra_cost_total
        byproduct_moves = self.move_byproduct_ids.filtered(lambda move: move.state not in ('done', 'cancel') and move.quantity > 0)
        byproduct_cost_share = 0.0
        for byproduct in byproduct_moves:
            if byproduct.cost_share == 0:
                continue
            byproduct_cost_share += byproduct.cost_share
            if byproduct.product_id.cost_method in ('fifo', 'average'):
                byproduct_quantity = byproduct.product_uom._compute_quantity(byproduct.quantity, byproduct.product_id.uom_id)
                byproduct.price_unit = total_cost * byproduct.cost_share / 100 / byproduct_quantity

        if finished_move.product_id.cost_method in ('fifo', 'average'):
            finished_move.price_unit = total_cost * (1 - byproduct_cost_share / 100) / effective_quantity
        return True

    def action_confirm(self):
        """Override to validate dimensions before confirming."""
        for production in self:
            if (production.product_id and
                    hasattr(production.product_id, 'price_calculation_based_on') and
                    production.product_id.price_calculation_based_on == 'based_on_dimension'):

                if not production.dimension_method:
                    raise ValidationError("Please select a Dimension Method for dimension-based products.")

                if production.dimension_method in ['length', 'length_width', 'length_height', 'length_width_height']:
                    if production.length <= 0:
                        raise ValidationError("Length must be greater than 0 for the selected dimension method.")

                if production.dimension_method in ['width', 'length_width', 'width_height', 'length_width_height']:
                    if production.width <= 0:
                        raise ValidationError("Width must be greater than 0 for the selected dimension method.")

                if production.dimension_method in ['height', 'width_height', 'length_height', 'length_width_height']:
                    if production.height <= 0:
                        raise ValidationError("Height must be greater than 0 for the selected dimension method.")

        return super().action_confirm()

    def create_sale_order_mo(self, sale_order_line):
        """
        Create manufacturing order from sales order line with dimensions.
        This method can be called when creating MO from sales order.
        """
        if hasattr(sale_order_line, 'length'):
            self.length = sale_order_line.length or 0.0
        if hasattr(sale_order_line, 'width'):
            self.width = sale_order_line.width or 0.0
        if hasattr(sale_order_line, 'height'):
            self.height = sale_order_line.height or 0.0
        if hasattr(sale_order_line, 'dimension_qty'):
            pass

        return True
