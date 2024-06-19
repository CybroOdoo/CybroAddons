# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class AccountPayment(models.Model):
    """Added custom field bank_charges to add the extra charges"""
    _inherit = "account.payment"

    bank_charges = fields.Monetary(currency_field='currency_id',
                                   string="Bank Charges",
                                   help="Bank charge amount")

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        """Adding bank charges in move line"""
        res = super(AccountPayment, self)._prepare_move_line_default_vals(
            write_off_line_vals=write_off_line_vals)
        if self.bank_charges:
            # Compute default label in journal items for bank charges.
            liquidity_line_name = ''.join(
                x[1] for x in self._get_liquidity_aml_display_name_list())
            bank_charges_line_name = liquidity_line_name.replace(
                str(("{:,}".format(self.amount))),
                str(self.bank_charges))
            move = self.env['account.move'].create({
                'journal_id': self.journal_id.id,
                'move_type': 'entry',
                'partner_id': self.partner_id.id,
                'line_ids': [
                    (0, 0, {
                        'name': bank_charges_line_name,
                        'partner_id': self.partner_id.id,
                        'journal_id': self.journal_id.id,
                        'account_id': self.journal_id.account_id.id,
                        'debit': self.bank_charges,
                        'credit': 0.0,
                    }),
                    (0, 0, {
                        'name': bank_charges_line_name,
                        'partner_id': self.partner_id.id,
                        'journal_id': self.journal_id.id,
                        'account_id': self.journal_id.default_account_id.id,
                        'debit': 0.0,
                        'credit': self.bank_charges,
                    }),
                ],
            })
            move.action_post()
        return res
