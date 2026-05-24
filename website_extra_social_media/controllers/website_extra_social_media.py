# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import http
from odoo.http import request


class WebsiteExtraSocialMedia(http.Controller):
    """Handle social media redirection routes."""

    def _get_config_param(self, key):
        """
        Fetch a configuration parameter value by key.
        """
        return request.env['ir.config_parameter'].sudo().get_param(key)

    @http.route('/website/sm/<string:platform>', type="http", auth="public", website=True)
    def redirect_social(self, platform):
        """Redirect to configured social media URL."""
        key_map = {
            'instagram': 'instagram_link',
            'whatsapp': 'whatsapp_link',
            'github': 'github_link',
            'youtube': 'youtube_link',
            'google_plus': 'google_plus_link',
            'snapchat': 'snapchat_link',
            'flickr': 'flickr_link',
            'quora': 'quora_link',
            'pinterest': 'pinterest_link',
            'dribbble': 'dribbble_link',
            'tumblr': 'tumblr_link',
        }

        key = key_map.get(platform)
        if not key:
            return request.redirect('/', local=False)

        value = self._get_config_param(f'website_extra_social_media.{key}')

        if platform == 'whatsapp' and value:
            value = f'https://api.whatsapp.com/send?phone={value}'

        if value:
            return request.redirect(value, local=False)

        return request.redirect('/', local=False)
