# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ranjith R (odoo@cybrosys.com)
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
from odoo import api, fields, models


class BookOrderLine(models.Model):
    """ For managing order lines of booked order """
    _name = "book.order.line"
    _description = "Lines of Point of Sale Booked Order"
    _rec_name = "product_id"

    company_id = fields.Many2one('res.company', string='Company',
                                 help="Company of the booked order",
                                 default=lambda self: self.env.user.company_id)
    product_id = fields.Many2one('product.product',
                                 help="Select products for ordering",
                                 string='Product',
                                 domain=[('sale_ok', '=', True)],
                                 required=True, change_default=True)
    price_unit = fields.Float(string='Unit Price',
                              help="Unite price of selected product", digits=0)
    qty = fields.Float(string='Quantity', default=1,
                       help="Enter how much quantity of product want ")
    price_subtotal = fields.Float(compute='_compute_amount_line_all',
                                  digits=0,
                                  help="Sub total amount of each order line"
                                       "without tax",
                                  string='Subtotal w/o Tax')
    price_subtotal_incl = fields.Float(compute='_compute_amount_line_all',
                                       digits=0, string='Subtotal',
                                       help="Sub total amount of each order "
                                            "line with tax")
    discount = fields.Float(string='Discount (%)', digits=0, default=0.0,
                            help="You can apply discount for each product")
    order_id = fields.Many2one('book.order', string='Order Ref',
                               help="Relation to book order field",
                               ondelete='cascade')
    tax_ids = fields.Many2many('account.tax', string='Taxes',
                               readonly=True, help="Taxes for each line")
    tax_after_fiscal_position_ids = fields.Many2many(
        'account.tax', 'account_tax_rel', 'uid',
        'tag_id', string='Taxes', help="Fiscal position after entering "
                                       "the tax")

    @api.depends('price_unit', 'tax_ids', 'qty', 'discount', 'product_id')
    def _compute_amount_line_all(self):
        """ To compute tax included and excluded subtotal in each line"""
        for line in self:
            currency = self.env.company.currency_id
            taxes = line.tax_ids.filtered(
                lambda tax: tax.company_id.id == line.order_id.company_id.id)
            fiscal_position_id = line.order_id.fiscal_position_id
            if fiscal_position_id:
                taxes = fiscal_position_id.map_tax(taxes, line.product_id,
                                                   line.order_id.partner_id)
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            line.price_subtotal = line.price_subtotal_incl = price * line.qty
            if taxes:
                taxes = taxes.compute_all(price, currency, line.qty,
                                          product=line.product_id,
                                          partner=line.order_id.partner_i or
                                                  False)
                line.price_subtotal = taxes['total_excluded']
                line.price_subtotal_incl = taxes['total_included']

            line.price_subtotal = currency.round(line.price_subtotal)
            line.price_subtotal_incl = currency.round(line.price_subtotal_incl)
