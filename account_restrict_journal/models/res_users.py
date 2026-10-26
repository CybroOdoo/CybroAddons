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
from odoo import Command, api, fields, models


class ResUsers(models.Model):
    """Add the restricted journals configuration to the users."""
    _inherit = 'res.users'

    is_check_user = fields.Boolean(
        string="Check",
        compute='_compute_is_check_user',
        inverse='_inverse_is_check_user',
        help="Enabled when the user belongs to the Restrict Journals group.")
    journal_ids = fields.Many2many(
        'account.journal',
        string="Restricted Journals",
        help="Selected journals are read-only for this user; "
             "all others remain fully accessible.")

    @api.depends('group_ids')
    def _compute_is_check_user(self):
        """Flag the users that belong to the Restrict Journals group."""
        group = self.env.ref('account_restrict_journal.account_restrict_journal_group_admin')
        for user in self:
            user.is_check_user = group in user.group_ids

    def _inverse_is_check_user(self):
        """Add or remove the user from the Restrict Journals group."""
        group = self.env.ref('account_restrict_journal.account_restrict_journal_group_admin')
        for user in self:
            if user.is_check_user:
                user.group_ids = [Command.link(group.id)]
            else:
                user.group_ids = [Command.unlink(group.id)]

    def write(self, vals):
        """Clear the restricted journals of users who left the group."""
        result = super().write(vals)
        if 'group_ids' in vals:
            group = self.env.ref(
                'account_restrict_journal.account_restrict_journal_group_admin',
                raise_if_not_found=False)
            if group:
                users = self.filtered(lambda user: user.journal_ids and group not in user.group_ids)
                users.journal_ids = [Command.clear()]
        return result
