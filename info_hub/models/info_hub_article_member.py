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

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class InformationArticleMember(models.Model):
    """
    Stores the access permission a partner has on a specific info article.

    A member record links a res.partner to a info.hub.article with one of three
    permission levels: ``edit`` (full write access), ``read`` (view-only), or
    ``none`` (explicitly blocked). The article owner's record is protected and
    cannot be removed or demoted below ``edit``.
    """

    _name = 'info.hub.article.member'
    _description = 'Article Member Permission'
    _rec_name = 'partner_id'
    _order = 'permission desc, partner_id'

    article_id = fields.Many2one(
        comodel_name='info.hub.article',
        string='Article',
        domain="[('is_template', '=', False), ('is_article_item', '=', False)]",
        required=True,
        ondelete='cascade',
        index=True,
        help='The article to which permission is granted.',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='User / Partner',
        required=True,
        ondelete='cascade',
        index=True,
        help='The partner or user granted access to the article.',
    )
    permission = fields.Selection(
        selection=[
            ('edit', 'Can edit'),
            ('read', 'Can read'),
            ('none', 'No access'),
        ],
        string='Permission Level',
        required=True,
        default='read',
        help='Permission level granted to this member (edit, read, or none).',
    )

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        compute='_compute_user_id',
        store=True,
        readonly=True,
        help='The res.users record corresponding to the member partner.',
    )

    partner_email = fields.Char(
        related='partner_id.email',
        string='Email',
        readonly=True,
        help='Email address of the member partner.',
    )

    member_type = fields.Selection(
        selection=[
            ('admin', 'Admin'),
            ('employee', 'Employee'),
            ('guest', 'Guest'),
        ],
        string='User Type',
        compute='_compute_member_type',
        store=True,
        help='Classification of the member (Admin, Employee, or Guest).',
    )

    @api.depends('partner_id')
    def _compute_user_id(self):
        """Resolve the partner to a res.users record (first user linked to the partner)."""
        for member in self:
            member.user_id = member.partner_id.user_ids[:1]

    @api.depends('partner_id', 'user_id')
    def _compute_member_type(self):
        """Classify the member as admin, employee, or guest based on their user groups."""
        for member in self:
            user = member.user_id or member.partner_id.user_ids[:1]
            if not user:
                member.member_type = 'guest'
            elif user.has_group('base.group_system') or user.has_group('info_hub.group_info_admin'):
                member.member_type = 'admin'
            elif user.has_group('base.group_user'):
                member.member_type = 'employee'
            else:
                member.member_type = 'guest'

    def write(self, vals):
        if 'permission' in vals:
            for member in self:
                if member.partner_id == member.article_id.create_uid.partner_id:
                    if vals['permission'] != 'edit':
                        raise UserError(_("The article owner must always have 'Can edit' permission and it cannot be modified."))
        return super().write(vals)

    def unlink(self):
        """Block removal of the article owner and demote shared articles to private when all non-owner members are removed."""
        for member in self:
            if member.partner_id == member.article_id.create_uid.partner_id:
                raise UserError(_("The article owner cannot be removed from the members list."))
        articles = self.mapped('article_id')
        res = super().unlink()
        for article in articles:
            if article.category == 'shared':
                owner_partner = article.author_id.partner_id or article.create_uid.partner_id
                other_members = article.member_ids.filtered(lambda m: m.partner_id != owner_partner)
                if not other_members:
                    article.write({'category': 'private'})
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """Promote portal-only partners to the shared-user group on membership creation."""
        records = super().create(vals_list)
        shared_group = self.env.ref('info_hub.group_info_shared_user')
        for record in records:
            if record.partner_id:
                for user in record.partner_id.user_ids:
                    if user.has_group('base.group_user') and not (user.has_group('info_hub.group_info_user') or user.has_group('info_hub.group_info_admin')):
                        user.write({'group_ids': [(4, shared_group.id)]})
            article = record.article_id
            if article.category == 'private' and record.partner_id != (article.author_id.partner_id or article.create_uid.partner_id):
                article.write({'category': 'shared'})
        return records

    _unique_article_partner = models.Constraint(
        'UNIQUE(article_id, partner_id)',
        'A partner can only have one permission record per article.',
    )
