# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields, api


class AccountPaymentRegister(models.TransientModel):
    """inherited account payment register wizard models"""
    _inherit = 'account.payment.register'

    branch_id = fields.Many2one('res.branch', store=True, readonly=False)
    journal_id = fields.Many2one('account.journal', store=True, readonly=False,
                                 compute='_compute_journal_id',
                                 domain="[('company_id', '=', company_id), "
                                        "('type', 'in', ('bank', 'cash'))]")

    @api.depends('company_id', 'source_currency_id')
    def _compute_journal_id(self):
        """methode to compute journal id based on current branch"""
        self.ensure_one()
        lines = self.line_ids._origin
        branch = lines.branch_id
        if branch:
            for wizard in self:
                domain = [
                    ('type', 'in', ('bank', 'cash')),
                    ('branch_id', '=', branch.id),
                ]
                journal = None
                if wizard.source_currency_id:
                    journal = self.env['account.journal'].search(domain + [
                        ('currency_id', '=', wizard.source_currency_id.id)],
                                                                 limit=1)
                if not journal:
                    journal = self.env['account.journal'].search(domain,
                                                                 limit=1)
                if not journal:
                    domain = [
                        ('type', 'in', ('bank', 'cash')),
                        ('branch_id', '=', False),
                    ]
                    journal = None
                    if wizard.source_currency_id:
                        journal = self.env['account.journal'].search(domain + [
                            ('currency_id', '=', wizard.source_currency_id.id)],
                                                                     limit=1)
                    if not journal:
                        journal = self.env['account.journal'].search(domain,
                                                                     limit=1)
                wizard.journal_id = journal
        else:
            res = super(AccountPaymentRegister, self)._compute_journal_id()
            return res

    def _create_payment_vals_from_wizard(self):
        """create payment values"""
        self.ensure_one()
        lines = self.line_ids._origin
        branch = lines.branch_id
        payment_vals = {
            'date': self.payment_date,
            'amount': self.amount,
            'payment_type': self.payment_type,
            'partner_type': self.partner_type,
            'ref': self.communication,
            'journal_id': self.journal_id.id,
            'branch_id': branch.id,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            'payment_method_id': self.payment_method_id.id,
            'destination_account_id': self.line_ids[0].account_id.id
        }
        if not self.currency_id.is_zero(
                self.payment_difference) and self.payment_difference_handling == 'reconcile':
            payment_vals['write_off_line_vals'] = {
                'name': self.writeoff_label,
                'amount': self.payment_difference,
                'account_id': self.writeoff_account_id.id,
            }
        return payment_vals
