# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class ProductBundleLine(models.Model):
    """Model representing a single component line within a product bundle."""

    _name = 'product.bundle.line'
    _description = 'Product Bundle Line'

    bundle_id = fields.Many2one(
        'product.template',
        string='Bundle',
        help='The parent bundle product this line belongs to.',
        ondelete='cascade',
        index=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        help='The component product included in this bundle.',
        required=True,
    )
    image_128 = fields.Image(
        related='product_id.image_128',
        string='Image',
        help='Thumbnail image of the component product.',
    )
    quantity = fields.Float(
        string='Quantity',
        help='Quantity of this component included in one bundle unit.',
        default=1.0,
        required=True,
    )
    price_unit = fields.Float(
        related='product_id.list_price',
        string='Unit Price',
        help='Sales price of the component product.',
    )
    cost_unit = fields.Float(
        related='product_id.standard_price',
        string='Unit Cost',
        help='Cost price of the component product.',
    )
    subtotal_price = fields.Float(
        compute='_compute_subtotals',
        string='Subtotal Price',
        help='Total sales price for this component (quantity × unit price).',
        store=True,
    )
    subtotal_cost = fields.Float(
        compute='_compute_subtotals',
        string='Subtotal Cost',
        help='Total cost for this component (quantity × unit cost).',
        store=True,
    )

    @api.depends('quantity', 'product_id', 'price_unit', 'cost_unit')
    def _compute_subtotals(self):
        """Compute the price and cost subtotals for each bundle line."""
        for line in self:
            line.subtotal_price = line.quantity * line.price_unit
            line.subtotal_cost = line.quantity * line.cost_unit

    @api.onchange('quantity', 'product_id')
    def _onchange_quantity(self):
        """Update subtotals immediately in the UI."""
        self.subtotal_price = self.quantity * self.price_unit
        self.subtotal_cost = self.quantity * self.cost_unit
