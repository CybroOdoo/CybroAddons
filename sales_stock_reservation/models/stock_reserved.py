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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class StockReserved(models.Model):
    """This model stores details of product reservations made in sale orders."""

    _name = "stock.reserved"
    _description = "Reserved Stock Details"

    name = fields.Char(
        readonly=True,
        help="Name of the reservation sequence.",
    )
    order_line_name = fields.Char(
        string="Order Line",
        readonly=True,
        help="Name of the corresponding order line.",
    )
    product_id = fields.Many2one(
        "product.product",
        readonly=True,
        help="Product reserved for the quotation.",
    )
    status = fields.Selection(
        [('reserved', 'Reserved'), ('cancelled', 'Cancelled')],
        readonly=True,
        help="Current status of the stock reservation.",
    )
    reserved_quantity = fields.Float(
        readonly=True,
        help="Quantity of product reserved.",
    )
    sale_order_id = fields.Many2one(
        "sale.order",
        readonly=True,
        help="Sales order linked to this reservation.",
    )
    move_id = fields.Many2one(
        "stock.move",
        string="Stock Move",
        readonly=True,
        help="Associated stock move.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Create a new record and generate a sequence for the name field."""
        clean_vals_list = []
        for vals in vals_list:
            vals_copy = dict(vals)
            if vals_copy.get('name', self.env._('New')) == self.env._('New'):
                vals_copy['name'] = self.env['ir.sequence'].next_by_code(
                    'stock.reserved'
                ) or self.env._('New')
            clean_vals_list.append(vals_copy)
        return super().create(clean_vals_list)
