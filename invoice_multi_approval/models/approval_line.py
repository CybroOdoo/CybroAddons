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
"""Approval line model."""
from odoo import api, fields, models
from odoo.exceptions import UserError


class ApprovalLine(models.Model):
    """This class creates a model 'approval.line' and adds fields"""
    _name = 'approval.line'
    _description = 'Approval Line In Move'

    move_id = fields.Many2one(
        'account.move',
        string="Approval lines",
        ondelete='cascade',
        help="Approval line",
    )
    approver_id = fields.Many2one(
        'res.users',
        help="Approver of the invoice",
    )
    approval_status = fields.Boolean(
        string='Status',
        help="Status of approvals",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Prevent unauthorized users from manually creating approval lines."""
        if not self.env.su and not self.env.is_admin():
            is_manager = self.env.user.has_group(
                'invoice_multi_approval.group_approve_manager'
            )
            if not is_manager:
                raise UserError(
                    self.env._("You are not authorized to create approval lines.")
                )
        return super().create(vals_list)

    def unlink(self):
        """Prevent unauthorized users from deleting approval lines."""
        if not self.env.su and not self.env.is_admin():
            is_manager = self.env.user.has_group(
                'invoice_multi_approval.group_approve_manager'
            )
            if not is_manager:
                raise UserError(  # pylint: disable=no-raise-unlink
                    self.env._("You are not authorized to delete approval lines.")
                )
        return super().unlink()

    def write(self, vals):
        """Prevent approvers from modifying approval status of other users."""
        if not self.env.su and not self.env.is_admin():
            is_manager = self.env.user.has_group(
                'invoice_multi_approval.group_approve_manager'
            )
            if not is_manager:
                if any(field in vals for field in ('approver_id', 'move_id')):
                    raise UserError(
                        self.env._("You cannot modify the approver or invoice on approval lines.")
                    )
                for line in self:
                    if line.approver_id != self.env.user:
                        raise UserError(
                            self.env._("You cannot approve or modify approval lines of "
                                       "other users.")
                        )
        return super().write(vals)
