# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vishnu KP @ Cybrosys, (odoo@cybrosys.com)
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
from odoo import fields, models


class ProductSaleHistoryLine(models.TransientModel):
    """Adding the product sale history line to add the product, order id and
    quantity"""
    _name = 'product.sale.history.line'
    _rec_name = 'sale_order_id'

    order_line_id = fields.Many2one('product.sale.order.history',
                                    string='Order Line', help='To add the '
                                                              'order line to '
                                                              'the sale '
                                                              'history')
    sale_order_id = fields.Many2one('sale.order',
                                    string="Sale order",
                                    help='To add the sale order to the sale '
                                         'history')
    history_price = fields.Char(string='Unit Price', help='Add the product '
                                                          'price')
    history_qty = fields.Float(string='Quantity', help='Add the product '
                                                       'quantity')
    history_total = fields.Float(string='Total', help='Add the price total')
