# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: fasluca(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'tax_line_ids.amount_rounding',
                 'currency_id', 'company_id', 'date_invoice', 'type')
    def _compute_amount(self):
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
        self.amount_tax = sum(line.amount_total for line in self.tax_line_ids)
        self.amount_total = self.amount_untaxed + self.amount_tax
        self.amount_discount = sum((line.quantity * line.price_unit * line.discount)/100 for line in self.invoice_line_ids)
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id.with_context(date=self.date_invoice)
            amount_total_company_signed = currency_id._convert(self.amount_total, self.company_id.currency_id, self.company_id, self.date_invoice or fields.Date.today())
            amount_untaxed_signed = currency_id._convert(self.amount_untaxed, self.company_id.currency_id,  self.company_id, self.date_invoice or fields.Date.today())
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign

    discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], string='Discount Type',
                                     readonly=True, states={'draft': [('readonly', False)]}, default='percent')
    discount_rate = fields.Float('Discount Amount', digits=(16, 2), readonly=True, states={'draft': [('readonly', False)]})
    amount_discount = fields.Monetary(string='Discount', store=True, readonly=True, compute='_compute_amount',
                                      track_visibility='always')

    @api.onchange('discount_type', 'discount_rate', 'invoice_line_ids')
    def supply_rate(self):
        for inv in self:
            if inv.discount_type == 'percent':
                for line in inv.invoice_line_ids:
                    line.discount = inv.discount_rate
            else:
                total = discount = 0.0
                for line in inv.invoice_line_ids:
                    total += (line.quantity * line.price_unit)
                if inv.discount_rate != 0:
                    discount = (inv.discount_rate / total) * 100
                else:
                    discount = inv.discount_rate
                for line in inv.invoice_line_ids:
                    line.discount = discount

    @api.multi
    def compute_invoice_totals(self, company_currency, invoice_move_lines):
        total = 0
        total_currency = 0
        for line in invoice_move_lines:
            if self.currency_id != company_currency:
                currency = self.currency_id.with_context(date=self.date or self.date_invoice or fields.Date.context_today(self))
                line['currency_id'] = currency.id
                line['amount_currency'] = currency.round(line['price'])
                line['price'] = currency.compute(line['price'], company_currency)
            else:
                line['currency_id'] = False
                line['amount_currency'] = False
                line['price'] = line['price']
            if self.type in ('out_invoice', 'in_refund'):
                total += line['price']
                total_currency += line['amount_currency'] or line['price']
                line['price'] = - line['price']
            else:
                total -= line['price']
                total_currency -= line['amount_currency'] or line['price']
        return total, total_currency, invoice_move_lines

    @api.multi
    def button_dummy(self):
        self.supply_rate()
        return True

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    discount = fields.Float(string='Discount (%)', digits=(16, 20), default=0.0)
