###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
from odoo import http
from odoo.http import request


SOCIAL_MEDIA_FIELDS = {
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


class WebsiteExtraSocialMedia(http.Controller):
    """Expose configured social links to visitors and handle redirects."""

    @http.route(
        '/website/social_media/values',
        type='jsonrpc',
        auth='public',
        website=True,
        readonly=True,
    )
    def get_social_media_values(self):
        """Return only the configured social links needed by the snippet."""
        get_param = request.env['ir.config_parameter'].sudo().get_str
        return {
            platform: get_param('website_extra_social_media.%s' % field_name) or False
            for platform, field_name in SOCIAL_MEDIA_FIELDS.items()
        }

    @http.route(
        '/website/sm/<string:platform>',
        type='http',
        auth='public',
        website=True,
    )
    def social_media_redirect(self, platform):
        """Redirect to a configured social link, or home if it is unavailable."""
        field_name = SOCIAL_MEDIA_FIELDS.get(platform)
        if not field_name:
            return request.redirect('/', local=False)

        value = request.env['ir.config_parameter'].sudo().get_str(
            'website_extra_social_media.%s' % field_name,
        )
        if not value:
            return request.redirect('/', local=False)
        if platform == 'whatsapp':
            value = 'https://api.whatsapp.com/send?phone=%s' % value
        return request.redirect(value, local=False)
