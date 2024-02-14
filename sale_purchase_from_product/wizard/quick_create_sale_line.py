# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class QuickSaleOrderLines(models.TransientModel):
    """OrderLine for quick sale order"""
    _name = 'quick.sale.line'
    _description = 'Quick Sale Line'

    product_id = fields.Many2one('product.product',
                                 string='Product', required=True,
                                 help="Products")
    product_uom_qty = fields.Float(string="Quantity", help="Product Quantity")
    price_unit = fields.Float(string="Unit Price", required=True,
                              help="Product unit price")
    tax_id = fields.Many2many(comodel_name='account.tax', string="Taxes",
                              help="Choose taxes for the products")
    order_id = fields.Many2one('quick.sale.order',
                               string="Order", help="Created sale order")
