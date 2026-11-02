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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields, models
from odoo.fields import Domain


class SaleOrder(models.Model):
    """Flag textile sale orders and store the customer feedback given at
    checkout."""
    _inherit = 'sale.order'

    is_textile_sale_order = fields.Boolean(
        help="The sale order was created from the Textile app")
    comment = fields.Char(
        readonly=True, copy=False,
        help='The comment provided by the customer.')
    rating = fields.Selection(
        [('0', 'Not Rated'), ('1', 'Poor'), ('2', 'Average'), ('3', 'Nice'),
         ('4', 'Excellent')],
        readonly=True, copy=False,
        help='The rating provided by the customer.')

    def _get_product_catalog_domain(self):
        """Limit the product catalog of textile orders to textile products."""
        domain = super()._get_product_catalog_domain()
        if self.is_textile_sale_order:
            domain &= Domain('is_textile_product', '=', True)
        return domain

    def _action_confirm(self):
        """Flag the website orders of textile products as textile, before the
        stock rules create their manufacturing orders."""
        self.filtered(
            lambda order: order.website_id
            and not order.is_textile_sale_order
            and any(order.order_line.product_id.mapped('is_textile_product')),
        ).is_textile_sale_order = True
        return super()._action_confirm()
