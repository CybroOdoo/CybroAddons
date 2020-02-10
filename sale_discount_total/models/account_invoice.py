# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Faslu Rahman(odoo@cybrosys.com)
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

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state')
    def _compute_amount(self):

        invoice_ids = [move.id for move in self if move.id and move.is_invoice(include_receipts=True)]
        self.env['account.payment'].flush(['state'])
        if invoice_ids:
            self._cr.execute(
                '''
                    SELECT move.id
                    FROM account_move move
                    JOIN account_move_line line ON line.move_id = move.id
                    JOIN account_partial_reconcile part ON part.debit_move_id = line.id OR part.credit_move_id = line.id
                    JOIN account_move_line rec_line ON
                        (rec_line.id = part.credit_move_id AND line.id = part.debit_move_id)
                        OR
                        (rec_line.id = part.debit_move_id AND line.id = part.credit_move_id)
                    JOIN account_payment payment ON payment.id = rec_line.payment_id
                    JOIN account_journal journal ON journal.id = rec_line.journal_id
                    WHERE payment.state IN ('posted', 'sent')
                    AND journal.post_at = 'bank_rec'
                    AND move.id IN %s
                ''', [tuple(invoice_ids)]
            )
            in_payment_set = set(res[0] for res in self._cr.fetchall())
        else:
            in_payment_set = {}

        for move in self:
            total_untaxed = 0.0
            total_untaxed_currency = 0.0
            total_tax = 0.0
            total_tax_currency = 0.0
            total_residual = 0.0
            total_residual_currency = 0.0
            currencies = set()

            for line in move.line_ids:
                if line.currency_id:
                    currencies.add(line.currency_id)

                # Untaxed amount.
                if (move.is_invoice(include_receipts=True) and not line.exclude_from_invoice_tab) \
                        or (move.type == 'entry' and line.debit and not line.tax_line_id):
                    total_untaxed += line.balance
                    total_untaxed_currency += line.amount_currency

                # Tax amount.
                if line.tax_line_id:
                    total_tax += line.balance
                    total_tax_currency += line.amount_currency

                # Residual amount.
                if move.type == 'entry' or line.account_id.user_type_id.type in ('receivable', 'payable'):
                    total_residual += line.amount_residual
                    total_residual_currency += line.amount_residual_currency

            total = total_untaxed + total_tax
            total_currency = total_untaxed_currency + total_tax_currency

            if move.type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1
            if move.discount_type == 'percent':
                move.amount_discount = sum((line.quantity * line.price_unit * line.discount) / 100 for line in move.invoice_line_ids)
            else:
                move.amount_discount = move.discount_rate
            move.amount_untaxed = sign * (total_untaxed_currency if len(currencies) == 1 else total_untaxed)
            move.amount_tax = sign * (total_tax_currency if len(currencies) == 1 else total_tax)
            move.amount_total = sign * (total_currency if len(currencies) == 1 else total)
            move.amount_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual)
            move.amount_untaxed_signed = -total_untaxed
            move.amount_tax_signed = -total_tax
            move.amount_total_signed = -total
            move.amount_residual_signed = total_residual

            currency = len(currencies) == 1 and currencies.pop() or move.company_id.currency_id
            is_paid = currency and currency.is_zero(move.amount_residual) or not move.amount_residual

            # Compute 'invoice_payment_state'.
            if move.state == 'posted' and is_paid:
                if move.id in in_payment_set:
                    move.invoice_payment_state = 'in_payment'
                else:
                    move.invoice_payment_state = 'paid'
            else:
                move.invoice_payment_state = 'not_paid'

    discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], string='Discount Type',
                                     readonly=True, states={'draft': [('readonly', False)]}, default='percent')
    discount_rate = fields.Float('Discount Amount', digits=(16, 2), readonly=True,
                                 states={'draft': [('readonly', False)]})
    amount_discount = fields.Monetary(string='Discount', store=True, readonly=True, compute='_compute_amount',
                                      track_visibility='always')

    @api.onchange('discount_type', 'discount_rate', 'invoice_line_ids')
    def supply_rate(self):
        for inv in self:
            if inv.discount_type == 'percent':
                for line in inv.line_ids:
                    line.discount = inv.discount_rate
                    line._onchange_price_subtotal()
            else:
                total = discount = 0.0
                for line in inv.invoice_line_ids:
                    total += (line.quantity * line.price_unit)
                if inv.discount_rate != 0:
                    discount = (inv.discount_rate / total) * 100
                else:
                    discount = inv.discount_rate
                for line in inv.line_ids:
                    line.discount = discount
                    line._onchange_price_subtotal()

            inv._compute_invoice_taxes_by_group()
    #

    def button_dummy(self):
        self.supply_rate()
        return True


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    discount = fields.Float(string='Discount (%)', digits=(16, 20), default=0.0)
