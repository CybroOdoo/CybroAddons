# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class ProductRecommendation(models.TransientModel):
    """Creating a transient model """
    _name = "product.recommendation"
    _description = "Recommended products for current purchase order"

    order_id = fields.Many2one(
        "purchase.order", string="Purchase Order",
        default=lambda self: self._default_order_id(), help="Select Product"
    )
    line_ids = fields.One2many(
        "product.recommendation.line", "recommendation_id", string="Products",
        help="Product recommendation"
    )

    @api.model
    def _default_order_id(self):
        """Selecting the active vendor"""
        return self.env.context.get("active_id", False)

    def add_to_order_line(self):
        """Product adding to order line"""
        po_lines = self.env["purchase.order.line"]
        sequence = max(self.order_id.mapped("order_line.sequence") or [0])
        for line in self.line_ids.filtered(lambda l: l.is_modified is True):
            if line.qty_need > 0:
                sequence += 1
                po_line = po_lines.new(line._prepare_order_line(sequence))
                po_line.onchange_product_id()
                po_line.product_qty = line.qty_need
                po_lines |= po_line
        self.order_id.order_line |= po_lines
