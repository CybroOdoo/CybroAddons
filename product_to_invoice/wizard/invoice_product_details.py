# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Midilaj V K (<https://www.cybrosys.com>)
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

from odoo import models, fields, api
from datetime import timedelta


class InvoiceProductDetailsWizard(models.TransientModel):
    _name = 'invoice.product.details.wizard'
    _description = 'Invoice Product Details Wizard'

    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    qty = fields.Float(string='Quantity', default=1)
    account_move_id = fields.Many2one('account.move', readonly=True)
    price_unit = fields.Float(string='Unit Price')
    invoice_history_ids = fields.One2many('product.invoice.history', 'product_details_id', readonly=True)
    date_from = fields.Date(default=fields.Date.today() - timedelta(days=30))
    limit = fields.Integer(string='Limit', default=20)

    @api.onchange('date_from', 'limit')
    def _onchange_date_from(self):
        invoice_lines = self.env['account.move.line'].search([('product_id', '=', self.product_id.id),
                                                              ('move_id.state', '=', 'posted'),
                                                              ('move_id.invoice_date', '>=', self.date_from),
                                                              ('move_id.move_type', 'in',
                                                               ('out_invoice', 'in_invoice')),
                                                              ('exclude_from_invoice_tab', '=', False)],
                                                             limit=self.limit)
        vals = [(5, 0, 0)]
        for line in invoice_lines:
            vals.append((0, 0, {
                'date': line.move_id.invoice_date,
                'partner_id': line.move_id.partner_id.id,
                'qty': line.quantity,
                'account_move_number': line.move_id.name,
                'price_unit': line.price_unit,
                'total': line.price_subtotal,
                'type': line.move_id.move_type,
                'move_id': line.move_id.id
            }))
        self.invoice_history_ids = vals

    def add_to_invoice(self):
        account_id = self.product_id._get_invoice_account(self.account_move_id)
        tax_ids = self.product_id._get_invoice_taxes(self.account_move_id, account_id)
        self.account_move_id.write({
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'product_uom_id': self.product_id.uom_id.id,
                'quantity': self.qty,
                'price_unit': self.price_unit,
                'account_id': account_id,
                'tax_ids': tax_ids
            })]
        })


class ProductInvoiceHistory(models.TransientModel):
    _name = 'product.invoice.history'
    _description = 'Product Invoice History'

    product_details_id = fields.Many2one('invoice.product.details.wizard')
    date = fields.Datetime(string='Date')
    move_id = fields.Many2one('account.move', string='Invoice/Bill')
    account_move_number = fields.Char(string='Invoice/Bill No')
    partner_id = fields.Many2one('res.partner', string='Customer/vendor')
    price_unit = fields.Float(string='Unit Price')
    total = fields.Float(string='Total')
    qty = fields.Float(string='Quantity')
    type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Vendor Bill')
    ], string='Type')
