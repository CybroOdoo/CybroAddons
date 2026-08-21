# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models, api

class ResUsers(models.Model):
    """Extends res.users with info-specific helpers and computed fields.

    Adds a count of shared articles for the user and utility methods for checking
    info access group membership.
    """
    _inherit = 'res.users'

    shared_article_count = fields.Integer(
        string='Shared Articles Count',
        compute='_compute_shared_article_count',
        store=False,
        help='Total number of shared articles accessible by this user.',
    )

    @api.depends('partner_id')
    def _compute_shared_article_count(self):
        """Compute the number of info articles the user has been granted access to."""
        for user in self:
            user.shared_article_count = self.env['info.hub.article.member'].sudo().search_count([
                ('partner_id', '=', user.partner_id.id),
                ('permission', '!=', 'none'),
            ])

    def _get_member_article_ids(self):
        """ Return a list of article IDs for which this user has an explicit member record."""
        self.ensure_one()
        members = self.env['info.hub.article.member'].sudo().search([
            ('partner_id', '=', self.partner_id.id)
        ])
        return members.mapped('article_id').ids

    def is_info_shared_user(self):
        """Return True if this user belongs to the 'Information Shared User' group."""
        self.ensure_one()
        return self.has_group('info_hub.group_info_shared_user')
