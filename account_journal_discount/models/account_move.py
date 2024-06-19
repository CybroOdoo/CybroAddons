# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vivek @ cybrosys,(odoo@cybrosys.com)
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
from odoo import models
from odoo.tools import float_round


class AccountMove(models.Model):
    """This model is used for redefining the action_post function in order to
       create journal entries for discount provided on invoice line and bills
    """
    _inherit = 'account.move'

    def action_post(self):
        """Redefining the function to create new journal entries whenever
        journal discounts are provided.
        """
        if self.move_type == 'out_invoice':
            for line in self.invoice_line_ids:
                if line.discount > 0 and \
                        line.product_id.categ_id.customer_account_discount_id:
                    debit_credit_value = abs(
                        float_round((line.price_subtotal - line.price_unit),
                                    precision_digits=
                                    self.currency_id.decimal_places))
                    self.env['account.move.line'].create({
                        'move_id': self.id,
                        'currency_id': self.currency_id.id,
                        'display_type': 'tax',
                        'name': line.name,
                        'account_id': line.product_id.categ_id.customer_account_discount_id.id,
                        'journal_id': self.journal_id,
                        'credit': 0,
                        'debit': debit_credit_value,
                    })
                    self.env['account.move.line'].create({
                        'move_id': self.id,
                        'display_type': 'tax',
                        'currency_id': self.currency_id.id,
                        'name': line.name,
                        'account_id': line.account_id.id,
                        'journal_id': self.journal_id,
                        'credit': debit_credit_value,
                        'debit': 0,
                    })
        elif self.move_type == 'in_invoice':
            for line in self.invoice_line_ids:
                if line.discount > 0 and \
                        line.product_id.categ_id.vendor_account_discount_id:
                    debit_credit_value = abs(
                        float_round((line.price_subtotal - line.price_unit),
                                    precision_digits=
                                    self.currency_id.decimal_places))
                    self.env['account.move.line'].with_context(
                        check_move_validity=False).create({
                            'move_id': self.id,
                            'display_type': 'tax',
                            'name': line.name,
                            'account_id': line.product_id.categ_id.vendor_account_discount_id.id,
                            'journal_id': self.journal_id,
                            'currency_id': self.currency_id.id,
                            'credit': 0,
                            'debit': debit_credit_value,
                        })
                    self.env['account.move.line'].with_context(
                        check_move_validity=False).create({
                            'move_id': self.id,
                            'display_type': 'tax',
                            'name': line.name,
                            'account_id': line.account_id.id,
                            'journal_id': self.journal_id,
                            'currency_id': self.currency_id.id,
                            'credit': debit_credit_value,
                            'debit': 0,
                        })
        res = super(AccountMove, self).action_post()
        return res
