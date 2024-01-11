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


class ProductSaleOrderHistory(models.TransientModel):
    _name = 'product.sale.order.history'
    _description = 'Product Sale Order History'
    _rec_name = 'product_id'

    product_sale_history_ids = fields.One2many('product.sale.history.line',
                                           'order_line_id',
                                           string='Product Sale Price History',
                                           help="shows the product sale "
                                                "history of the customer")
    product_id = fields.Many2one('product.product',
                                 string="Product",
                                 help="Choose a Product")
