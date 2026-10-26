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
from odoo import fields, models, _


class AccountMove(models.Model):
    """Extends account.move to generate separate journal items for discounts
    offered on customer invoices, vendor bills, and refunds upon posting.
    """
    _inherit = 'account.move'

    def _create_discount_lines(self):
        """Create journal lines for discounts on invoice and bill lines."""
        for move in self.filtered(lambda m: m.state == 'draft'):
            # Remove existing custom discount lines to prevent duplication on re-posting.
            # Odoo's native discount allocation lines ('discount') are left untouched.
            existing_discount_lines = move.line_ids.filtered(
                lambda l: l.is_discount_journal_entry or l.display_type == 'category_discount'
            )
            if existing_discount_lines:
                existing_discount_lines.unlink()

            if move.move_type not in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund'):
                continue

            lines_vals = []
            for line in move.invoice_line_ids:
                if line.discount <= 0 or not line.product_id:
                    continue

                categ = line.product_id.categ_id.with_company(move.company_id)
                if move.move_type in ('out_invoice', 'out_refund'):
                    discount_account = categ.customer_account_discount_id
                else:
                    discount_account = categ.vendor_account_discount_id

                if not discount_account or discount_account == line.account_id:
                    continue

                # Discount amount in invoice/document currency, handling tax-included prices
                if line.tax_ids:
                    taxes_res = line.tax_ids.compute_all(
                        line.price_unit,
                        currency=line.currency_id,
                        quantity=line.quantity,
                        product=line.product_id,
                        partner=move.commercial_partner_id,
                        is_refund=move.is_refund(),
                        handle_price_include=True,
                    )
                    undiscounted_base = taxes_res['total_excluded']
                    discount_amount_currency = line.currency_id.round(
                        undiscounted_base * (line.discount / 100.0)
                    )
                else:
                    discount_amount_currency = line.currency_id.round(
                        line.price_unit * line.quantity * (line.discount / 100.0)
                    )

                if discount_amount_currency <= 0:
                    continue

                # Company currency balance
                if line.currency_id == line.company_currency_id:
                    discount_balance = discount_amount_currency
                elif line.currency_rate:
                    discount_balance = line.company_currency_id.round(
                        discount_amount_currency / line.currency_rate
                    )
                else:
                    discount_balance = line.currency_id._convert(
                        discount_amount_currency,
                        line.company_currency_id,
                        line.company_id,
                        move.date or fields.Date.today(),
                    )

                # Determine debit and credit accounts based on move type
                # For customer invoices (out_invoice) and vendor refunds (in_refund):
                #   Debit = Discount Account, Credit = Line Account
                # For customer refunds (out_refund) and vendor bills (in_invoice):
                #   Debit = Line Account, Credit = Discount Account
                if move.move_type in ('out_invoice', 'in_refund'):
                    debit_account = discount_account
                    credit_account = line.account_id
                else:
                    debit_account = line.account_id
                    credit_account = discount_account

                line_name = line.name or _("Discount")
                lines_vals.extend([
                    {
                        'move_id': move.id,
                        'name': line_name,
                        'account_id': debit_account.id,
                        'journal_id': move.journal_id.id,
                        'currency_id': line.currency_id.id,
                        'amount_currency': discount_amount_currency,
                        'debit': discount_balance,
                        'credit': 0.0,
                        'display_type': 'category_discount',
                        'is_discount_journal_entry': True,
                        'partner_id': move.commercial_partner_id.id,
                    },
                    {
                        'move_id': move.id,
                        'name': line_name,
                        'account_id': credit_account.id,
                        'journal_id': move.journal_id.id,
                        'currency_id': line.currency_id.id,
                        'amount_currency': -discount_amount_currency,
                        'debit': 0.0,
                        'credit': discount_balance,
                        'display_type': 'category_discount',
                        'is_discount_journal_entry': True,
                        'partner_id': move.commercial_partner_id.id,
                    },
                ])

            if lines_vals:
                self.env['account.move.line'].with_context(
                    check_move_validity=False
                ).create(lines_vals)

    def action_post(self):
        """Create discount journal entries when posting invoices or bills."""
        self._create_discount_lines()
        return super().action_post()

    def _post(self, soft=True):
        """Ensure discount lines are created when documents are posted."""
        self._create_discount_lines()
        return super()._post(soft=soft)

    def button_draft(self):
        """Clean up discount lines when resetting move to draft."""
        res = super().button_draft()
        self.line_ids.filtered(
            lambda l: l.is_discount_journal_entry or l.display_type == 'category_discount'
        ).unlink()
        return res

    def button_cancel(self):
        """Clean up discount lines when cancelling move."""
        res = super().button_cancel()
        self.line_ids.filtered(
            lambda l: l.is_discount_journal_entry or l.display_type == 'category_discount'
        ).unlink()
        return res
