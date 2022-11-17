# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    state = fields.Selection(
        selection_add=[('waiting_approval', 'Waiting For Approval'),
                       ('approved', 'Approved'),
                       ('rejected', 'Rejected')],
        ondelete={'waiting_approval': 'set default', 'approved': 'set default', 'rejected': 'set default'})


class AccountPayment(models.Model):
    _inherit = "account.payment"

    # _inherits = {'account.move': 'move_id'}

    def _check_is_approver(self):
        if self.env['ir.config_parameter'].sudo().get_param(
                'account_payment_approval.multi_approval'):
            approval = self.env['ir.config_parameter'].sudo().get_param(
                'account_payment_approval.multi_approval')
            print(approval, 'nn')
            approver_id = self.env['payment.approves'].search([],order='amount')
            print(approver_id, 'vvvvv')
            for rec in approver_id:
                print(rec.approve_user_id,'approve_user_id')
                if rec.approve_user_id.id == self.env.user.id:
                        self.is_approver_check = True
                else:
                    self.is_approver_check = False
        if self.env['ir.config_parameter'].sudo().get_param(
                'account_payment_approval.payment_approval'):
            approval = self.env['ir.config_parameter'].sudo().get_param(
                'account_payment_approval.payment_approval')
            approver_id = int(self.env['ir.config_parameter'].sudo().get_param(
                'account_payment_approval.approval_user_id'))
            self.is_approver_check = True if self.env.user.id == approver_id and approval else False

    is_approver_check = fields.Boolean(compute=_check_is_approver, readonly=True)

    is_approver = fields.Boolean()

    def action_post(self):
        # Post the payments "normally" if no transactions are needed.
        # If not, let the acquirer update the state.

        validation = self._check_payment_approval()
        if validation and self.state:
            if self.state not in ('draft', 'approved'):
                raise UserError(_("Only a draft or approved payment can be posted."))

            payments_need_tx = self.filtered(
                lambda p: p.payment_token_id and not p.payment_transaction_id
            )
            # creating the transaction require to access data on payment acquirers, not always accessible to users
            # able to create payments
            transactions = payments_need_tx.sudo()._create_payment_transaction()

            res = super(AccountPayment, self - payments_need_tx).action_post()

            for tx in transactions:  # Process the transactions with a payment by token
                tx._send_payment_request()

            # Post payments for issued transactions
            transactions._finalize_post_processing()
            payments_tx_done = payments_need_tx.filtered(
                lambda p: p.payment_transaction_id.state == 'done'
            )
            super(AccountPayment, payments_tx_done).action_post()
            payments_tx_not_done = payments_need_tx.filtered(
                lambda p: p.payment_transaction_id.state != 'done'
            )
            payments_tx_not_done.action_cancel()

            return res

    def _check_payment_approval(self):
        if self.state == "draft":
            second_approval = self.env['ir.config_parameter'].sudo().get_param(
                'account_payment_approval.multi_approval')
            first_approval = self.env['ir.config_parameter'].sudo().get_param(
                'account_payment_approval.payment_approval')
            if first_approval:
                amount = float(self.env['ir.config_parameter'].sudo().get_param(
                    'account_payment_approval.approval_amount'))
                payment_currency_id = int(self.env['ir.config_parameter'].sudo().get_param(
                    'account_payment_approval.approval_currency_id'))
                payment_amount = self.amount
                if payment_currency_id:
                    if self.currency_id and self.currency_id.id != payment_currency_id:
                        currency_id = self.env['res.currency'].browse(payment_currency_id)
                        payment_amount = self.currency_id._convert(
                            self.amount, currency_id, self.company_id,
                            self.date or fields.Date.today(), round=True)
                if payment_amount > amount:
                    self.write({
                        'state': 'waiting_approval'
                    })
                    self.is_approver = True
                    return False
            if second_approval:
                val = self.env['payment.approves'].search([], order='amount').mapped('amount')
                approve_payment = self.env['payment.approves'].search([], order='amount')
                for x in val:
                    for rec in approve_payment:
                        index = val.index(x) + 1
                        if index ==len(val):
                            index = index - 1
                        if  self.amount > rec.amount and rec.approve_user_id.id == self.env.user.id:
                            self.is_approver = True
                            if self.amount > rec.amount and self.amount <= val[index] :
                                if rec.approve_user_id.id == self.env.user.id:
                                    self.is_approver = True
                                    payment_amount = self.amount
                                    if rec.approval_currency_id:
                                        if self.currency_id.id != rec.approval_currency_id.id:
                                            currency_id = self.env['res.currency'].browse(rec.approval_currency_id.id)
                                            payment_amount = self.currency_id._convert(
                                                self.amount, currency_id, self.company_id,
                                                self.date or fields.Date.today(), round=True)
                                    if payment_amount > rec.amount:
                                        self.write({
                                            'state': 'waiting_approval'
                                        })
                                        return False
                                else:
                                    self.is_approver = False
                                    self.write({
                                        'state': 'waiting_approval'
                                    })
                                return False
                        elif self.amount < val[0]:
                            self.is_approver = False
                            return True
                        else:
                            self.write({
                                'state': 'waiting_approval'
                            })
                            self.is_approver = False
                            return False
        return True

    def approve_transfer(self):
        if self.is_approver:
            self.write({
                'state': 'approved'
            })

    def reject_transfer(self):
        if self.is_approver:
            self.write({
                'state': 'rejected'
            })
