# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
"""Wizard for updating the sale and cost price of products."""
from odoo import api, fields, models


class ProductPrice(models.TransientModel):
    """Wizard for updating the sale and cost price of the product."""

    _name = 'product.price'
    _description = 'Product Price'

    product_id = fields.Many2one(
        'product.template',
        string="All Products",
        required=True,
        help="Select the product for changing the sales and cost price.",
    )
    sale_price = fields.Float(
        required=True,
        help="Defines the new selling price for the selected product.",
    )
    cost_price = fields.Float(
        required=True,
        help="Defines the new cost of the selected product.",
    )

    def action_change_product_price(self):
        """Open a wizard with current sale and cost price of selected product.

        :return: returns to the product form with updated price
        """
        self.ensure_one()
        self.product_id.write({
            'list_price': self.sale_price,
            'standard_price': self.cost_price,
        })
        return {
            'name': self.env._('Products'),
            'view_mode': 'form',
            'res_model': 'product.template',
            'type': 'ir.actions.act_window',
            'res_id': self.product_id.id,
            'context': self.env.context,
        }

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Update the selected product's sale and cost price."""
        if self.product_id:
            self.sale_price = self.product_id.list_price
            self.cost_price = self.product_id.standard_price
