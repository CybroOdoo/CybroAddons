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


class StockMove(models.Model):
    """Carry dimension values on stock moves so procurements can preserve them."""
    _inherit = 'stock.move'

    length = fields.Float(string='Length', digits='Product Unit of Measure')
    width = fields.Float(string='Width', digits='Product Unit of Measure')
    height = fields.Float(string='Height', digits='Product Unit of Measure')
    dimension_qty = fields.Float(
        string="Dimension Qty",
        compute="_compute_dimension_qty",
        store=True,
    )
    dimension_method = fields.Selection([
        ('length', 'Length'),
        ('width', 'Width'),
        ('height', 'Height'),
        ('length_width', 'Length x Width'),
        ('width_height', 'Width x Height'),
        ('length_height', 'Length x Height'),
        ('length_width_height', 'Length x Width x Height'),
    ], default='length_width_height')

    @api.depends('product_id', 'product_id.price_calculation_based_on', 'length', 'width', 'height', 'dimension_method')
    def _compute_dimension_qty(self):
        """Compute the dimension quantity based on the selected dimension method."""
        for move in self:
            if not move.product_id or move.product_id.price_calculation_based_on != 'based_on_dimension':
                move.dimension_qty = 0.0
                continue
            if not any((move.length, move.width, move.height)):
                move.dimension_qty = 0.0
                continue

            length = move.length if move.length != 0 else 1
            width = move.width if move.width != 0 else 1
            height = move.height if move.height != 0 else 1

            if move.dimension_method == 'length':
                move.dimension_qty = length
            elif move.dimension_method == 'width':
                move.dimension_qty = width
            elif move.dimension_method == 'height':
                move.dimension_qty = height
            elif move.dimension_method == 'length_width':
                move.dimension_qty = length * width
            elif move.dimension_method == 'width_height':
                move.dimension_qty = width * height
            elif move.dimension_method == 'length_height':
                move.dimension_qty = length * height
            else:
                move.dimension_qty = length * width * height

    def _prepare_procurement_values(self):
        """Keep dimension values on procurements generated from stock moves."""
        values = super()._prepare_procurement_values()
        values.update({
            'length': self.length,
            'width': self.width,
            'height': self.height,
            'dimension_qty': self.dimension_qty,
            'dimension_method': self.dimension_method,
        })
        return values
