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

from odoo import http, SUPERUSER_ID, tools
from odoo.http import request
from odoo.addons.html_editor.controllers.main import HTML_Editor, get_existing_attachment
import re

class InformationPublicController(http.Controller):
    """HTTP controller for the portal and public-facing info pages.

    Handles routes for shared-user portal access, public article viewing, article
    creation/saving by portal users, member invitation, and publishing toggles.
    """

    def _prepare_portal_info_values(self, active_article=None, filter_text=''):
        """Build the template context dict for the portal info layout.

        Collects all articles visible to the current portal/shared user, determines
        the active article and its permission level, and returns partner data needed
        for the invitation UI.
        """
        user = request.env.user
        partner = user.partner_id

        workspace_placeholder = "There are no Articles in your Workspace."

        shared_memberships = request.env['info.hub.article.member'].sudo().search([
            ('partner_id', '=', partner.id),
            ('permission', '!=', 'none'),
            ('article_id.active', '=', True),
        ])
        shared_articles_all = shared_memberships.mapped('article_id')

        private_articles_all = request.env['info.hub.article'].sudo().search([
            ('active', '=', True),
            ('is_template', '=', False),
            '|',
            ('create_uid', '=', user.id),
            ('author_id', '=', user.id),
            ('id', 'not in', shared_articles_all.ids),
        ])

        all_visible_articles = (shared_articles_all | private_articles_all)

        if filter_text:
            filter_text_lower = filter_text.lower()
            all_visible_articles = all_visible_articles.filtered(lambda a: filter_text_lower in (a.name or '').lower())

        favorite_articles = all_visible_articles.filtered(lambda a: a.is_favorite)
        workspace_articles = all_visible_articles.filtered(lambda a: a.category == 'workspace')
        shared_articles = all_visible_articles.filtered(lambda a: a.category == 'shared')
        private_articles = all_visible_articles.filtered(lambda a: a.category == 'private')

        if not active_article:
            if workspace_articles:
                active_article = workspace_articles[0]
            elif shared_articles:
                active_article = shared_articles[0]
            elif private_articles:
                active_article = private_articles[0]

        active_permission = 'none'
        if active_article:
            active_permission = active_article._get_user_permission(user)

        all_partners = request.env['res.partner'].sudo().search([
            ('id', '!=', partner.id),
            ('active', '=', True)
        ], limit=50)

        active_members = []
        if active_article:
            active_members = active_article.member_ids.sudo()

        is_website_installed = request.env['info.hub.article'].sudo().check_website_installed()

        return {
            'favorite_articles': favorite_articles,
            'workspace_articles': workspace_articles,
            'shared_articles': shared_articles,
            'private_articles': private_articles,
            'active_article': active_article,
            'active_permission': active_permission,
            'filter_text': filter_text or '',
            'workspace_placeholder': workspace_placeholder,
            'all_partners': all_partners,
            'active_members': active_members,
            'is_website_installed': is_website_installed,
            'user': user,
        }

    @http.route('/info/shared', type='http', auth='user', website=True)
    def info_shared(self, article_id=None, search=None, **kwargs):
        """Render the shared-user portal info page.

        Redirects internal users to the Odoo Information client action.
        Returns HTTP 403 if the requested article is inaccessible.
        """
        user = request.env.user
        
        if not user.share:
            return request.redirect('/odoo/action-info_hub.action_info_client')

        active_article = None
        if article_id:
            active_article = request.env['info.hub.article'].sudo().browse(int(article_id))
            if not active_article.exists() or not active_article.active or not active_article._can_access_portal(user):
                return request.render('http_routing.403')

        values = self._prepare_portal_info_values(active_article=active_article, filter_text=search)
        return request.render('info_hub.info_portal_layout', values)

    @http.route('/info/article/<int:article_id>', type='http', auth='public', website=True)
    def article_detail(self, article_id, **kwargs):
        """Render a single info article for public or portal users.

        Returns 404 if the article does not exist or is archived.
        Returns 403 if the requesting user has no read permission.
        """
        article = request.env['info.hub.article'].sudo().browse(article_id)
        if not article.exists() or not article.active:
            return request.not_found()

        user = request.env.user
        permission = article._get_user_permission(user)

        if permission == 'none':
            if user._is_public():
                return request.redirect(f'/web/login?redirect=/info/article/{article.id}')
            return request.render('http_routing.403') if hasattr(request, 'render') else "Access Denied"

        if not user.share:
            return request.redirect(f'/odoo/action-info_hub.action_info_client/{article.id}')
        elif user.share and not user._is_public():
            return request.redirect(f'/info/shared?article_id={article.id}')

        is_public = user._is_public()
        has_inaccessible = False
        if article.body:
            inaccessible_keywords = ['o_info_behavior', 'oe_view', 'o_info_behavior_type']
            has_inaccessible = any(kw in article.body for kw in inaccessible_keywords)

        values = {
            'article': article,
            'has_inaccessible_blocks': has_inaccessible,
            'is_public': is_public,
        }
        return request.render('info_hub.public_article_view', values)

    @http.route('/info/portal/create', type='http', auth='user', methods=['POST'], website=True)
    def info_portal_create(self, **kwargs):
        """Create a new private article for the current portal/shared user and return JSON."""
        user = request.env.user
        if not user.share:
            return request.redirect('/odoo/action-info_hub.action_info_client')

        article = request.env['info.hub.article'].sudo().create({
            'name': 'Untitled',
            'icon': '📄',
            'category': 'private',
            'author_id': user.id,
            'body': '<h1>Untitled</h1><p>Start writing...</p>',
            'visibility': 'members',
        })
        
        request.env['info.hub.article.member'].sudo().create({
            'article_id': article.id,
            'partner_id': user.partner_id.id,
            'permission': 'edit',
        })
        
        return request.redirect(f'/info/shared?article_id={article.id}')

    @http.route('/info/portal/save', type='jsonrpc', auth='user')
    def info_portal_save(self, article_id, name=None, icon=None, body=None, **kwargs):
        """Save name, icon, and body edits made by a portal user to their article."""
        user = request.env.user
        article = request.env['info.hub.article'].sudo().browse(int(article_id))
        if not article.exists() or not article.active or not article._can_access_portal(user):
            return {'error': 'Access Denied'}

        active_permission = article._get_user_permission(user)
        if active_permission != 'edit':
            return {'error': 'Read Only'}

        vals = {}
        if name is not None:
            vals['name'] = name
        if icon is not None:
            vals['icon'] = icon
        if body is not None:
            vals['body'] = body

        if vals:
            article.sudo().write(vals)

        return {'success': True}

    @http.route('/info/portal/toggle_favorite', type='jsonrpc', auth='user')
    def info_portal_toggle_favorite(self, article_id, favorite, **kwargs):
        """Toggle favorite status of an article for the portal user."""
        user = request.env.user
        article = request.env['info.hub.article'].sudo().browse(int(article_id))
        if not article.exists() or not article.active or not article._can_access_portal(user):
            return {'error': 'Access Denied'}
        article.sudo().write({'is_favorite': favorite})
        return {'success': True}

    @http.route('/info/portal/toggle_locked', type='jsonrpc', auth='user')
    def info_portal_toggle_locked(self, article_id, locked, **kwargs):
        """Toggle lock status of an article for the portal user."""
        user = request.env.user
        article = request.env['info.hub.article'].sudo().browse(int(article_id))
        if not article.exists() or not article.active or not article._can_access_portal(user):
            return {'error': 'Access Denied'}
        active_permission = article._get_user_permission(user)
        if active_permission != 'edit':
            return {'error': 'Permission Denied'}
        article.sudo().write({'is_locked': locked})
        return {'success': True}

    @http.route('/info/portal/toggle_full_width', type='jsonrpc', auth='user')
    def info_portal_toggle_full_width(self, article_id, full_width, **kwargs):
        """Toggle full width status of an article for the portal user."""
        user = request.env.user
        article = request.env['info.hub.article'].sudo().browse(int(article_id))
        if not article.exists() or not article.active or not article._can_access_portal(user):
            return {'error': 'Access Denied'}
        article.sudo().write({'is_full_width': full_width})
        return {'success': True}

    @http.route('/info/portal/archive', type='jsonrpc', auth='user')
    def info_portal_archive(self, article_id, **kwargs):
        """Archive (Move to Trash) an article for the portal user."""
        user = request.env.user
        article = request.env['info.hub.article'].sudo().browse(int(article_id))
        if not article.exists() or not article.active or not article._can_access_portal(user):
            return {'error': 'Access Denied'}
        active_permission = article._get_user_permission(user)
        if active_permission != 'edit':
            return {'error': 'Permission Denied'}
        article.sudo().write({'active': False})
        return {'success': True}

    @http.route('/info/portal/remove_icon', type='jsonrpc', auth='user')
    def info_portal_remove_icon(self, article_id, **kwargs):
        """Remove icon (set to default 📄) for the portal user."""
        user = request.env.user
        article = request.env['info.hub.article'].sudo().browse(int(article_id))
        if not article.exists() or not article.active or not article._can_access_portal(user):
            return {'error': 'Access Denied'}
        active_permission = article._get_user_permission(user)
        if active_permission != 'edit':
            return {'error': 'Permission Denied'}
        article.sudo().write({'icon': '📄'})
        return {'success': True}

    @http.route('/info/portal/add_random_icon', type='jsonrpc', auth='user')
    def info_portal_add_random_icon(self, article_id, **kwargs):
        """Add a random emoji icon for the portal user."""
        import random
        user = request.env.user
        article = request.env['info.hub.article'].sudo().browse(int(article_id))
        if not article.exists() or not article.active or not article._can_access_portal(user):
            return {'error': 'Access Denied'}
        active_permission = article._get_user_permission(user)
        if active_permission != 'edit':
            return {'error': 'Permission Denied'}

        emojis = [
            "😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😇",
            "🙂", "🙃", "😉", "😌", "😍", "🥰", "😘", "😗", "😙", "😚",
            "😋", "😛", "😝", "😜", "🤪", "🤨", "🧐", "🤓", "😎", "🤩",
            "🥳", "😏", "😒", "😞", "😔", "😟", "😕", "🙁", "☹️", "😣",
            "😖", "😫", "😩", "🥺", "😢", "😭", "😤", "😠", "😡",
            "🤯", "😳", "🥵", "🥶", "😱", "😨", "😰", "😥", "😓", "🤗",
            "🤔", "🤭", "🤫", "🤥", "😶", "😐", "😑", "😬", "🙄", "😯",
            "😦", "😧", "😮", "😲", "🥱", "😴", "🤤", "😪", "😵", "🤐",
            "😷", "🤒", "🤕", "🤑", "🤠", "😈", "👻", "💀", "☠️", "👽",
            "👾", "🤖", "🎃", "🍉", "🍊", "🍋", "🍌", "🍍", "🍎", "🍏",
            "🌽", "🌶️", "🥬", "🥦", "🍄", "🥨", "🥞", "🧇", "🧀", "🍖",
            "🌭", "🍔", "🍟", "🍕", "🥪", "🍳", "🍲", "🍿", "🍩", "🍪",
            "🎂", "🧁", "🍫", "🍬", "🍭"
        ]
        random_emoji = random.choice(emojis)
        article.sudo().write({'icon': random_emoji})
        return {'success': True, 'icon': random_emoji}

    @http.route('/info/portal/duplicate', type='jsonrpc', auth='user')
    def info_portal_duplicate(self, article_id, **kwargs):
        """Create a duplicate copy of the article for the portal user."""
        user = request.env.user
        article = request.env['info.hub.article'].sudo().browse(int(article_id))
        if not article.exists() or not article.active or not article._can_access_portal(user):
            return {'error': 'Access Denied'}

        # Duplicate article
        new_article_id = request.env['info.hub.article'].sudo().duplicate_article(article.id)

        # Create member record for the portal user so they can access/edit it
        request.env['info.hub.article.member'].sudo().create({
            'article_id': new_article_id,
            'partner_id': user.partner_id.id,
            'permission': 'edit',
        })
        return {'success': True, 'new_article_id': new_article_id}

    @http.route('/info/portal/move_article', type='jsonrpc', auth='user')
    def info_portal_move_article(self, article_id, target_category, target_article_id=None, position='before', **kwargs):
        """Move and reorder an article in the portal."""
        user = request.env.user
        if not user.share:
            return {'success': False, 'error': 'Forbidden'}

        article = request.env['info.hub.article'].sudo().browse(int(article_id))
        if not article.exists() or not article._can_access_portal(user):
            return {'success': False, 'error': 'Forbidden'}

        # Handle favorites
        if target_category == 'favorites':
            article.write({'is_favorite': True})
            return {'success': True}

        # Check shared requirements
        resolved_category = target_category
        if target_article_id and not target_category:
            target_article = request.env['info.hub.article'].sudo().browse(int(target_article_id))
            if target_article.exists():
                resolved_category = target_article.category

        if resolved_category == 'shared' and article.category != 'shared':
            member_count = request.env['info.hub.article.member'].sudo().search_count([
                ('article_id', '=', article.id)
            ])
            if member_count < 2:
                return {
                    'success': False,
                    'error': 'You need at least 2 members for the Article to be shared.'
                }

        vals = {}
        if target_category in ['workspace', 'shared', 'private'] and article.category != target_category:
            vals['category'] = target_category
            vals['parent_id'] = False # Clear nesting on category change

        if target_article_id:
            target_article = request.env['info.hub.article'].sudo().browse(int(target_article_id))
            if target_article.exists():
                if not target_category:
                    vals['category'] = target_article.category

                sibling_domain = [('active', '=', True), ('is_template', '=', False)]
                if target_category == 'favorites':
                    sibling_domain.append(('is_favorite', '=', True))
                else:
                    sibling_domain.append(('category', '=', target_category or target_article.category))

                siblings = request.env['info.hub.article'].sudo().search(sibling_domain, order='sequence, id')

                ordered_ids = [s.id for s in siblings if s.id != article.id]
                try:
                    target_idx = ordered_ids.index(target_article.id)
                    if position == 'after':
                        insert_idx = target_idx + 1
                    else:
                        insert_idx = target_idx
                    ordered_ids.insert(insert_idx, article.id)
                except ValueError:
                    ordered_ids.append(article.id)

                for index, s_id in enumerate(ordered_ids):
                    request.env['info.hub.article'].sudo().browse(s_id).write({'sequence': (index + 1) * 10})
        else:
            if target_category in ['workspace', 'shared', 'private']:
                siblings = request.env['info.hub.article'].sudo().search([
                    ('active', '=', True),
                    ('is_template', '=', False),
                    ('category', '=', target_category)
                ], order='sequence desc', limit=1)
                max_seq = siblings[0].sequence if siblings else 0
                vals['sequence'] = max_seq + 10

        if vals:
            article.write(vals)

        return {'success': True}

    @http.route('/info/portal/search_partners', type='jsonrpc', auth='user')
    def info_portal_search_partners(self, q, **kwargs):
        """Search for partners by name/email for the invitation autocomplete widget."""
        partners = request.env['res.partner'].sudo().search([
            '|',
            ('name', 'ilike', q),
            ('email', 'ilike', q)
        ], limit=10)
        return [{'id': p.id, 'name': p.name, 'email': p.email} for p in partners]

    @http.route('/info/portal/invite', type='jsonrpc', auth='user')
    def info_portal_invite(self, article_id, partner_id, permission, **kwargs):
        """Invite a partner to the given article with the specified permission level.

        Upgrades the article from private to shared when the first external member is added.
        """
        user = request.env.user
        article = request.env['info.hub.article'].sudo().browse(int(article_id))
        if not article.exists() or not article.active or not article._can_access_portal(user):
            return {'error': 'Access Denied'}

        active_permission = article._get_user_permission(user)
        if active_permission != 'edit':
            return {'error': 'Read Only'}

        if article.create_uid != user and article.author_id != user:
            if int(partner_id) == user.partner_id.id and permission == 'none':
                pass
            else:
                return {'error': 'Access Denied: Non-owners cannot manage members.'}

        partner = request.env['res.partner'].browse(int(partner_id))
        if not partner.exists():
            return {'error': 'Partner not found'}

        existing_member = request.env['info.hub.article.member'].sudo().search([
            ('article_id', '=', article.id),
            ('partner_id', '=', partner.id)
        ], limit=1)

        if permission == 'none':
            if existing_member:
                try:
                    existing_member.unlink()
                except Exception as e:
                    return {'error': str(e)}
        else:
            if existing_member:
                try:
                    existing_member.write({'permission': permission})
                except Exception as e:
                    return {'error': str(e)}
            else:
                try:
                    request.env['info.hub.article.member'].sudo().create({
                        'article_id': article.id,
                        'partner_id': partner.id,
                        'permission': permission,
                    })
                except Exception as e:
                    return {'error': str(e)}

        return {'success': True}

    @http.route('/info/portal/toggle_published', type='jsonrpc', auth='user')
    def info_portal_toggle_published(self, article_id, publish, **kwargs):
        """Toggle the website_published flag on the given article."""
        user = request.env.user
        article = request.env['info.hub.article'].sudo().browse(int(article_id))
        if not article.exists() or not article.active or not article._can_access_portal(user):
            return {'error': 'Access Denied'}

        active_permission = article._get_user_permission(user)
        if active_permission != 'edit':
            return {'error': 'Read Only'}

        if article.create_uid != user and article.author_id != user:
            return {'error': 'Access Denied: Non-owners cannot toggle web sharing.'}

        article.sudo().write({'website_published': bool(publish)})
        return {'success': True, 'share_url': article.share_url}

    @http.route('/info/portal/update_settings', type='jsonrpc', auth='user')
    def info_portal_update_settings(self, article_id, visibility=None, default_access=None, **kwargs):
        """Update visibility and/or default_access settings on the given article."""
        user = request.env.user
        article = request.env['info.hub.article'].sudo().browse(int(article_id))
        if not article.exists() or not article.active or not article._can_access_portal(user):
            return {'error': 'Access Denied'}

        active_permission = article._get_user_permission(user)
        if active_permission != 'edit':
            return {'error': 'Read Only'}

        if article.create_uid != user and article.author_id != user:
            return {'error': 'Access Denied: Non-owners cannot change article sharing settings.'}

        vals = {}
        if visibility is not None:
            vals['visibility'] = visibility
        if default_access is not None:
            vals['default_access'] = default_access

        if vals:
            article.sudo().write(vals)
        return {'success': True}


class InformationHtmlEditorController(HTML_Editor):

    @http.route(['/web_editor/attachment/remove', '/html_editor/attachment/remove'], type='jsonrpc', auth='user', website=True)
    def remove(self, ids, **kwargs):
        """Removes a web-based image attachment if it belongs to an info_hub article the portal user has edit permission for."""
        user = request.env.user
        attachments = request.env['ir.attachment'].sudo().browse(ids)

        safe_to_unlink_sudo = True
        for attachment in attachments:
            if attachment.res_model == 'info.hub.article' and attachment.res_id:
                article = request.env['info.hub.article'].sudo().browse(int(attachment.res_id))
                if not (article.exists() and article._get_user_permission(user) == 'edit'):
                    safe_to_unlink_sudo = False
                    break
            else:
                safe_to_unlink_sudo = False
                break

        if safe_to_unlink_sudo:
            self._clean_context()
            attachments_to_remove = request.env['ir.attachment'].sudo()
            Views = request.env['ir.ui.view'].sudo()
            removal_blocked_by = {}
            for attachment in attachments:
                url = tools.html_escape(attachment.local_url)
                views = Views.search([
                    "|",
                    ('arch_db', 'like', '"%s"' % url),
                    ('arch_db', 'like', "'%s'" % url)
                ])
                if views:
                    removal_blocked_by[attachment.id] = views.read(['name'])
                else:
                    attachments_to_remove += attachment
            if attachments_to_remove:
                attachments_to_remove.unlink()
            return removal_blocked_by

        return super().remove(ids, **kwargs)

    @http.route(['/web_editor/modify_image/<model("ir.attachment"):attachment>', '/html_editor/modify_image/<model("ir.attachment"):attachment>'], type="jsonrpc", auth="user", website=True)
    def modify_image(self, attachment, res_model=None, res_id=None, name=None, data=None, original_id=None, mimetype=None, alt_data=None):
        """Allows portal users to modify images attached to articles they have edit permission for."""
        user = request.env.user
        target_model = res_model or attachment.res_model
        target_id = res_id or attachment.res_id

        if target_model == 'info.hub.article' and target_id:
            article = request.env['info.hub.article'].sudo().browse(int(target_id))
            if article.exists() and article._get_user_permission(user) == 'edit':
                self._clean_context()
                attachment_sudo = attachment.sudo()
                if not data and attachment_sudo.datas:
                    data = attachment_sudo.datas

                fields = {
                    'original_id': attachment_sudo.id,
                    'datas': data,
                    'type': 'binary',
                    'res_model': target_model,
                    'mimetype': mimetype or attachment_sudo.mimetype,
                    'name': name or attachment_sudo.name,
                    'res_id': int(target_id),
                }

                existing_attachment = get_existing_attachment(request.env['ir.attachment'].sudo(), fields)
                if existing_attachment and not existing_attachment.url:
                    attachment_new = existing_attachment
                else:
                    attachment_new = attachment_sudo.copy(fields)
                    if attachment_new.mimetype == 'text/plain' != fields['mimetype']:
                        attachment_new.with_user(SUPERUSER_ID).mimetype = fields['mimetype']

                if alt_data:
                    for size, per_type in alt_data.items():
                        reference_id = attachment_new.id
                        if 'image/webp' in per_type:
                            resized = attachment_new.sudo().create_unique([{
                                'name': attachment_new.name,
                                'description': 'resize: %s' % size,
                                'datas': per_type['image/webp'],
                                'res_id': reference_id,
                                'res_model': 'ir.attachment',
                                'mimetype': 'image/webp',
                            }])
                            reference_id = resized[0]
                        if 'image/jpeg' in per_type:
                            attachment_new.sudo().create_unique([{
                                'name': re.sub(r'\.webp$', '.jpg', attachment_new.name, flags=re.I),
                                'description': 'format: jpeg',
                                'datas': per_type['image/jpeg'],
                                'res_id': reference_id,
                                'res_model': 'ir.attachment',
                                'mimetype': 'image/jpeg',
                            }])

                if attachment_new.url:
                    if re.match(r'^/\w+/static/', attachment_new.url):
                        attachment_new.url = None
                    else:
                        url_fragments = attachment_new.url.split('/')
                        url_fragments.insert(-1, str(attachment_new.id))
                        attachment_new.url = '/'.join(url_fragments)

                if attachment_new.public:
                    return attachment_new.image_src

                attachment_new.sudo().generate_access_token()
                return '%s?access_token=%s' % (attachment_new.image_src, attachment_new.access_token)

        return super().modify_image(attachment, res_model, res_id, name, data, original_id, mimetype, alt_data)
