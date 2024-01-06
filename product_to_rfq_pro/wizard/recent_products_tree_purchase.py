# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Albin PJ (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import fields, models


class RecentProductsTreePurchase(models.TransientModel):
    """This is for recent products"""
    _name = 'recent.products.tree.purchase'
    _description = "Recent Products Tree Purchase"

    partner_id = fields.Many2one('res.partner', string='Vendor',
                                 related='order_line_id.partner_id',
                                 help="Name of the vendor")
    quotation_id = fields.Many2one('purchase.order',
                                   string='Order Number',
                                   related='order_line_id.order_id',
                                   help='Quotation number')
    price = fields.Float(string='Unit Price',
                         related='order_line_id.price_unit',
                         help="Unit Price of the product")
    date = fields.Datetime(string='Date', related='order_line_id.date_planned',
                           help="Date of the purchase")
    qty = fields.Float(string='Quantity', related='order_line_id.product_qty',
                       help="Quantity of product purchased")
    purchase_total = fields.Monetary(string='Total',
                                     related='order_line_id.price_total',
                                     help="Purchase total")
    purchase_id = fields.Many2one('product.to.rfq',
                                  string='Product to rfq ID',
                                  help="Purchase Order")
    order_line_id = fields.Many2one('purchase.order.line',
                                    string='Order Line', readonly=True,
                                    help="Purchase Order Line")
    company_id = fields.Many2one('res.company',
                                 related='order_line_id.company_id',
                                 string='Company', store=True,
                                 help="Company Name")
    currency_id = fields.Many2one(related='order_line_id.currency_id',
                                  store=True, string='Currency',
                                  help="Currency")
