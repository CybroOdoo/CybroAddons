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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models
from odoo.exceptions import ValidationError


class AccountMoveCancelReset(models.TransientModel):
    """ Wizard for cancel and reset of journal entries"""
    _name = "account.move.cancel.reset"
    _description = "Cancel and Reset Journal Entries"

    def action_mass_journal_entry_cancel(self):
        """ Cancel all the selected journal entries"""
        moves = self.env['account.move'].browse(
            self.env.context.get('active_ids', []))
        invalid_moves = moves.filtered(lambda move: move.state != "posted")
        if invalid_moves:
            raise ValidationError(self.env._(
                "Only posted journal entries can be cancelled. "
                "These entries are not posted: %s",
                ", ".join(invalid_moves.mapped('display_name'))))
        moves.button_cancel()

    def action_mass_journal_entry_reset(self):
        """ Reset all the selected journal entries to draft state"""
        moves = self.env['account.move'].browse(
            self.env.context.get('active_ids', []))
        invalid_moves = moves.filtered(lambda move: move.state != "cancel")
        if invalid_moves:
            raise ValidationError(self.env._(
                "Only cancelled journal entries can be reset to draft. "
                "These entries are not cancelled: %s",
                ", ".join(invalid_moves.mapped('display_name'))))
        moves.button_draft()
