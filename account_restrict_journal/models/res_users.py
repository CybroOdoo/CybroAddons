# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
                                   help="Check the field is true or false")
    journal_ids = fields.Many2many(
        'account.journal',
        string='Restricted Journals',
        help='Only the selected journal will be visible'
             ' to the particular user')

    def _compute_is_check_user(self):
        """Function for viewing the page for restrict journal users."""
        self.is_check_user = False
        if (self.env.ref(
                'account_restrict_journal.account_restrict_journal_group_admin').id in
                self.groups_id.mapped('id')):
            self.is_check_user = True
