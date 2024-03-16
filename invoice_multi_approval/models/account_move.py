# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen (<https://www.cybrosys.com>)
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


class AccountMove(models.Model):
    """This class inherits model account.move and adds required fields"""
    _inherit = 'account.move'

    approval_ids = fields.One2many('approval.line',
                                   'move_id', string="Lines",
                                   help="Approval lines")
    document_fully_approved = fields.Boolean(string="Document Fully Approved",
                                             compute='_compute_document_fully_'
                                                     'approved',
                                             help="Enable/disable to approve"
                                                  " document.")
    check_approve_ability = fields.Boolean(string="Check Approve Ability",
                                           compute='_compute_check_approve_'
                                                   'ability',
                                           help="Enable/disable to check "
                                                "approve ability.")
    is_approved = fields.Boolean(string="Is Approved",
                                 compute='_compute_is_approved',
                                 help="Enable/disable to compute approved"
                                      " or not.")
    page_visibility = fields.Boolean(string="Page visibility",
                                     compute='_compute_page_visibility',
                                     help=" To compute page visibility.")
    users_approved = fields.Boolean(string="Users Approved",
                                    help="All the users approved the invoice")

    @api.depends('approval_ids')
    def _compute_page_visibility(self):
        """Compute function for making the approval page visible/invisible"""
        for rec in self:
            rec.page_visibility = True if rec.approval_ids else False

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """This is the onchange function of the partner which loads the
        persons for the approval to the approver table of the account.move"""
        res = super(AccountMove, self)._onchange_partner_id()
        invoice_approval_id = self.env['invoice.approval'].browse(self.env.ref(
            'invoice_multi_approval.default_invoice_multi_approval_config').id)
        self.approval_ids = None
        approval_managers = self.env['res.users'].search([('groups_id', 'in',
                                                           self.env.ref(
                                                               'invoice_multi_'
                                                               'approval.group_approve_manager').id)])
        if invoice_approval_id.no_approve:
            if approval_managers:
                for manager in approval_managers:
                    if not manager.id in self.approval_ids.approver_id.ids:
                        vals = {
                            'approver_id': manager.id
                        }
                        self.approval_ids |= self.approval_ids.new(vals)
            if (invoice_approval_id.approve_customer_invoice and
                    self.move_type == 'out_invoice'):
                for user in invoice_approval_id.invoice_approver_ids:
                    if not user.id in self.approval_ids.approver_id.ids:
                        vals = {
                            'approver_id': user.id
                        }
                        self.approval_ids |= self.approval_ids.new(vals)
            elif (invoice_approval_id.approve_vendor_bill and
                  self.move_type == 'in_invoice'):
                for user in invoice_approval_id.bill_approver_ids:
                    if not user.id in self.approval_ids.approver_id.ids:
                        vals = {
                            'approver_id': user.id
                        }
                        self.approval_ids |= self.approval_ids.new(vals)
            elif (invoice_approval_id.approve_customer_credit and
                  self.move_type == 'out_refund'):
                for user in invoice_approval_id.cust_credit_approver_ids:
                    if not user.id in self.approval_ids.approver_id.ids:
                        vals = {
                            'approver_id': user.id
                        }
                        self.approval_ids |= self.approval_ids.new(vals)
            elif (invoice_approval_id.approve_vendor_credit and
                  self.move_type == 'in_refund'):
                for user in invoice_approval_id.vend_credit_approver_ids:
                    if not user.id in self.approval_ids.approver_id.ids:
                        vals = {
                            'approver_id': user.id
                        }
                        self.approval_ids |= self.approval_ids.new(vals)
        return res

    @api.depends('approval_ids.approver_id')
    def _compute_check_approve_ability(self):
        """This is the compute function which checks if the current
        logged-in user is eligible for approving the document"""
        for rec in self:
            current_user = self.env.uid
            if self.env.ref(
                    'invoice_multi_approval.default_invoice_multi_approval_config').approve_customer_invoice:
                approvers_list = [approver.approver_id.id for approver in
                                  rec.approval_ids]
                rec.check_approve_ability = current_user in approvers_list
            else:
                rec.check_approve_ability = False

    def action_invoice_approve(self):
        """This is the function of the approve button also updates the approval
        table values according to the approval of the users"""
        self.ensure_one()
        current_user = self.env.uid
        for approval_id in self.approval_ids:
            if current_user == approval_id.approver_id.id:
                approval_id.update({'approval_status': True})
        invoice_approval_id = self.env['invoice.approval'].browse(self.env.ref(
            'invoice_multi_approval.default_invoice_multi_approval_config').id)
        approved_users = self.approval_ids.filtered(
            lambda item: item.approval_status).approver_id.ids
        if (invoice_approval_id.approve_customer_invoice and
                self.move_type == 'out_invoice'):
            approval_users = invoice_approval_id.invoice_approver_ids.ids
            if approved_users == approval_users:
                self.users_approved = True
        elif (invoice_approval_id.approve_vendor_bill and
              self.move_type == 'in_invoice'):
            approval_users = invoice_approval_id.bill_approver_ids.ids
            if approved_users == approval_users:
                self.users_approved = True
        elif (invoice_approval_id.approve_customer_credit and
              self.move_type == 'out_refund'):
            approval_users = invoice_approval_id.cust_credit_approver_ids.ids
            if approved_users == approval_users:
                self.users_approved = True
        elif (invoice_approval_id.approve_vendor_credit and
              self.move_type == 'in_refund'):
            approval_users = invoice_approval_id.vend_credit_approver_ids.ids
            if approved_users == approval_users:
                self.users_approved = True

    def _compute_is_approved(self):
        """In this compute function we are verifying whether the document
        is approved/not approved by the current logged in user"""
        for rec in self:
            current_user = rec.env.uid
            if rec.invoice_line_ids and rec.approval_ids:
                for approval_id in rec.approval_ids:
                    if current_user == approval_id.approver_id.id:
                        if approval_id.approval_status:
                            rec.is_approved = True
                            break
                        else:
                            rec.is_approved = False
                    else:
                        rec.is_approved = False
            else:
                rec.is_approved = False

    @api.depends('approval_ids')
    def _compute_document_fully_approved(self):
        """This is the compute function which verifies whether
        the document is completely approved or not"""
        for rec in self:
            length_approval_ids = len(rec.approval_ids)
            approval_ids = rec.approval_ids
            approve_lines = approval_ids.filtered(
                lambda item: item.approval_status)
            length_approve_lines = len(approve_lines)
            rec.document_fully_approved = True \
                if length_approval_ids == length_approve_lines else False
            approval_managers = self.env['res.users'].search(
                [('groups_id', 'in',
                  self.env.ref(
                      'invoice_multi_'
                      'approval.group_approve_manager').id)]).ids
            for approval in approve_lines:
                if approval.approver_id.id in approval_managers:
                    rec.document_fully_approved = True
            if rec.users_approved:
                rec.document_fully_approved = True

    @api.model
    def create(self, vals_list):
        """Super the create function adding approvers while create account
             move through sale /purchase
        :param vals_list: dictionary with the detaisl of current record set
        :return: record"""
        res = super(AccountMove, self).create(vals_list)
        res._onchange_partner_id()
        return res
