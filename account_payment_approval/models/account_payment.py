# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    state = fields.Selection(selection_add=[('waiting_approval', 'Waiting For Approval'),
                                            ('approved', 'Approved'),
                                            ('rejected', 'Rejected')],
                             ondelete={'waiting_approval': 'set default', 'approved': 'set default',
                                       'rejected': 'set default'})


class AccountPayment(models.Model):
    _inherit = "account.payment"
    _inherits = {'account.move': 'move_id'}

    origin_invoice_ids = fields.Many2many('account.move', string='Invoice Origin')
    to_reconcile_inv = fields.Many2one('account.move.line', string='Reconcile Move Line')

    def _check_is_approver(self):
        approval = self.env['ir.config_parameter'].sudo().get_param(
            'account_payment_approval.payment_approval')
        approver_id = int(self.env['ir.config_parameter'].sudo().get_param(
            'account_payment_approval.approval_user_id'))
        self.is_approver = True if self.env.user.id == approver_id and approval else False

    is_approver = fields.Boolean(compute=_check_is_approver, readonly=True)

    def action_post(self):
        """Overwrites the _post() to validate the payment in the 'approved' stage too.
        Currently Odoo allows payment posting only in draft stage.
        """

        if self._context.get('active_model') == 'account.move':
            if self._context.get('active_ids'):
                if len(self._context.get('active_ids')) == 1:
                    self.write({
                        'origin_invoice_ids': [(4, self._context.get('active_ids')[0])]
                    })
                    validation = self._check_payment_approval()
                    if not validation:
                        if self.state in ('waiting_approval'):
                            return True
                        if self.state not in ('draft', 'approved'):
                            raise UserError(_("Only a draft or approved payment can be posted."))

                        if any(inv.state != 'posted' for inv in self.reconciled_invoice_ids):
                            raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))
                        self.move_id._post(soft=False)
                    else:
                        self.move_id._post(soft=False)

                if len(self._context.get('active_ids')) > 1:

                    for rec in self:
                        validation = rec._check_payment_approval()


        else:
            validation = self._check_payment_approval()
            if not validation:
                if self.state in ('waiting_approval'):
                    return True
                if self.state not in ('draft', 'approved'):
                    raise UserError(_("Only a draft or approved payment can be posted."))

                if any(inv.state != 'posted' for inv in self.reconciled_invoice_ids):
                    raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))
                self.move_id._post(soft=False)
                self.reconcile_move_payment()
            else:
                self.move_id._post(soft=False)
                self.reconcile_move_payment()

    def reconcile_move_payment(self):
        if self.to_reconcile_inv:
            domain = [('account_internal_type', 'in', ('receivable', 'payable')), ('reconciled', '=', False)]
            payment_lines = self.line_ids.filtered_domain(domain)
            lines = self.to_reconcile_inv

            for account in payment_lines.account_id:
                (payment_lines + lines) \
                    .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)]) \
                    .reconcile()

    def _check_payment_approval(self):
        if not self.state:
            return True
        if self.state == "draft":
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
                    return False
            return True
        return True

    def approve_transfer(self):
        if self.is_approver:
            self.write({
                'state': 'approved'
            })

    def reject_transfer(self):
        self.write({
            'state': 'rejected'
        })


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payments(self):
        self.ensure_one()
        batches = self._get_batches()
        edit_mode = self.can_edit_wizard and (len(batches[0]['lines']) == 1 or self.group_payment)
        to_process = []

        if edit_mode:
            payment_vals = self._create_payment_vals_from_wizard()
            to_process.append({
                'create_vals': payment_vals,
                'to_reconcile': batches[0]['lines'],
                'batch': batches[0],
            })
        else:
            # Don't group payments: Create one batch per move.
            if not self.group_payment:
                new_batches = []
                for batch_result in batches:
                    for line in batch_result['lines']:
                        new_batches.append({
                            **batch_result,
                            'lines': line,
                        })
                batches = new_batches

            for batch_result in batches:
                to_reconcile_inv = batch_result['lines']
                to_process.append({
                    'create_vals': self._create_payment_vals_from_batch(batch_result),
                    'to_reconcile': batch_result['lines'],
                    'batch': batch_result,
                })

        payments = self._init_payments(to_process, edit_mode=edit_mode)
        self._post_payments(to_process, edit_mode=edit_mode)

        for item_rec in to_process:
            item_rec.get('payment').write({
                'to_reconcile_inv': item_rec.get('to_reconcile'),

            })

        for rec in payments:
            if rec.state == 'posted':
                self._reconcile_payments(to_process, edit_mode=edit_mode)
        return payments
