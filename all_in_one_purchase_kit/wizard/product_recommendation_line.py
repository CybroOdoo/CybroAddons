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
from odoo import fields, models


class ProductRecommendationLine(models.TransientModel):
    """Model product.recommendation.line"""
    _name = "product.recommendation.line"
    _description = "Recommended product for current purchase order"
    _order = "id"

    currency_id = fields.Many2one(
        related="product_id.currency_id", string="Currency", help="Currency"
    )
    partner_id = fields.Many2one(
        related="recommendation_id.order_id.partner_id",
        string="Partner",
        help="Partner Selected in Product recommendation"
    )
    product_id = fields.Many2one(
        comodel_name="product.product", string="Product",
        help="Select product"
    )
    product_code = fields.Char(
        string="Product reference", help="Product reference code"
    )
    list_price = fields.Monetary(
        readonly=True, help='Product cost', string="Product cost"
    )
    available_qty = fields.Float(
        readonly=True, help="Available quantity", string="Available quantity"
    )
    recommendation_id = fields.Many2one(
        "product.recommendation", string="Product recommendation",
        ondelete="cascade", help="Product recommendation"
    )
    order_line_id = fields.Many2one(
        "purchase.order.line", string="Product", help="Purchased product"
    )
    is_modified = fields.Boolean(
        string='Select', help='Select the product to add to orderline'
    )
    qty_need = fields.Integer(string="Quantity", help='Enter the quantity')

    def _prepare_order_line(self, sequence):
        """So we can extend PO create"""
        return {
            "order_id": self.recommendation_id.order_id.id,
            "product_id": self.product_id.id,
            "sequence": sequence,
            "product_qty": self.qty_need,
        }
