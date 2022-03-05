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

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    """inherited account payment"""
    _inherit = "account.payment"

    destination_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Destination Account',
        store=True, readonly=False,
        compute='_compute_destination_account_id',
        domain="[('user_type_id.type', 'in', ('receivable', 'payable')), "
               "('company_id', '=', company_id),"
               "'|', ('branch_id', '=', branch_id), ('branch_id', '=', False)]",
        check_company=True)

    @api.constrains('branch_id')
    def _check_payment_branch_id(self):
        """methode to check branch of accounts and entry"""
        for payment in self:
            branch = payment.destination_account_id.branch_id
            if branch and branch != payment.branch_id:
                raise ValidationError(_(
                    "Your payment belongs to  '%s' branch whereas the account"
                    " belongs to '%s' branch.", payment.branch_id.name,
                    branch.name))

    @api.depends('journal_id', 'branch_id', 'partner_id', 'partner_type',
                 'is_internal_transfer')
    def _compute_destination_account_id(self):
        """methode to compute destination account"""
        if self.branch_id:
            self.destination_account_id = False
            for pay in self:
                if pay.is_internal_transfer:
                    pay.destination_account_id = \
                        pay.journal_id.company_id.transfer_account_id
                elif pay.partner_type == 'customer':
                    # Receive money from invoice or send money to refund it.
                    if pay.partner_id:
                        pay.destination_account_id = \
                            pay.partner_id.with_company(
                                pay.company_id).property_account_receivable_id
                    else:
                        destination_account = self.env[
                            'account.account'].search([
                                ('company_id', '=', pay.company_id.id),
                                ('branch_id', '=', pay.branch_id.id),
                                ('internal_type', '=', 'receivable'),
                            ], limit=1)
                        pay.destination_account_id = destination_account
                        if not destination_account:
                            destination_account = self.env[
                                'account.account'].search([
                                    ('company_id', '=', pay.company_id.id),
                                    ('branch_id', '=', False),
                                    ('internal_type', '=', 'receivable'),
                                ], limit=1)
                        pay.destination_account_id = destination_account
                elif pay.partner_type == 'supplier':
                    # Send money to pay a bill or receive money to refund it.
                    if pay.partner_id:
                        pay.destination_account_id = \
                            pay.partner_id.with_company(
                                pay.company_id).property_account_payable_id
                    else:
                        destination_account = self.env[
                            'account.account'].search([
                                ('company_id', '=', pay.company_id.id),
                                ('branch_id', '=', pay.branch_id.id),
                                ('internal_type', '=', 'payable'),
                            ], limit=1)
                        pay.destination_account_id = destination_account
                        if not destination_account:
                            destination_account = self.env[
                                'account.account'].search([
                                    ('company_id', '=', pay.company_id.id),
                                    ('branch_id', '=', False),
                                    ('internal_type', '=', 'payable'),
                                ], limit=1)
                            pay.destination_account_id = destination_account
        else:
            res = super(AccountMove, self)._compute_destination_account_id()
            return res
