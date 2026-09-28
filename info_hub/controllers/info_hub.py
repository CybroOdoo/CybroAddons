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
from odoo import http, conf
from odoo.http import request

class InformationPublicController(http.Controller):
    """HTTP controller for the portal and public-facing info pages.

    Handles routes for shared-user portal access and public article viewing.
    """

    @http.route([
        '/info/shared',
        '/info/shared/<int:article_id>',
    ], type='http', auth='user', website=True)
    def info_shared(self, article_id=None, search=None, **kwargs):
        """Render the shared-user portal info page.

        Redirects internal users to the Odoo Information client action.
        """
        user = request.env.user
        
        if not user.share:
            if article_id:
                return request.redirect(f'/odoo/action-info_hub.action_info_client/{article_id}')
            return request.redirect('/odoo/action-info_hub.action_info_client')

        session_info = request.env['ir.http'].session_info()
        user_context = dict(request.env.context)
        mods = conf.server_wide_modules or []
        lang = user_context.get("lang") or user.lang or 'en_US'
        cache_hashes = {
            "translations": request.env['ir.http'].get_web_translations_hash(mods, lang),
        }

        session_info.update(
            cache_hashes=cache_hashes,
            user_companies={
                'current_company': request.env.company.id,
                'allowed_companies': {
                    request.env.company.id: {
                        'id': request.env.company.id,
                        'name': request.env.company.name,
                    },
                },
            },
        )

        return request.render('info_hub.portal_webclient_view', {
            'session_info': session_info,
        })

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
