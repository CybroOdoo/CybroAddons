# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    """ Adding journal fields where we can select allowed journal """

    _inherit = 'res.users'

    check_user = fields.Boolean(string="Check", compute='_compute_check_user',
                                help="Check the field is true or false")
    journal_ids = fields.Many2many(
        'account.journal',
        string='Restricted Journals',
        help='Only the selected journal will be visible'
             ' to the particular user')

    def write(self, vals):
        """
            Override the write method to restrict users with specific groups.
            :param vals: Dictionary of field values to update.
            :type vals: dict
            :raises: ValidationError if the current user has both
            'account_restrict_journal.user_allowed_journal'
                     and 'base.group_system' groups and attempts to restrict
                     journals of the Administrator.
            :return: None
            """
        super().write(vals)
        if self.env.user.has_group(
                'account_restrict_journal.user_allowed_journal') and \
                self.env.user.has_group('base.group_system'):
            user_groups = self.env.user.groups_id.filtered(
                lambda g: g.name == 'Restrict Journals')
            if user_groups:
                raise ValidationError(
                    _("You are not allowed to restrict journals for the "
                      "Administrator."))

    def _compute_check_user(self):
        """Function for viewing the page for restrict journal users."""
        self.check_user = False
        if (self.env.ref('account_restrict_journal.user_allowed_journal').id in
                self.groups_id.mapped('id')):
            self.check_user = True
