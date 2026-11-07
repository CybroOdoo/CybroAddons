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


class ProductSaleHistoryLine(models.TransientModel):
    """ Adding the product sale history line to add the product, order id and
    quantity """
    _name = 'product.sale.history.line'
    _description = 'Product Sale History Line'
    _rec_name = 'sale_order_id'

    order_line_id = fields.Many2one('product.sale.order.history',
                                    help="To add the order line to the sale"
                                         " history.")
    sale_order_id = fields.Many2one('sale.order',
                                    string="Sale order",
                                    help='To add the sale order to the sale '
                                         'history')
    history_price = fields.Float(string='Unit Price', help='Add the product '
                                                          'price')
    history_qty = fields.Float(string='Quantity', help='Add the product '
                                                       'quantity')
    history_total = fields.Float(string='Total', help='Add the price total')
