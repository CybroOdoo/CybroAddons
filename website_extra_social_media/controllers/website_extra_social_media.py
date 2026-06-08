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
    """Handle social media redirection routes for the website."""

    @http.route(['/website/sm/instagram'], type="http", auth="public")
    def instagram(self):
        """Redirect to the configured Instagram URL."""
        values = self._get_social_values()
        if values.get('instagram_link'):
            url = values['instagram_link']
            return request.redirect(url, local=False)
        return request.redirect('/', local=False)

    @http.route(['/website/sm/whatsapp'], type="http", auth="public")
    def whatsapp(self):
        """Redirect to WhatsApp chat using the configured number."""
        values = self._get_social_values()
        if values.get('whatsapp_link'):
            url = 'https://api.whatsapp.com/send?phone=' + values.get('whatsapp_link')
            return request.redirect(url, local=False)
        return request.redirect('/', local=False)

    @http.route(['/website/sm/github'], type="http", auth="public")
    def github(self):
        """Redirect to the configured GitHub URL."""
        values = self._get_social_values()
        if values.get('github_link'):
            url = values['github_link']
            return request.redirect(url, local=False)
        return request.redirect('/', local=False)

    @http.route(['/website/sm/youtube'], type="http", auth="public")
    def youtube(self):
        """Redirect to the configured YouTube URL."""
        values = self._get_social_values()
        if values.get('youtube_link'):
            url = values['youtube_link']
            return request.redirect(url, local=False)
        return request.redirect('/', local=False)

    @http.route(['/website/sm/google_plus'], type="http", auth="public")
    def google_plus(self):
        """Redirect to the configured Google+ URL."""
        values = self._get_social_values()
        if values.get('google_plus_link'):
            url = values['google_plus_link']
            return request.redirect(url, local=False)
        return request.redirect('/', local=False)

    @http.route(['/website/sm/snapchat'], type="http", auth="public")
    def snapchat(self):
        """Redirect to the configured Snapchat URL."""
        values = self._get_social_values()
        if values.get('snapchat_link'):
            url = values['snapchat_link']
            return request.redirect(url, local=False)
        return request.redirect('/', local=False)

    @http.route(['/website/sm/flickr'], type="http", auth="public")
    def flickr(self):
        """Redirect to the configured Flickr URL."""
        values = self._get_social_values()
        if values.get('flickr_link'):
            url = values['flickr_link']
            return request.redirect(url, local=False)
        return request.redirect('/', local=False)

    @http.route(['/website/sm/quora'], type="http", auth="public")
    def quora(self):
        """Redirect to the configured Quora URL."""
        values = self._get_social_values()
        if values.get('quora_link'):
            url = values['quora_link']
            return request.redirect(url, local=False)
        return request.redirect('/', local=False)

    @http.route(['/website/sm/pinterest'], type="http", auth="public")
    def pinterest(self):
        """Redirect to the configured Pinterest URL."""
        values = self._get_social_values()
        if values.get('pinterest_link'):
            url = values['pinterest_link']
            return request.redirect(url, local=False)
        return request.redirect('/', local=False)

    @http.route(['/website/sm/dribbble'], type="http", auth="public")
    def dribbble(self):
        """Redirect to the configured Dribbble URL."""
        values = self._get_social_values()
        if values.get('dribble_link'):
            url = values['dribble_link']
            return request.redirect(url, local=False)
        return request.redirect('/', local=False)

    @http.route(['/website/sm/tumblr'], type="http", auth="public")
    def tumblr(self):
        """Redirect to the configured Tumblr URL."""
        values = self._get_social_values()
        if values.get('tumblr_link'):
            url = values['tumblr_link']
            return request.redirect(url, local=False)
        return request.redirect('/', local=False)

    def _get_social_values(self):
        """Fetch configured social media values from settings."""
        return request.env['res.config.settings'].sudo().default_get(
            request.env['res.config.settings'].fields_get().keys()
        )
