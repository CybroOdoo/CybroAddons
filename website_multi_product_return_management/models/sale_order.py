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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    """Extend the sale order model to manage the return orders"""
    _inherit = 'sale.order'

    return_order_count = fields.Integer(
        compute="_compute_return_order_count", string='Return Orders',
        help="Count of product returned on this order")

    def _compute_return_order_count(self):
        """Method to compute return count for sale orders."""
        for order in self:
            order.return_order_count = self.env['sale.return'].sudo().search_count(
                [('sale_order_id', '=', order.id)]
            )

    def action_open_returns(self):
        """This function returns an action that displays the sale return
        orders from sale order"""
        action = self.env['ir.actions.act_window']._for_xml_id(
            'website_multi_product_return_management.sale_return_action')
        domain = [('sale_order_id', '=', self.id)]
        action['domain'] = domain
        action['context'] = {'search_default_order': 1}
        return action


class SaleOrderLine(models.Model):
    """Extend the Sale Order line model to include a new field."""
    _inherit = 'sale.order.line'

    return_order_line_count = fields.Integer(
        string='Return Orders', default=0,
        help="Count of product returned in this order line")
