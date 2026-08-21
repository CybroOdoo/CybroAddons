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

import uuid
from odoo import api, fields, models

class InformationArticle(models.Model):
    """Core model for info base articles in the community edition."""

    _name = 'info.hub.article'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Information Article'
    _parent_store = True
    _order = 'sequence, id'
    _rec_name = 'name'

    name = fields.Char(
        string='Title',
        required=True,
        translate=True,
        help='Title of the article.',
    )
    icon = fields.Char(
        string='Emoji Icon',
        size=5,
        default='📄',
        help='A single emoji to represent this article in lists and the sidebar.',
    )
    body = fields.Html(
        string='Content',
        sanitize=True,
        sanitize_tags=True,
        help='HTML content of the article.',
    )
    cover_image = fields.Image(
        string='Cover Image',
        max_width=1200,
        max_height=400,
        help='Cover image displayed at the top of the article.',
    )
    cover_image_position = fields.Float(
        string="Cover Image Position",
        default=50.0,
        help="Vertical position of the cover image (0=top, 50=center, 100=bottom)",
    )

    parent_id = fields.Many2one(
        comodel_name='info.hub.article',
        string='Parent Article',
        ondelete='cascade',
        index=True,
        help='Parent article in the hierarchy tree.',
    )
    child_ids = fields.One2many(
        comodel_name='info.hub.article',
        inverse_name='parent_id',
        string='Sub-Articles',
        help='Sub-articles nested under this article.',
    )
    parent_path = fields.Char(
        index=True,
        help='Internal hierarchical path for parent-child tree navigation.',
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Sequence order for listing articles.',
    )

    category = fields.Selection(
        [
            ('workspace', 'Workspace'),
            ('shared', 'Shared'),
            ('private', 'Private'),
        ],
        string='Category',
        default='workspace',
        required=True,
        index=True,
        help='Scope of the article: Workspace, Shared, or Private.',
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='If unchecked, hides the article without permanently deleting it.',
    )
    is_template = fields.Boolean(
        string='Is Template',
        default=False,
        help='Template articles can be duplicated as a starting point for new content.',
    )
    is_locked = fields.Boolean(
        string='Is Locked',
        default=False,
        help='Locks the article to prevent further modifications.',
    )
    is_full_width = fields.Boolean(
        string='Is Full Width',
        default=False,
        help='Renders the article content in full-width layout mode.',
    )
    is_favorite = fields.Boolean(
        string='Is Favorite',
        default=False,
        help='Marks the article as a global favorite.',
    )
    is_article_item = fields.Boolean(
        string='Is Article Item',
        default=False,
        help='Mark this article as an item. By default, only non-item articles are shown in the Articles list.',
    )
    item_date_start = fields.Datetime(
        string="Start Date",
        help='Start date and time for the article item (used in calendar view).',
    )
    item_date_end = fields.Datetime(
        string="End Date",
        help='End date and time for the article item (used in calendar view).',
    )
    stage_id = fields.Many2one(
        comodel_name='info.hub.article.stage',
        string='Stage',
        group_expand='_read_group_stage_ids',
        ondelete='set null',
        index=True,
        help='Kanban stage of this article item.',
    )
    display_mode = fields.Selection(
        [
            ('document', 'Document'),
            ('kanban', 'Kanban'),
        ],
        string='Display Mode',
        default='document',
        required=True,
        help='Display mode for child items: Document or Kanban.',
    )
    template_category_id = fields.Many2one(
        comodel_name='info.hub.template.category',
        string='Template Category',
        ondelete='set null',
        help='Category under which this template will be listed in the template browser.',
    )
    template_description = fields.Text(
        string='Template Description',
        translate=True,
        help='A short description of what this template is used for.',
    )
    template_sequence = fields.Integer(
        string='Template Sequence',
        default=10,
        help='Used to sequence templates inside their category.',
    )

    author_id = fields.Many2one(
        comodel_name='res.users',
        string='Author',
        default=lambda self: self.env.user,
        ondelete='set null',
        index=True,
        help='User who created or owns this article.',
    )
    last_edition_uid = fields.Many2one(
        comodel_name='res.users',
        string='Last Edited By',
        ondelete='set null',
        help='User who last edited the article content.',
    )
    last_edition_date = fields.Datetime(
        string='Last Edited On',
        help='Date and time when the article was last modified.',
    )

    member_ids = fields.One2many(
        comodel_name='info.hub.article.member',
        inverse_name='article_id',
        string='Members',
        help='List of partner permissions and members for this article.',
    )

    website_published = fields.Boolean(
        string='Share to Web',
        default=False,
        help='Publish this article to make it accessible publicly via share link.',
    )
    share_token = fields.Char(
        string='Share Token',
        copy=False,
        help='Unique access token for sharing this article via link.',
    )
    share_url = fields.Char(
        compute='_compute_share_url',
        string='Share URL',
        help='Full public URL to access this shared article.',
    )
    visibility = fields.Selection(
        [
            ('everyone', 'Everyone'),
            ('members', 'Members'),
        ],
        default='everyone',
        string='Visibility',
        help='Specifies who can view this workspace article (Everyone or Members).',
    )
    default_access = fields.Selection(
        [
            ('none', 'No Access'),
            ('read', 'Can Read'),
            ('edit', 'Can Edit'),
        ],
        default='read',
        string='Default Access Rights',
        help='Default access permission for internal users on this article.',
    )
    user_permission = fields.Selection(
        [
            ('edit', 'Can edit'),
            ('read', 'Can read'),
            ('none', 'No access'),
        ],
        compute='_compute_user_permission',
        string='User Permission',
        help='Effective access permission level of the current user on this article.',
    )

    reading_assignment_ids = fields.One2many(
        comodel_name='info.hub.article.reading',
        inverse_name='article_id',
        string='Reading Assignments',
        help='Reading assignments and acknowledgement status for this article.',
    )
    reading_compliance_stat = fields.Char(
        string='Reading Compliance Stat',
        compute='_compute_reading_compliance_stat',
        help='Summary statistic of read acknowledgements versus total assigned readers.',
    )

    child_count = fields.Integer(
        string='Sub-Article Count',
        compute='_compute_child_count',
        store=True,
        help='Number of direct child articles nested under this article.',
    )
    custom_property_defs = fields.Json(
        string='Custom Property Definitions',
        default=list,
        help='Stores the schema (label, type, options…) for properties defined on this article\'s children.',
    )
    custom_property_values = fields.Json(
        string='Custom Property Values',
        default=dict,
        help='Stores per-article property values keyed by property label.',
    )
    article_properties_definition = fields.PropertiesDefinition(
        string='Article Properties Definition',
        compute='_compute_article_properties',
        store=True,
        help='Property definitions schema inherited by child items.',
    )
    article_properties = fields.Properties(
        string='Article Properties',
        definition='parent_id.article_properties_definition',
        compute='_compute_article_properties',
        store=True,
        copy=True,
        help='Dynamic custom property values configured for this article.',
    )
    card_properties_html = fields.Html(
        string='Card Properties',
        compute='_compute_card_properties_html',
        store=False,
        sanitize=False,
        help='HTML representation of article properties displayed on kanban cards.',
    )
    cover_image_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Cover Image Attachment',
        compute='_compute_cover_image_id',
        store=False,
        help='Attachment record corresponding to the cover image.',
    )
    is_user_favorite = fields.Boolean(
        string='Is User Favorite',
        compute='_compute_is_user_favorite',
        inverse='_inverse_is_user_favorite',
        search='_search_is_user_favorite',
        help='Indicates whether the current logged-in user marked this article as favorite.',
    )
    card_properties = fields.Json(
        string='Card Properties JSON',
        compute='_compute_card_properties',
        store=False,
        help='JSON summary of article properties used for frontend rendering.',
    )

    @api.depends('child_ids')
    def _compute_child_count(self):
        """Compute the number of direct child articles for each record."""
        for article in self:
            article.child_count = len(article.child_ids)

    @api.depends('reading_assignment_ids', 'reading_assignment_ids.state')
    def _compute_reading_compliance_stat(self):
        """Compute a "read / total" compliance string for reading assignments."""
        for article in self:
            total = len(article.reading_assignment_ids)
            read = len(article.reading_assignment_ids.filtered(lambda r: r.state == 'read'))
            article.reading_compliance_stat = f"{read} / {total}"

    def _compute_card_properties_html(self):
        """Build an HTML snippet of custom property values to display on kanban item cards."""
        for article in self:
            parts = []
            parent = article.parent_id
            if parent:
                defs = parent.sudo().custom_property_defs or []
                values = article.sudo().custom_property_values or {}
                for prop in defs:
                    if not prop.get('displayInCards'):
                        continue
                    prop_type = prop.get('type', '')
                    label = prop.get('label', '')
                    suffix = prop.get('suffix', '')
                    val_data = values.get(label, {})

                    if isinstance(val_data, dict):
                        val = val_data.get('value', '')
                    else:
                        val = str(val_data) if val_data else ''

                    if prop_type == 'Checkbox':
                        is_checked = (val == 'true')
                        if is_checked:
                            val_display = '<i class="fa fa-check-square" style="color: #0d9488; font-size: 0.88rem; vertical-align: middle; margin-bottom: 2px;"/>'
                        else:
                            val_display = '<i class="fa fa-square-o" style="color: #4b5563; font-size: 0.88rem; vertical-align: middle; margin-bottom: 2px;"/>'
                    elif prop_type == 'Tags':
                        tag_list = []
                        if isinstance(val, list):
                            tag_list = val
                        elif isinstance(val, str) and val.strip():
                            tag_list = [t.strip() for t in val.split(',') if t.strip()]
                        if not tag_list:
                            continue
                        badges = [
                            f'<span class="badge" style="background-color: #0d9488; color: #ffffff; border: 1px solid #0f766e; padding: 2px 6px; border-radius: 4px; font-weight: 500; font-size: 0.75rem; margin-right: 4px; margin-bottom: 2px; display: inline-block;">{t}</span>'
                            for t in tag_list
                        ]
                        val_display = "".join(badges)
                    elif prop_type == 'Many2many':
                        m2m_records = val_data.get('m2mRecords', []) if isinstance(val_data, dict) else []
                        if not m2m_records:
                            continue
                        badges = []
                        for rec in m2m_records:
                            rec_name = rec.get('name') or rec.get('display_name') or ''
                            if rec_name:
                                badges.append(f'<span class="badge" style="background-color: #f3f4f6; color: #374151; border: 1px solid #d1d5db; padding: 2px 6px; border-radius: 4px; font-weight: 500; font-size: 0.75rem; margin-right: 4px; margin-bottom: 2px; display: inline-block;">{rec_name}</span>')
                        if not badges:
                            continue
                        val_display = "".join(badges)
                    else:
                        if not val and val != 0:
                            val = prop.get('defaultValue', '')
                        if not val and val != 0:
                            continue
                        if prop_type == 'HTML':
                            suffix_str = f'<div class="text-muted mt-1" style="font-size:0.78rem;">{suffix}</div>' if suffix else ''
                            parts.append(
                                f'<div class="o_info_hub_card_prop o_info_hub_card_prop_html w-100 mt-1 mb-1">'
                                f'<div class="o_info_hub_card_prop_html_content bg-white text-dark p-2 border" style="border-radius: 4px; overflow: hidden; font-size: 0.85rem; max-height: 150px; overflow-y: auto;">{val}</div>'
                                f'{suffix_str}'
                                f'</div>'
                            )
                            continue
                        val_display = val

                    suffix_str = f' {suffix}' if suffix else ''
                    parts.append(
                        f'<div class="o_info_hub_card_prop w-100 mt-1">'
                        f'<span class="o_info_hub_card_prop_label">{label}:</span> '
                        f'<span class="o_info_hub_card_prop_value">{val_display}{suffix_str}</span>'
                        f'</div>'
                    )
            article.card_properties_html = ''.join(parts) if parts else False

    @api.depends('website_published')
    def _compute_share_url(self):
        """Compute the public share URL for portal-accessible articles."""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for article in self:
            if article.website_published:
                article.share_url = f"{base_url}/info/article/{article.id}"
            else:
                article.share_url = False

    @api.depends('member_ids', 'member_ids.permission', 'visibility', 'default_access')
    def _compute_user_permission(self):
        """Compute the effective permission of the current user for each article."""
        for article in self:
            article.user_permission = article._get_user_permission(self.env.user)

    def _get_user_permission(self, user):
        """Return the effective permission level of *user* for this article. """
        self.ensure_one()

        if user._is_admin() or user.has_group('info_hub.group_info_admin'):
            return 'edit'
        
        if self.create_uid == user or self.author_id == user:
            return 'edit'

        member = self.member_ids.sudo().filtered(lambda m: m.partner_id == user.partner_id)
        if member:
            return member[0].permission

        if self.category == 'private':
            return 'none'

        if (
                self.category != 'private'
                and self.visibility == 'everyone'
                and self.default_access != 'none'
        ):
            if user.share and not self.website_published:
                return 'none'
            return self.default_access

        if (
                self.visibility == 'members'
                and self.member_ids.filtered(
            lambda m: m.partner_id == user.partner_id
                      and m.permission != 'none'
        )
        ):
            member = self.member_ids.filtered(
                lambda m: m.partner_id == user.partner_id
            )[0]
            return member.permission

        if user._is_public() and self.website_published and self.default_access != 'none':
            return self.default_access

        return 'none'

    def _can_user_access_article(self, user):
        """Return True if *user* has at least read permission on this article."""
        self.ensure_one()
        return self._get_user_permission(user) in ('read', 'edit')

    def _can_access_portal(self, user):
        """Return True if *user* is allowed to view this article via the portal."""
        self.ensure_one()
        return self._get_user_permission(user) in ('read', 'edit')

    def _has_article_access(self, user):
        """Alias for _can_user_access_article — returns True when user has read or edit access."""
        self.ensure_one()
        return self._get_user_permission(user) in ('read', 'edit')

    @api.model
    def get_user_metadata(self):
        """Return a dict of info-related metadata for the currently logged-in user."""
        user = self.env.user
        return {
            'is_shared_user': user.is_info_shared_user(),
            'is_admin': user.has_group('info_hub.group_info_admin') or user._is_admin(),
            'is_info_user': user.has_group('info_hub.group_info_user'),
        }

    @api.model
    def get_sidebar_articles(self):
        """Return all articles visible to the current user for the sidebar navigation tree.

        Admins see all non-template, active articles. Regular users see only articles
        they created, authored, or have an explicit member record for.
        """
        user = self.env.user

        pending_readings = self.env['info.hub.article.reading'].sudo().search([
            ('user_id', '=', user.id),
            ('state', '=', 'pending'),
        ])
        pending_article_ids = set(pending_readings.mapped('article_id').ids)

        is_admin = (
            user._is_admin()
            or user.has_group('info_hub.group_info_admin')
        )

        if is_admin:
            articles = self.sudo().search([
                ('active', '=', True),
                ('is_template', '=', False),
                '|',
                ('category', '!=', 'private'),
                '|',
                ('create_uid', '=', user.id),
                ('author_id', '=', user.id),
            ], order='sequence asc, id asc')
        else:
            member_article_ids = self.env['info.hub.article.member'].sudo().search([
                ('partner_id', '=', user.partner_id.id),
                ('permission', 'in', ['read', 'edit']),
                ('article_id.active', '=', True),
            ]).mapped('article_id').ids

            creator_articles = self.sudo().search([
                ('active', '=', True),
                ('is_template', '=', False),
                '|',
                ('create_uid', '=', user.id),
                ('author_id', '=', user.id),
            ])

            # Shared articles where the user has an explicit member record
            member_articles = self.sudo().search([
                ('id', 'in', member_article_ids),
                ('active', '=', True),
                ('is_template', '=', False),
                ('category', 'in', ['workspace', 'shared']),
                ('create_uid', '!=', user.id),
                ('author_id', '!=', user.id),
            ])

            # Workspace articles with visibility='everyone' open to all
            workspace_everyone_articles = self.sudo().search([
                ('active', '=', True),
                ('is_template', '=', False),
                ('category', '=', 'workspace'),
                ('visibility', '=', 'everyone'),
                ('default_access', 'in', ['read', 'edit']),
            ])

            # Merge all recordsets (duplicates automatically removed by ORM)
            articles = creator_articles | member_articles | workspace_everyone_articles

            articles = articles.sorted(
                key=lambda a: (a.sequence, a.id)
            )

        result = []
        for a in articles:
            result.append({
                'id': a.id,
                'name': a.name or 'Untitled',
                'icon': a.icon or '📄',
                'category': a.category,
                'body': a.body or '',
                'author_id': [a.author_id.id, a.author_id.name] if a.author_id else False,
                'last_edition_date': fields.Datetime.to_string(a.last_edition_date) if a.last_edition_date else False,
                'is_favorite': a.is_favorite,
                'parent_id': [a.parent_id.id, a.parent_id.name] if a.parent_id else False,
                'display_mode': a.display_mode,
                'stage_id': [a.stage_id.id, a.stage_id.name] if a.stage_id else False,
                'is_article_item': a.is_article_item,
                'sequence': a.sequence,
                'is_unread': a.id in pending_article_ids,
            })
        return result

    @api.model
    def get_shared_sidebar_data(self):
        """Return sidebar data for portal/shared users: shared articles, public articles, and own private articles."""
        user = self.env.user
        partner = user.partner_id

        pending_readings = self.env['info.hub.article.reading'].sudo().search([
            ('user_id', '=', user.id),
            ('state', '=', 'pending'),
        ])
        pending_article_ids = set(pending_readings.mapped('article_id').ids)

        shared_memberships = self.env['info.hub.article.member'].sudo().search([
            ('partner_id', '=', partner.id),
            ('permission', '!=', 'none'),
            ('article_id.active', '=', True),
        ])
        shared_articles = shared_memberships.mapped('article_id')

        all_shared = shared_articles

        own_private_articles = self.env['info.hub.article'].sudo().search([
            ('active', '=', True),
            ('is_template', '=', False),
            ('category', '=', 'private'),
            '|',
            ('create_uid', '=', user.id),
            ('author_id', '=', user.id),
            ('id', 'not in', shared_articles.ids),
        ])

        def to_dict(articles):
            res = []
            for a in articles:
                res.append({
                    'id': a.id,
                    'name': a.name or 'Untitled',
                    'icon': a.icon or '📄',
                    'category': a.category,
                    'body': a.body or '',
                    'author_id': [a.author_id.id, a.author_id.name] if a.author_id else False,
                    'last_edition_date': fields.Datetime.to_string(a.last_edition_date) if a.last_edition_date else False,
                    'is_unread': a.id in pending_article_ids,
                })
            return res

        return {
            'articles': to_dict(all_shared),
            'favorites': [],
            'private': to_dict(own_private_articles),
        }

    @api.model
    def create_shared_user_private_article(self):
        """Create a new private article owned by the current shared/portal user and return its ID."""
        user = self.env.user
        article = self.sudo().create({
            'name': 'Untitled',
            'icon': '📄',
            'category': 'private',
            'author_id': user.id,
            'body': '',
            'visibility': 'members',
        })
        self.env['info.hub.article.member'].sudo().create({
            'article_id': article.id,
            'partner_id': user.partner_id.id,
            'permission': 'edit',
        })
        return article.id

    def action_join_article(self):
        """Add the current internal user as a member of this article with the default access level.

        Returns a dict with article metadata on success, or False for portal/shared users.
        """
        self.ensure_one()
        user = self.env.user
        if user.share:
            return False
        sudo_self = self.sudo()
        member = sudo_self.member_ids.filtered(
            lambda m: m.partner_id == user.partner_id
        )
        if not member:
            self.env['info.hub.article.member'].sudo().create({
                'article_id': self.id,
                'partner_id': user.partner_id.id,
                'permission': sudo_self.default_access or 'read',
            })
        return {
            'id': self.id,
            'name': sudo_self.name or 'Untitled',
            'icon': sudo_self.icon or '📄',
            'category': sudo_self.category,
            'parent_id': [sudo_self.parent_id.id, sudo_self.parent_id.name] if sudo_self.parent_id else False,
            'is_favorite': sudo_self.is_favorite,
            'display_mode': sudo_self.display_mode,
            'sequence': sudo_self.sequence,
            'is_article_item': sudo_self.is_article_item,
            'last_edition_date': fields.Datetime.to_string(sudo_self.last_edition_date) if sudo_self.last_edition_date else False,
            'author_id': [sudo_self.author_id.id, sudo_self.author_id.name] if sudo_self.author_id else False,
        }

    @api.model
    def get_hidden_workspace_articles(self, search_term=''):
        """Return workspace and shared articles the current user is not yet a member of.

        Used by the "Find more articles" dialog. Results are limited to 100 records.
        """
        user = self.env.user

        if user.share:
            return []

        member_article_ids = self.env['info.hub.article.member'].sudo().search([
            ('partner_id', '=', user.partner_id.id),
            ('permission', 'in', ['read', 'edit']),
        ]).mapped('article_id').ids

        domain = [
            ('active', '=', True),
            ('is_template', '=', False),
            ('is_article_item', '=', False),
            ('category', 'in', ['workspace', 'shared']),
            ('visibility', '=', 'members'),
            ('default_access', '!=', 'none'),

            ('create_uid', '!=', user.id),
            ('author_id', '!=', user.id),

            ('id', 'not in', member_article_ids),
        ]

        if search_term:
            domain.append(('name', 'ilike', search_term))

        articles = self.sudo().search(
            domain,
            order='name asc',
            limit=100,
        )

        result = []

        for art in articles:
            result.append({
                'id': art.id,
                'name': art.name or 'Untitled',
                'icon': art.icon or '📄',
                'category': art.category,
                'parent_id': [art.parent_id.id, art.parent_id.name] if art.parent_id else False,
                'parent_name': art.parent_id.name if art.parent_id else '',
                'default_access': art.default_access,
                'is_favorite': art.is_favorite,
                'display_mode': art.display_mode,
                'sequence': art.sequence,
                'is_article_item': art.is_article_item,
                'last_edition_date': fields.Datetime.to_string(art.last_edition_date)
                if art.last_edition_date else False,
                'author_id': [art.author_id.id, art.author_id.name]
                if art.author_id else False,
            })

        return result

    def invite_members(self, partner_ids, permission):
        """Grant or update access for the given partner IDs on this article.

        If the article is currently private and partners are added, it is automatically
        promoted to the shared category.
        """
        self.ensure_one()
        for partner_id in partner_ids:
            member = self.env['info.hub.article.member'].search([
                ('article_id', '=', self.id),
                ('partner_id', '=', partner_id)
            ], limit=1)
            if member:
                if member.partner_id != self.create_uid.partner_id:
                    member.write({'permission': permission})
            else:
                self.env['info.hub.article.member'].create({
                    'article_id': self.id,
                    'partner_id': partner_id,
                    'permission': permission,
                })

        if self.category == 'private':
            self.write({
                'category': 'shared',
            })

        return True

    @api.model
    def check_website_installed(self):
        """Return True if the "website" Odoo module is currently installed."""
        return bool(self.env['ir.module.module'].search([('name', '=', 'website'), ('state', '=', 'installed')]))

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to inherit the parent's category, generate a share token, assign the
        first kanban stage to new items, and snapshot the initial body as a version record.
        """
        for vals in vals_list:
            if vals.get('parent_id') and not vals.get('category'):
                parent = self.browse(vals['parent_id'])
                vals['category'] = parent.category
            if not vals.get('share_token'):
                vals['share_token'] = uuid.uuid4().hex

            if vals.get('category') == 'workspace':
                if not vals.get('visibility'):
                    vals['visibility'] = 'everyone'
                if vals.get('default_access', 'none') == 'none':
                    vals['default_access'] = 'read'

            parent_id = vals.get('parent_id') or self.env.context.get('default_parent_id')
            is_item = vals.get('is_article_item') or self.env.context.get('default_is_article_item')
            if is_item and parent_id and not vals.get('stage_id'):
                self.create_default_item_stages(parent_id)
                first_stage = self.env['info.hub.article.stage'].search(
                    [('parent_id', '=', parent_id)],
                    order='sequence, id',
                    limit=1
                )
                if first_stage:
                    vals['stage_id'] = first_stage.id
        records = super().create(vals_list)
        for record in records:
            if record.body:
                self.env['info.hub.article.version'].create({
                    'article_id': record.id,
                    'body': record.body,
                })
        return records

    def write(self, vals):
        """Override write to update edition metadata, snapshot body changes as version records,
        propagate category changes to descendants, and clean up members when moving to private.
        """
        if 'body' in vals or 'name' in vals:
            vals.setdefault('last_edition_uid', self.env.uid)
            vals.setdefault('last_edition_date', fields.Datetime.now())
            
        if 'body' in vals:
            for article in self:
                if article.body != vals['body']:
                    version_count = self.env['info.hub.article.version'].search_count([('article_id', '=', article.id)])
                    if version_count == 0 and article.body:
                        self.env['info.hub.article.version'].create({
                            'article_id': article.id,
                            'body': article.body,
                        })
                    self.env['info.hub.article.version'].create({
                        'article_id': article.id,
                        'body': vals['body'],
                    })

        if 'parent_id' in vals:
            parent_id = vals['parent_id']
            if parent_id:
                parent = self.env['info.hub.article'].browse(parent_id)
                vals['category'] = parent.category

        if vals.get('category') == 'workspace':
            if not vals.get('visibility'):
                vals['visibility'] = 'everyone'
            if 'default_access' not in vals:
                if any(r.default_access == 'none' for r in self):
                    vals['default_access'] = 'read'
            elif vals['default_access'] == 'none':
                vals['default_access'] = 'read'

        if vals.get('category') == 'private':
            for article in self:
                if article.category == 'shared':
                    owner_partner = article.author_id.partner_id or article.create_uid.partner_id

                    invited_members = article.member_ids.filtered(
                        lambda m: m.partner_id != owner_partner
                    )

                    invited_members.unlink()

        res = super().write(vals)

        if 'category' in vals:
            category = vals['category']
            for record in self:
                descendants = self.with_context(active_test=False).search([('id', 'child_of', record.ids)]) - record
                if descendants:
                    super(InformationArticle, descendants).write({'category': category})
        return res

    def action_view_reading_compliance(self):
        """Open a list/pivot view of reading assignment records for this article."""
        self.ensure_one()
        return {
            'name': 'Reading Compliance',
            'type': 'ir.actions.act_window',
            'res_model': 'info.hub.article.reading',
            'view_mode': 'list,pivot',
            'domain': [('article_id', '=', self.id)],
            'context': {'default_article_id': self.id},
        }

    def action_archive(self):
        """Archive this article and all of its descendant articles."""
        self.with_context(active_test=False).search(
            [('id', 'child_of', self.ids)]
        ).write({'active': False})
        return True

    def action_unarchive(self):
        """Restore this article from the archive, along with any inactive parent articles and descendant articles."""
        for article in self:
            if article.parent_id and not article.parent_id.active:
                article.parent_id.action_unarchive()
        self.with_context(active_test=False).search(
            [('id', 'child_of', self.ids)]
        ).write({'active': True})
        return True

    def action_do_nothing(self):
        """Do nothing action, useful for disabling list row click actions."""
        return True

    def action_open_in_editor(self):
        """Return an action to open this article in the Information client-side editor."""
        self.ensure_one()
        action = self.env.ref('info_hub.action_info_client').read()[0]
        action['res_id'] = self.id
        action['params'] = {
            'article_id': self.id,
        }
        action['context'] = {
            **self.env.context,
            'active_id': self.id,
        }
        return action

    @api.readonly
    def get_formview_action(self, access_uid=None):
        """Override to redirect record opens to the Information editor instead of the standard form view."""
        self.ensure_one()
        if not self.active or self.is_template:
            return super().get_formview_action(access_uid=access_uid)

        action = self.env.ref('info_hub.action_info_client').read()[0]
        action['res_id'] = self.id
        action['params'] = {
            'article_id': self.id,
        }
        action['context'] = {
            **self.env.context,
            'active_id': self.id,
        }
        return action

    @api.model
    def get_available_templates(self):
        """Return a list of all template articles with their metadata for the template browser."""
        templates = self.search([('is_template', '=', True)])
        return [{
            'id': t.id,
            'name': t.name,
            'icon': t.icon,
            'template_category_id': [t.template_category_id.id, t.template_category_id.name] if t.template_category_id else False,
            'template_category_sequence': t.template_category_id.sequence if t.template_category_id else 999,
            'template_description': t.template_description or '',
            'template_sequence': t.template_sequence,
        } for t in templates]

    @api.model
    def get_template_preview(self, template_id):
        """Return body and metadata for the given template article so it can be previewed."""
        template = self.browse(template_id)
        if not template.exists():
            return {}
        return {
            'id': template.id,
            'name': template.name,
            'icon': template.icon,
            'body': template.body or "",
            'cover_image_url': f'/web/image/info.hub.article/{template.id}/cover_image' if template.cover_image else False,
            'template_description': template.template_description or "",
            'template_category': template.template_category_id.name if template.template_category_id else "",
        }

    @api.model
    def get_kanban_view_id(self):
        """Return the database ID of the embedded kanban item view, or False if not found."""
        view = self.env.ref(
            "info_hub.view_info_article_kanban_items",
            raise_if_not_found=False,
        )
        return view.id if view else False

    @api.model
    def create_article_from_template(self, template_id, category, parent_id=None):
        """Create a new non-template article based on the given template and return its ID."""
        template = self.browse(template_id)
        if not template.exists() or not template.is_template:
            raise ValueError("Invalid template.")
        if category not in ['workspace', 'private', 'shared']:
            raise ValueError("Invalid category.")

        vals = {
            'name': template.name,
            'icon': template.icon,
            'body': template.body,
            'cover_image': template.cover_image,
            'category': category,
            'parent_id': parent_id,
            'is_template': False,
            'active': True,
            'author_id': self.env.uid,
        }
        new_article = self.create([vals])
        return new_article.id


    @api.model
    def duplicate_article(self, article_id):
        """Create a copy of the given article (not a template) and return the new article's ID."""
        original = self.browse(article_id)
        if not original.exists():
            raise ValueError("Article not found.")
        copy_vals = {
            'name': original.name + ' (Copy)',
            'icon': original.icon,
            'body': original.body,
            'cover_image': original.cover_image,
            'category': original.category,
            'parent_id': original.parent_id.id if original.parent_id else False,
            'is_template': False,
            'is_locked': False,
            'is_full_width': original.is_full_width,
            'active': True,
            'author_id': self.env.uid,
        }
        new_article = self.create([copy_vals])
        return new_article.id

    @api.model
    def add_article_to_templates(self, article_id, template_category_id=False):
        """Mark the given article as a template so it appears in the template browser."""
        article = self.browse(article_id)
        if not article.exists():
            raise ValueError("Article not found.")
        vals = {'is_template': True}
        if template_category_id:
            vals['template_category_id'] = template_category_id
        article.write(vals)
        return True


    @api.model
    def toggle_lock(self, article_id):
        """Toggle the is_locked flag on the given article and return the new boolean value."""
        article = self.browse(article_id)
        if not article.exists():
            raise ValueError("Article not found.")
        article.write({'is_locked': not article.is_locked})
        return article.is_locked

    @api.model
    def toggle_full_width(self, article_id):
        """Toggle the is_full_width flag on the given article and return the new boolean value."""
        article = self.browse(article_id)
        if not article.exists():
            raise ValueError("Article not found.")
        article.write({'is_full_width': not article.is_full_width})
        return article.is_full_width

    @api.model
    def save_article_properties(self, article_id, parent_id, property_defs, property_values):
        """Persist custom property definitions on the parent article and property values on the article."""
        parent = self.browse(parent_id)
        if parent.exists():
            parent.sudo().write({'custom_property_defs': property_defs})
        article = self.browse(article_id)
        if article.exists():
            article.sudo().write({'custom_property_values': property_values})
        return True

    @api.model
    def load_article_properties(self, article_id, parent_id):
        """Load custom property definitions from the parent article and values from the article."""
        parent = self.browse(parent_id)
        article = self.browse(article_id)
        return {
            'property_defs': (parent.sudo().custom_property_defs or []) if parent.exists() else [],
            'property_values': (article.sudo().custom_property_values or {}) if article.exists() else {},
        }

    @api.model
    def remove_cover_image(self, article_id):
        """Remove the cover image from the given article."""
        article = self.browse(article_id)
        if not article.exists():
            raise ValueError("Article not found.")
        article.write({'cover_image': False})
        return True

    @api.model
    def apply_template_to_article(self, article_id, template_id):
        """Overwrite the article's name, icon, body, cover image, and display mode with those of the given template."""
        article = self.browse(article_id)
        template = self.browse(template_id)
        if not article.exists():
            raise ValueError("Article not found.")
        if not template.exists() or not template.is_template:
            raise ValueError("Invalid template.")
        article.write({
            'name': template.name,
            'icon': template.icon,
            'body': template.body,
            'cover_image': template.cover_image,
            'display_mode': template.display_mode,
        })
        return True

    @api.model
    def create_default_item_stages(self, article_id):
        """Create the default Kanban stages (New, Ongoing, Done) for the given article if none exist."""
        article = self.browse(article_id)
        if not article.exists():
            raise ValueError("Article not found.")

        existing_stages = self.env['info.hub.article.stage'].search([('parent_id', '=', article.id)])
        if not existing_stages:
            self.env['info.hub.article.stage'].create([
                {'name': 'New', 'sequence': 10, 'parent_id': article.id, 'fold': False},
                {'name': 'Ongoing', 'sequence': 20, 'parent_id': article.id, 'fold': False},
                {'name': 'Done', 'sequence': 30, 'parent_id': article.id, 'fold': True},
            ])
        return True

    def _compute_cover_image_id(self):
        for record in self:
            attachment = self.env['ir.attachment'].search([
                ('res_model', '=', 'info.hub.article'),
                ('res_id', '=', record.id),
                ('res_field', '=', 'cover_image')
            ], limit=1)
            record.cover_image_id = attachment.id if attachment else False

    @api.depends('is_favorite')
    def _compute_is_user_favorite(self):
        for record in self:
            record.is_user_favorite = record.is_favorite

    def _inverse_is_user_favorite(self):
        for record in self:
            record.is_favorite = record.is_user_favorite

    def _search_is_user_favorite(self, operator, value):
        return [('is_favorite', operator, value)]

    @api.depends('custom_property_values')
    def _compute_card_properties(self):
        for article in self:
            properties = []
            parent = article.parent_id
            if parent:
                defs = parent.sudo().custom_property_defs or []
                values = article.sudo().custom_property_values or {}
                for prop in defs:
                    if not prop.get('displayInCards'):
                        continue
                    label = prop.get('label', '')
                    prop_type = prop.get('type', '')
                    val_data = values.get(label, {})

                    tag_list = []
                    if prop_type in ['Tags', 'Many2many']:
                        m2m_records = val_data.get('m2mRecords', []) if isinstance(val_data, dict) else []
                        for rec in m2m_records:
                            name = rec.get('name') or rec.get('display_name') or ''
                            if name:
                                tag_list.append(name)
                    elif prop_type == 'Selection':
                        if isinstance(val_data, dict):
                            val = val_data.get('value', '')
                        else:
                            val = str(val_data) if val_data else ''
                        if val:
                            tag_list.append(val)
                    elif prop_type == 'Checkbox':
                        if isinstance(val_data, dict):
                            val = val_data.get('value', '')
                        else:
                            val = str(val_data) if val_data else ''
                        if val == 'true':
                            tag_list.append(label)
                    else:
                        if isinstance(val_data, dict):
                            val = val_data.get('value', '')
                        else:
                            val = str(val_data) if val_data else ''
                        if val:
                            tag_list.append(f"{label}: {val}")

                    if tag_list:
                        properties.append({
                            'label': label,
                            'type': prop_type,
                            'tags': tag_list
                        })
            article.card_properties = properties

    @api.depends('custom_property_defs', 'parent_id.custom_property_defs', 'custom_property_values')
    def _compute_article_properties(self):
        def _get_property_name(label):
            if not label:
                return 'prop_empty'
            name = ''
            for char in label:
                if char.isalnum():
                    name += char.lower()
                elif char in [' ', '_', '-']:
                    name += '_'
            import re
            name = re.sub(r'_+', '_', name).strip('_')
            if not name or not name[0].isalpha():
                name = 'prop_' + name
            name = ''.join(c for c in name if c.isalnum() or c == '_')
            return name

        for article in self:
            defs = article.custom_property_defs or []
            native_defs = []
            seen_names = set()
            for d in defs:
                label = d.get('label') or ''
                prop_type = d.get('type') or 'Text'
                odoo_type = 'char'
                if prop_type == 'Checkbox':
                    odoo_type = 'boolean'
                elif prop_type == 'Number':
                    odoo_type = 'integer'
                elif prop_type == 'Date':
                    odoo_type = 'date'
                elif prop_type == 'Selection':
                    odoo_type = 'selection'
                elif prop_type in ['Tags', 'Many2many']:
                    odoo_type = 'tags'

                prop_name = _get_property_name(label)
                base_name = prop_name
                counter = 1
                while prop_name in seen_names:
                    prop_name = f"{base_name}_{counter}"
                    counter += 1
                seen_names.add(prop_name)

                prop_def = {
                    'name': prop_name,
                    'string': label,
                    'type': odoo_type,
                }
                if prop_type == 'Selection':
                    prop_def['selection'] = [[c, c] for c in d.get('choices', [])]
                native_defs.append(prop_def)
            article.article_properties_definition = native_defs

            parent = article.parent_id
            values = article.custom_property_values or {}
            native_values = {}
            if parent:
                parent_defs = parent.custom_property_defs or []
                seen_parent_names = set()
                for d in parent_defs:
                    label = d.get('label') or ''
                    val_data = values.get(label)
                    val = None
                    if isinstance(val_data, dict):
                        if d.get('type') in ['Tags', 'Many2many']:
                            m2m_records = val_data.get('m2mRecords', [])
                            val = [r.get('name') or r.get('display_name') or '' for r in m2m_records]
                            val = [v for v in val if v]
                        else:
                            val = val_data.get('value')
                    else:
                        val = val_data

                    if d.get('type') == 'Checkbox':
                        val = (val == 'true' or val is True)
                    elif d.get('type') == 'Number':
                        try:
                            val = int(val) if val else 0
                        except ValueError:
                            val = 0

                    prop_name = _get_property_name(label)
                    base_name = prop_name
                    counter = 1
                    while prop_name in seen_parent_names:
                        prop_name = f"{base_name}_{counter}"
                        counter += 1
                    seen_parent_names.add(prop_name)

                    native_values[prop_name] = val
            article.article_properties = native_values

    @api.model
    def get_embedded_card_view_id(self):
        """Return the database ID of the article item Cards Kanban view."""
        view = self.env.ref(
            "info_hub.info_article_view_embedded_cards",
            raise_if_not_found=False,
        )
        return view.id if view else False

    @api.model
    def get_views(self, views, options=None):
        # If context forces card view, replace the kanban view ID with the card view ID
        if self.env.context.get('force_embedded_cards') and views:
            new_views = []
            for view in views:
                if view[1] == 'kanban':
                    embedded_cards_view = self.env.ref(
                        'info_hub.info_article_view_embedded_cards',
                        raise_if_not_found=False
                    )
                    if embedded_cards_view:
                        new_views.append([embedded_cards_view.id, 'kanban'])
                        continue
                new_views.append(view)
            views = new_views
        return super().get_views(views, options=options)

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        """Return the ordered kanban stages for the current parent article context.

        Auto-creates default stages if none exist for the resolved parent.
        Uses active_test=False to ensure stages are found even when the parent
        article has been archived.
        """
        parent_id = self.env.context.get('default_parent_id')

        if not parent_id and domain:
            for term in domain:
                if isinstance(term, (list, tuple)) and len(term) == 3 and term[0] == 'parent_id':
                    operator = term[1]
                    value = term[2]
                    if operator == '=':
                        parent_id = value
                        break
                    elif operator == 'in':
                        if isinstance(value, (list, tuple)) and value:
                            parent_id = value[0]
                        else:
                            parent_id = value
                        break
                elif hasattr(term, 'left') and term.left == 'parent_id':
                    if term.operator == '=':
                        parent_id = term.right
                        break
                    elif term.operator == 'in':
                        parent_id = term.right[0] if isinstance(term.right, (list, tuple)) and term.right else term.right
                        break

        if isinstance(parent_id, (list, tuple)) and parent_id:
            parent_id = parent_id[0]

        if parent_id:
            # Use active_test=False so stages are found even when the parent
            # article is archived (inactive). Stage records themselves have no
            # active field, but the Many2one ORM join can otherwise filter them out.
            stage_env = self.env['info.hub.article.stage'].with_context(active_test=False)
            stages_records = stage_env.search([('parent_id', '=', parent_id)], order='sequence asc, id asc')
            if not stages_records:
                # Only auto-create stages outside a readonly context (i.e. when
                # called from a regular write transaction, not from web_read_group).
                if not self.env.context.get('no_stage_autocreate'):
                    try:
                        stage_env.create([
                            {'name': 'New', 'sequence': 10, 'parent_id': parent_id, 'fold': False},
                            {'name': 'Ongoing', 'sequence': 20, 'parent_id': parent_id, 'fold': False},
                            {'name': 'Done', 'sequence': 30, 'parent_id': parent_id, 'fold': True},
                        ])
                        stages_records = stage_env.search([('parent_id', '=', parent_id)], order='sequence asc, id asc')
                    except Exception:
                        # Silently ignore write errors (e.g. readonly context)
                        pass
            return stages_records
        return self.env['info.hub.article.stage']


    @api.model
    def _register_hook(self):
        """Ensure security group memberships are consistent on module installation/upgrade.

        - Removes the portal group from the shared-user group implied_ids.
        - Links the info_user group to the default_user_group.
        - Assigns info_user to any internal users that have no info group.
        """
        super()._register_hook()
        
        group_info_shared = self.env.ref('info_hub.group_info_shared_user', raise_if_not_found=False)
        group_portal = self.env.ref('base.group_portal', raise_if_not_found=False)
        if group_info_shared and group_portal and group_portal in group_info_shared.implied_ids:
            group_info_shared.sudo().write({
                'implied_ids': [fields.Command.unlink(group_portal.id)]
            })

        default_user_group = self.env.ref('base.default_user_group', raise_if_not_found=False)
        group_info_user = self.env.ref('info_hub.group_info_user', raise_if_not_found=False)
        if default_user_group and group_info_user and group_info_user not in default_user_group.implied_ids:
            default_user_group.sudo().write({
                'implied_ids': [fields.Command.link(group_info_user.id)]
            })

        group_user = self.env.ref('base.group_user', raise_if_not_found=False)
        group_info_admin = self.env.ref('info_hub.group_info_admin', raise_if_not_found=False)
        group_info_shared = self.env.ref('info_hub.group_info_shared_user', raise_if_not_found=False)
        
        if group_user and group_info_user and group_info_admin and group_info_shared:
            users_to_update = self.env['res.users'].sudo().search([
                ('active', '=', True),
                ('share', '=', False),
                ('id', '!=', self.env.ref('base.user_root').id),
                ('group_ids', 'in', group_user.id),
                ('group_ids', 'not in', [group_info_user.id, group_info_admin.id, group_info_shared.id])
            ])
            if users_to_update:
                users_to_update.write({
                    'group_ids': [fields.Command.link(group_info_user.id)]
                })

    @api.model
    def hierarchy_read(self, domain, fields, parent_field, child_field, order=None):
        clean_domain = []
        for leaf in domain:
            if isinstance(leaf, (list, tuple)) and len(leaf) == 3:
                if leaf[0] == 'parent_id' and leaf[1] == '=' and leaf[2] is False:
                    clean_domain.append(['id', '!=', False])
                    continue
            clean_domain.append(leaf)
        return super(InformationArticle, self).hierarchy_read(
            clean_domain, fields, parent_field, child_field, order
        )

class InformationArticleVersion(models.Model):
    """Stores immutable body snapshots of a info article for version history."""
    _name = 'info.hub.article.version'
    _description = 'Information Article Version'
    _order = 'create_date desc, id desc'

    article_id = fields.Many2one(
        comodel_name='info.hub.article',
        string='Article',
        required=True,
        ondelete='cascade',
        index=True,
        help='The article this version snapshot belongs to.',
    )
    body = fields.Html(
        string='Content',
        sanitize=True,
        sanitize_tags=True,
        help='Snapshot of HTML content for this version.',
    )
