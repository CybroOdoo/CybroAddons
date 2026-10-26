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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    """Extend journal entries to block records of restricted journals."""
    _inherit = 'account.move'

    is_check_journal = fields.Boolean(
        string="Check Journal",
        compute='_compute_is_check_journal',
        help="Technical field that raises a validation error when the entry "
             "or a payment reconciled with it belongs to a journal that is "
             "restricted for the current user.")

    @api.depends_context('uid')
    @api.depends('journal_id', 'line_ids.full_reconcile_id')
    def _compute_is_check_journal(self):
        """Raise a validation error for records of restricted journals."""
        restricted_journals = self.env.user.journal_ids
        for move in self:
            move.is_check_journal = True
            reconciled_moves = move.line_ids.full_reconcile_id.reconciled_line_ids.move_id
            journals = move.journal_id | reconciled_moves.origin_payment_id.journal_id
            if journals & restricted_journals:
                raise ValidationError(self.env._("Restricted journals found."))

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Clear the journal when it is restricted for the current user."""
        result = super()._onchange_partner_id()
        if self.journal_id & self.env.user.journal_ids:
            self.journal_id = False
        return result
