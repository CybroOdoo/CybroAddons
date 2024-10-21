# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ammu Raj(<https://www.cybrosys.com>)
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
from odoo import models, _
from odoo.exceptions import ValidationError


class AccountMoveCancelReset(models.TransientModel):
    """ Wizard for cancel and reset of journal entries"""
    _name = "account.move.cancel.reset"
    _description = "Wizard for cancel journal entries"

    def action_mass_journal_entry_cancel(self):
        """ Cancel all the selected journal entries"""
        for account in self.env['account.move'].browse(
                self._context['active_ids']):
            if account.state == "posted":
                account.button_cancel()
            else:
                raise ValidationError(
                    _("The selected journal entry %s is not in posted state") % account.name)

    def action_mass_journal_entry_reset(self):
        """ Reset all the selected journal entries to draft state"""
        for account in self.env['account.move'].browse(
                self._context['active_ids']):
            if account.state == "cancel":
                account.button_draft()
            else:
                raise ValidationError(
                    _("The selected journal entry %s is not in cancel state") % account.name)
