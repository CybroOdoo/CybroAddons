# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class ResUsers(models.Model):
    """ Adding journal fields in res. users where we can select a journal
         that can be accessed by the user"""
    _inherit = 'res.users'

    allowed_journal_ids = fields.Many2many(
        'account.journal', string='Allowed Journals',
        help='Only the selected journal will be visible to the'
             ' particular user')
    is_admin = fields.Boolean(compute='_compute_is_admin', string='Is Admin',
                              help='Check the user is admin or not')

    def write(self, vals):
        """Write the values of restrict journal to the corresponding users"""
        res = super(ResUsers, self).write(vals)
        for user in self:
            if user:
                journals = self.env['account.journal'].sudo(). \
                    search([('restrict_user_ids', 'in', user.id)])
                if user.allowed_journal_ids:
                    for journal in journals:
                        journal.is_account_journal = True
                    for journal in self.env['account.journal'].sudo(). \
                            search([('restrict_user_ids', 'not in',
                                     [rec.id for rec in journals])]):
                        journal.is_account_journal = False
                else:
                    for journal in self.env['account.journal'].sudo().search(
                            []):
                        journal.is_account_journal = True
                for user_journal in self.allowed_journal_ids:
                    user_journal.sudo().write({
                        'restrict_user_ids': [(4, user.id)]
                    })
            return res

    def _compute_is_admin(self):
        """ Compute the value of is_admin based on the user id admin or not"""
        for admin in self:
            admin.is_admin = False
            if admin.id == self.env.ref('base.user_admin').id:
                admin.is_admin = True
