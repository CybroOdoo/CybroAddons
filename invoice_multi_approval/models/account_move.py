# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sayooj A O(<https://www.cybrosys.com>)
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
    _inherit = 'account.move'

    approval_ids = fields.One2many('approval.line', 'move_id')
    document_fully_approved = fields.Boolean(compute='_compute_document_fully_approved')
    check_approve_ability = fields.Boolean(compute='_compute_check_approve_ability')
    is_approved = fields.Boolean(compute='_compute_is_approved')
    page_visibility = fields.Boolean(compute='_compute_page_visibility')

    @api.depends('approval_ids')
    def _compute_page_visibility(self):
        """Compute function for making the approval page visible/invisible"""
        if self.approval_ids:
            self.page_visibility = True
        else:
            self.page_visibility = False

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """This is the onchange function of the partner which loads the
        persons for the approval to the approver table of the account.move"""
        res = super(AccountMove, self)._onchange_partner_id()
        invoice_approval_id = self.env['invoice.approval'].search([])
        self.approval_ids = None
        if invoice_approval_id.approve_customer_invoice and self.move_type == 'out_invoice':
            for user in invoice_approval_id.invoice_approver_ids:
                vals = {
                    'approver_id': user.id
                }
                self.approval_ids |= self.approval_ids.new(vals)
        elif invoice_approval_id.approve_vendor_bill and self.move_type == 'in_invoice':
            for user in invoice_approval_id.bill_approver_ids:
                vals = {
                    'approver_id': user.id
                }
                self.approval_ids |= self.approval_ids.new(vals)
        elif invoice_approval_id.approve_customer_credit and self.move_type == 'out_refund':
            for user in invoice_approval_id.cust_credit_approver_ids:
                vals = {
                    'approver_id': user.id
                }
                self.approval_ids |= self.approval_ids.new(vals)
        elif invoice_approval_id.approve_vendor_credit and self.move_type == 'in_refund':
            for user in invoice_approval_id.vend_credit_approver_ids:
                vals = {
                    'approver_id': user.id
                }
                self.approval_ids |= self.approval_ids.new(vals)
        return res

    @api.depends('approval_ids.approver_id')
    def _compute_check_approve_ability(self):
        """This is the compute function which check the current
        logged in user is eligible or not for approving the document"""
        current_user = self.env.uid
        approvers_list = []
        for approver in self.approval_ids:
            approvers_list.append(approver.approver_id.id)
        if current_user in approvers_list:
            self.check_approve_ability = True
        else:
            self.check_approve_ability = False

    def invoice_approve(self):
        """This is the function of the approve button also
        updates the approval table values according to the
        approval of the users"""
        self.ensure_one()
        current_user = self.env.uid
        for approval_id in self.approval_ids:
            if current_user == approval_id.approver_id.id:
                approval_id.update({'approval_status': True})

    def _compute_is_approved(self):
        """In this compute function we are verifying whether the document
        is approved/not approved by the current logged in user"""
        current_user = self.env.uid
        if self.invoice_line_ids and self.approval_ids:
            for approval_id in self.approval_ids:
                if current_user == approval_id.approver_id.id:
                    if approval_id.approval_status:
                        self.is_approved = True
                        break
                    else:
                        self.is_approved = False
                else:
                    self.is_approved = False
        else:
            self.is_approved = False

    @api.depends('approval_ids')
    def _compute_document_fully_approved(self):
        """This is the compute function which verifies whether
        the document is completely approved or not"""
        length_approval_ids = len(self.approval_ids)
        approval_ids = self.approval_ids
        approve_lines = approval_ids.filtered(lambda item: item.approval_status)
        length_approve_lines = len(approve_lines)
        if length_approval_ids == length_approve_lines:
            self.document_fully_approved = True
        else:
            self.document_fully_approved = False


class ApprovalLine(models.Model):
    _name = 'approval.line'
    _description = 'Approval line in Move'

    move_id = fields.Many2one('account.move')
    approver_id = fields.Many2one('res.users', string='Approver')
    approval_status = fields.Boolean(string='Status')
