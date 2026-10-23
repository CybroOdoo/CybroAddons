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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import _, fields, models
from odoo.exceptions import UserError

GROUP_MANAGER = (
    'double_validation_invoice.double_validation_invoice_group_manager'
)
GROUP_FINANCE_MANAGER = (
    'double_validation_invoice.'
    'double_validation_invoice_group_finance_manager'
)


class AccountMove(models.Model):
    """Inherits 'account.move' to add new approval states and validation
    flow."""
    _inherit = 'account.move'

    state = fields.Selection(
        selection_add=[
            ('first_approval', 'First Approval'),
            ('second_approval', 'Second Approval'),
        ],
        help="First Approval is the state when the invoice requires the "
             "first approval, Second Approval is the state after confirmation "
             "of the First Approval if the amount is greater than second "
             "amount limit, Posted: invoice is posted after the confirmation "
             "of the approvals.",
        ondelete={'first_approval': 'cascade', 'second_approval': 'cascade'},
    )
    status_in_payment = fields.Selection(
        selection_add=[
            ('first_approval', 'First Approval'),
            ('second_approval', 'Second Approval'),
        ],
        ondelete={'first_approval': 'cascade', 'second_approval': 'cascade'},
    )

    def action_post(self):
        """Method for validating invoices, checks if total amount is greater
        than first validation amount."""
        icp = self.env['ir.config_parameter'].sudo()
        double_valid = icp.get_bool(
            'double_validation_invoice.double_validation', False
        )
        first_valid_amt = icp.get_float(
            'double_validation_invoice.first_valid_limit', 0.0
        )
        second_valid_amt = icp.get_float(
            'double_validation_invoice.second_valid_limit', 0.0
        )

        if double_valid:
            # Block direct posting of invoices that are in approval states
            approval_moves = self.filtered(
                lambda m: m.is_invoice(include_receipts=True)
                and m.state in ('first_approval', 'second_approval')
            )
            if approval_moves:
                if not self.env.context.get('from_approval'):
                    raise UserError(_(
                        "Invoices waiting for approval cannot be posted "
                        "directly. They must be approved by an authorized "
                        "manager."
                    ))
                for move in approval_moves:
                    if move.state == 'first_approval':
                        if not (self.env.user.has_group(GROUP_MANAGER)
                                or self.env.is_superuser()):
                            raise UserError(_(
                                "Only a Manager can approve this invoice."
                            ))
                        if move.amount_total > second_valid_amt:
                            raise UserError(_(
                                "This invoice exceeds the second validation "
                                "limit and requires Second Approval."
                            ))
                    elif move.state == 'second_approval':
                        if not (self.env.user.has_group(GROUP_FINANCE_MANAGER)
                                or self.env.is_superuser()):
                            raise UserError(_(
                                "Only a Finance Manager can approve this "
                                "invoice."
                            ))

            moves_to_approve = self.filtered(
                lambda m: m.is_invoice(include_receipts=True)
                and m.state == 'draft'
                and m.amount_total > first_valid_amt
            )
            if moves_to_approve:
                moves_to_approve.write({'state': 'first_approval'})
            moves_to_post = self - moves_to_approve
        else:
            moves_to_post = self

        if moves_to_post:
            return super(AccountMove, moves_to_post).action_post()
        return True

    def action_first_approval(self):
        """Method for first validation of invoice."""
        if not (self.env.user.has_group(GROUP_MANAGER)
                or self.env.is_superuser()):
            raise UserError(_("Only a Manager can approve this invoice."))
        if any(m.state != 'first_approval' for m in self):
            raise UserError(_(
                "Only invoices in 'First Approval' state can be approved."
            ))

        icp = self.env['ir.config_parameter'].sudo()
        second_valid_amount = icp.get_float(
            'double_validation_invoice.second_valid_limit', 0.0
        )
        to_second_approval = self.filtered(
            lambda m: m.amount_total > second_valid_amount
        )
        if to_second_approval:
            to_second_approval.write({'state': 'second_approval'})
        to_post = self - to_second_approval
        if to_post:
            to_post.with_context(from_approval=True).action_post()
        return True

    def action_second_approval(self):
        """Method for second validation of invoice."""
        if not (self.env.user.has_group(GROUP_FINANCE_MANAGER)
                or self.env.is_superuser()):
            raise UserError(_(
                "Only a Finance Manager can approve this invoice."
            ))
        if any(m.state != 'second_approval' for m in self):
            raise UserError(_(
                "Only invoices in 'Second Approval' state can be approved."
            ))
        return self.with_context(from_approval=True).action_post()

    def action_reject(self):
        """Method to reject an invoice in approval state and reset to draft."""
        for move in self:
            if move.state not in ('first_approval', 'second_approval'):
                raise UserError(_(
                    "Only invoices in approval states can be rejected."
                ))
        return self.button_draft()

    def _compute_show_reset_to_draft_button(self):
        super()._compute_show_reset_to_draft_button()
        is_manager = (
            self.env.user.has_group(GROUP_MANAGER) or self.env.is_superuser()
        )
        is_finance_manager = (
            self.env.user.has_group(GROUP_FINANCE_MANAGER)
            or self.env.is_superuser()
        )
        for move in self:
            if move.state == 'first_approval':
                move.show_reset_to_draft_button = is_manager
            elif move.state == 'second_approval':
                move.show_reset_to_draft_button = is_finance_manager

    def button_draft(self):
        for move in self:
            if move.state == 'first_approval':
                if not (self.env.user.has_group(GROUP_MANAGER)
                        or self.env.is_superuser()):
                    raise UserError(_(
                        "Only a Manager can reset an invoice in 'First "
                        "Approval' state to draft."
                    ))
            elif move.state == 'second_approval':
                if not (self.env.user.has_group(GROUP_FINANCE_MANAGER)
                        or self.env.is_superuser()):
                    raise UserError(_(
                        "Only a Finance Manager can reset an invoice in "
                        "'Second Approval' state to draft."
                    ))

        approvals = self.filtered(
            lambda m: m.state in ('first_approval', 'second_approval')
        )
        if approvals:
            approvals.write({'state': 'draft'})
        remaining = self - approvals
        if remaining:
            return super(AccountMove, remaining).button_draft()
        return True
