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
"""Account move model extension for multi approval workflow."""
from odoo import api, fields, models, Command
from odoo.exceptions import UserError


class AccountMove(models.Model):
    """This class inherits model account.move and adds required fields"""
    _inherit = 'account.move'

    approval_ids = fields.One2many(
        'approval.line',
        'move_id',
        string="Lines",
        readonly=True,
        help="Approval lines",
    )
    document_fully_approved = fields.Boolean(
        compute='_compute_document_fully_approved',
        help="Enable/disable to approve document.",
    )
    check_approve_ability = fields.Boolean(
        compute='_compute_check_approve_ability',
        help="Enable/disable to check approve ability.",
    )
    is_approved = fields.Boolean(
        compute='_compute_is_approved',
        help="Enable/disable to compute approved or not.",
    )
    page_visibility = fields.Boolean(
        string="Page visibility",
        compute='_compute_page_visibility',
        help="To compute page visibility.",
    )
    users_approved = fields.Boolean(
        compute='_compute_users_approved',
        readonly=True,
        help="All the users approved the invoice",
    )

    def _get_applicable_approvers(self):
        """Return (all_approvers, is_enabled) for this move based on
        configuration."""
        self.ensure_one()
        config = self.env.ref(
            'invoice_multi_approval.default_invoice_multi_approval_config',
            raise_if_not_found=False,
        )
        if not config:
            return self.env['res.users'], False

        is_enabled = False
        approvers = self.env['res.users']
        if self.move_type == 'out_invoice' and config.approve_customer_invoice:
            is_enabled = True
            approvers = config.invoice_approver_ids
        elif self.move_type == 'in_invoice' and config.approve_vendor_bill:
            is_enabled = True
            approvers = config.bill_approver_ids
        elif self.move_type == 'out_refund' and config.approve_customer_credit:
            is_enabled = True
            approvers = config.cust_credit_approver_ids
        elif self.move_type == 'in_refund' and config.approve_vendor_credit:
            is_enabled = True
            approvers = config.vend_credit_approver_ids

        if not is_enabled:
            return self.env['res.users'], False

        manager_group = self.env.ref(
            'invoice_multi_approval.group_approve_manager',
            raise_if_not_found=False,
        )
        approval_managers = self.env['res.users'].search([
            ('all_group_ids', 'in', manager_group.id)
        ]) if manager_group else self.env['res.users']

        return (approval_managers | approvers), True

    def _set_approval_lines(self):
        """Populate approvers according to module configuration while
        preserving already granted approvals."""
        for move in self:
            all_approvers, is_enabled = move._get_applicable_approvers()
            if not is_enabled:
                move.sudo().approval_ids = [Command.clear()]
                continue

            invalid_lines = move.approval_ids.filtered(
                lambda line: not line.approver_id
            )
            commands = [Command.unlink(line.id) for line in invalid_lines if line.id]

            existing_approvers = move.approval_ids.filtered(
                'approver_id'
            ).mapped('approver_id')
            new_approvers = all_approvers - existing_approvers
            if new_approvers:
                commands.extend([
                    Command.create({'approver_id': user.id})
                    for user in new_approvers
                ])
            if commands:
                move.sudo().approval_ids = commands

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Onchange function of partner which loads approvers if enabled"""
        res = super()._onchange_partner_id()
        if (not self.approval_ids or
                any(not line.approver_id for line in self.approval_ids)):
            self._set_approval_lines()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """Super create to populate approvers when creating an account.move"""
        clean_vals_list = []
        for vals in vals_list:
            vals_copy = dict(vals)
            vals_copy.pop('approval_ids', None)
            clean_vals_list.append(vals_copy)
        records = super().create(clean_vals_list)
        for record in records:
            if (not record.approval_ids or
                    any(not line.approver_id for line in record.approval_ids)):
                record._set_approval_lines()
        return records

    def write(self, vals):
        """Prevent writing users_approved or approval_ids directly via RPC."""
        vals_to_write = dict(vals)
        vals_to_write.pop('users_approved', None)
        if not self.env.su and not self.env.is_admin():
            is_manager = self.env.user.has_group(
                'invoice_multi_approval.group_approve_manager'
            )
            if not is_manager:
                vals_to_write.pop('approval_ids', None)
        res = super().write(vals_to_write)
        if 'partner_id' in vals:
            for record in self:
                if (not record.approval_ids or
                        any(not line.approver_id for line in record.approval_ids)):
                    record._set_approval_lines()
        return res

    @api.depends('approval_ids')
    def _compute_page_visibility(self):
        """Compute function for making the approval page visible/invisible"""
        for rec in self:
            rec.page_visibility = bool(rec.approval_ids)

    @api.depends('approval_ids.approver_id', 'move_type')
    def _compute_check_approve_ability(self):
        """Checks if the logged-in user is eligible to approve"""
        is_manager = self.env.user.has_group(
            'invoice_multi_approval.group_approve_manager'
        )
        for rec in self:
            _approvers, is_enabled = rec._get_applicable_approvers()
            if is_enabled:
                rec.check_approve_ability = (
                    is_manager or (
                        self.env.uid in rec.approval_ids.approver_id.ids
                    )
                )
            else:
                rec.check_approve_ability = False

    def action_invoice_approve(self):
        """Approve document for current user and update approval status"""
        self.ensure_one()
        current_user = self.env.user
        matching_lines = self.approval_ids.filtered(
            lambda line: line.approver_id == current_user
        )
        if matching_lines:
            matching_lines.approval_status = True
        elif current_user.has_group(
            'invoice_multi_approval.group_approve_manager'
        ):
            self.sudo().approval_ids = [Command.create({
                'approver_id': current_user.id,
                'approval_status': True,
            })]
        else:
            raise UserError(
                self.env._("You are not authorized to approve this document.")
            )

    @api.depends(
        'approval_ids.approval_status',
        'approval_ids.approver_id',
        'move_type',
    )
    def _compute_users_approved(self):
        """Verifies whether all configured required approvers have approved."""
        config = self.env.ref(
            'invoice_multi_approval.default_invoice_multi_approval_config',
            raise_if_not_found=False,
        )
        for move in self:
            if not config:
                move.users_approved = False
                continue
            req_users = self.env['res.users']
            if (move.move_type == 'out_invoice' and
                    config.approve_customer_invoice):
                req_users = config.invoice_approver_ids
            elif (move.move_type == 'in_invoice' and
                  config.approve_vendor_bill):
                req_users = config.bill_approver_ids
            elif (move.move_type == 'out_refund' and
                  config.approve_customer_credit):
                req_users = config.cust_credit_approver_ids
            elif (move.move_type == 'in_refund' and
                  config.approve_vendor_credit):
                req_users = config.vend_credit_approver_ids

            if not req_users:
                move.users_approved = False
                continue

            approved_user_ids = set(
                move.approval_ids.filtered('approval_status').approver_id.ids
            )
            move.users_approved = set(req_users.ids).issubset(
                approved_user_ids
            )

    @api.depends('approval_ids.approval_status', 'approval_ids.approver_id')
    def _compute_is_approved(self):
        """Verifies whether the document is approved by current user"""
        for rec in self:
            user_approval = rec.approval_ids.filtered(
                lambda line: line.approver_id.id == self.env.uid
            )
            rec.is_approved = any(user_approval.mapped('approval_status'))

    @api.depends(
        'approval_ids.approval_status',
        'move_type',
        'users_approved',
    )
    def _compute_document_fully_approved(self):
        """Verifies whether the document is completely approved"""
        manager_group = self.env.ref(
            'invoice_multi_approval.group_approve_manager',
            raise_if_not_found=False,
        )
        manager_ids = set(self.env['res.users'].search([
            ('all_group_ids', 'in', manager_group.id)
        ]).ids) if manager_group else set()
        for rec in self:
            _approvers, is_enabled = rec._get_applicable_approvers()
            if not is_enabled:
                rec.document_fully_approved = True
                continue

            if not rec.approval_ids:
                rec.document_fully_approved = False
                continue

            approve_lines = rec.approval_ids.filtered('approval_status')
            if len(rec.approval_ids) == len(approve_lines):
                rec.document_fully_approved = True
                continue

            if manager_ids and any(line.approver_id.id in manager_ids
                                   for line in approve_lines):
                rec.document_fully_approved = True
                continue

            if rec.users_approved:
                rec.document_fully_approved = True
                continue

            rec.document_fully_approved = False

    @api.depends('state', 'date', 'auto_post', 'document_fully_approved')
    def _compute_hide_post_button(self):
        """Hide post/confirm button until move is fully approved."""
        res = super()._compute_hide_post_button()
        for record in self:
            if not record.document_fully_approved:
                record.hide_post_button = True
        return res

    def action_post(self):
        """Server-side check ensuring approval before posting"""
        for move in self:
            if not move.document_fully_approved:
                raise UserError(
                    self.env._("You cannot confirm this document (%s) until it is "
                               "fully approved.", move.display_name)
                )
        return super().action_post()
