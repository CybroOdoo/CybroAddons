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
from odoo import fields, models



class ResUsers(models.Model):
    """ Adding journal fields where we can select allowed journal """
    _inherit = 'res.users'

    is_check_user = fields.Boolean(string="Check",
                                   compute='_compute_is_check_user',
                                   inverse='_inverse_is_check_user',
                                   help="Check the field is true or false")
    journal_ids = fields.Many2many(
        'account.journal',
        string='Restricted Journals',
        help='Only the selected journal will be visible'
             ' to the particular user')

    def _compute_is_check_user(self):
        """Compute the is_check_user field and
        clear journal_ids if necessary."""
        for user in self:
            admin_group = user.env.ref(
                'account_restrict_journal.account_restrict_journal_group_admin'
            ).id
            user_groups = user.group_ids.ids

            if admin_group in user_groups:
                user.is_check_user = True
            else:
                user.is_check_user = False
                user.journal_ids = False

    def _inverse_is_check_user(self):
        """Add or remove the user from the restriction group when the boolean is toggled."""
        admin_group = self.env.ref('account_restrict_journal.account_restrict_journal_group_admin')
        for user in self:
            if user.is_check_user:
                user.group_ids = [(4, admin_group.id)]
            else:
                user.group_ids = [(3, admin_group.id)]
                user.journal_ids = False
