# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
from odoo import fields, models, _
from odoo.exceptions import ValidationError, UserError


class AccountPayment(models.Model):
    """This class inherits model "account.payment" and adds required fields """
    _inherit = "account.payment"
    _inherits = {'account.move': 'move_id'}

    def _compute_is_approve_person(self):
        """This function fetches the value of the
        'account_payment_approval.payment_approval' parameter using the
        get_param method and converts to integer, it checks if the current
        user's ID matches the ID stored in the 'approval_user_id'
        parameter. If both conditions are met, it sets the is_approve_person
         field to True"""
        approval = self.env['ir.config_parameter'].sudo().get_param(
            'account_payment_approval.payment_approval')
        approver_id = int(self.env['ir.config_parameter'].sudo().get_param(
            'account_payment_approval.approval_user_id'))
        self.is_approve_person = True if (self.env.user.id == approver_id and
                                          approval) else False

    is_approve_person = fields.Boolean(string='Approving Person',
                                       compute=_compute_is_approve_person,
                                       readonly=True,
                                       help="Enable/disable if approving"
                                            " person.")

    def action_post(self):
        """Overwrites the _post() to validate the payment in the 'approved'
         stage too.
        currently Odoo allows payment posting only in draft stage."""
        validation = self._check_payment_approval()
        if validation:
            if self.state == (
                    'posted', 'cancel', 'waiting_approval', 'rejected'):
                raise UserError(
                    _("Only a draft or approved payment can be posted."))
            if any(inv.state != 'posted' for inv in
                   self.reconciled_invoice_ids):
                raise ValidationError(_("The payment cannot be processed "
                                        "because the invoice is not open!"))
            self.move_id._post(soft=False)

    def _check_payment_approval(self):
        """This function checks the payment approval if payment_amount grater
         than amount,then state changed to waiting_approval """
        self.ensure_one()
        if self.state == "draft":
            first_approval = self.env['ir.config_parameter'].sudo().get_param(
                'account_payment_approval.payment_approval')
            if first_approval:
                amount = float(self.env['ir.config_parameter'].sudo().get_param(
                    'account_payment_approval.approval_amount'))
                payment_currency_id = int(
                    self.env['ir.config_parameter'].sudo().get_param(
                        'account_payment_approval.approval_currency_id'))
                payment_amount = self.amount
                if payment_currency_id:
                    if (self.currency_id and
                            self.currency_id.id != payment_currency_id):
                        currency_id = self.env['res.currency'].browse(
                            payment_currency_id)
                        payment_amount = (self.currency_id._convert(
                            self.amount, currency_id, self.company_id,
                            self.date or fields.Date.today(), round=True))
                if payment_amount > amount:
                    self.write({
                        'state': 'waiting_approval'
                    })
                    return False
        return True

    def approve_transfer(self):
        """This function changes state to approved state if approving person
         approves payment"""
        if self.is_approve_person:
            self.write({
                'state': 'approved'
            })

    def reject_transfer(self):
        """This function changes state to rejected state if approving person
                reject approval"""
        self.write({
            'state': 'rejected'
        })
