# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sreerag PM(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import http
from odoo.http import request


class WebsiteExtraSocialMedia(http.Controller):
    """Class for the controllers of website_extra_social_media."""

    @http.route(['/website/sm/whatsapp'], type="http", auth="public")
    def whatsapp(self):
        """ when clicking on the whatsapp icon in the website, it will enter
            to this controller,and it will redirect to the
            link - 'https://api.whatsapp.com/send?phone='with the number that
            in the configuration settings of website module."""
        request.website = request.env[
            'website'].sudo().get_current_website()
        website_id = request.website
        if website_id.social_whatsapp is not False:
            url = 'https://api.whatsapp.com/send?phone=' + website_id.social_whatsapp
            return request.redirect(url, local=False)

    @http.route(['/website/sm/google/plus'], type="http", auth="public")
    def google_plus(self):
        """ when clicking on the Google plus icon in the website, it will enter
            to this controller,and it will redirect to the link that in the
            configuration settings of website module."""
        request.website = request.env[
            'website'].sudo().get_current_website()
        website_id = request.website
        if website_id.social_google_plus is not False:
            url = website_id.social_google_plus
            return request.redirect(url, local=False)

    @http.route(['/website/sm/snapchat'], type="http", auth="public")
    def snapchat(self):
        """ when clicking on the snapchat icon in the website, it will enter
            to this controller,and it will redirect to the link that in the
            configuration settings of website module."""
        request.website = request.env[
            'website'].sudo().get_current_website()
        website_id = request.website
        if website_id.social_snapchat is not False:
            url = website_id.social_snapchat
            return request.redirect(url, local=False)

    @http.route(['/website/sm/flickr'], type="http", auth="public")
    def flickr(self):
        """ when clicking on the flickr icon in the website, it will enter
            to this controller,and it will redirect to the link that in the
            configuration settings of website module."""
        request.website = request.env[
            'website'].sudo().get_current_website()
        website_id = request.website
        if website_id.social_flickr is not False:
            url = website_id.social_flickr
            return request.redirect(url, local=False)

    @http.route(['/website/sm/quora'], type="http", auth="public")
    def quora(self):
        """ when clicking on the quora icon in the website, it will enter to
            this controller,and it will redirect to the link that in the
            configuration settings of website module."""
        request.website = request.env[
            'website'].sudo().get_current_website()
        website_id = request.website
        if website_id.social_quora is not False:
            url = website_id.social_quora
            return request.redirect(url, local=False)

    @http.route(['/website/sm/pinterest'], type="http", auth="public")
    def pinterest(self):
        """ when clicking on the pinterest icon in the website, it will enter
            to this controller,and it will redirect to the link that in the
            configuration settings of website module."""
        request.website = request.env[
            'website'].sudo().get_current_website()
        website_id = request.website
        if website_id.social_pinterest is not False:
            url = website_id.social_pinterest
            return request.redirect(url, local=False)

    @http.route(['/website/sm/dribble'], type="http", auth="public")
    def dribble(self):
        """ when clicking on the dribble icon in the website, it will enter to
            this controller,and it will redirect to the link that in the
            configuration settings of website module."""
        request.website = request.env[
            'website'].sudo().get_current_website()
        website_id = request.website
        if website_id.social_dribble is not False:
            url = website_id.social_dribble
            return request.redirect(url, local=False)

    @http.route(['/website/sm/tumblr'], type="http", auth="public")
    def tumblr(self):
        """ when clicking on the tumblr icon in the website, it will enter to
            this controller,and it will redirect to the link that in the
            configuration settings of website module."""
        request.website = request.env[
            'website'].sudo().get_current_website()
        website_id = request.website
        if website_id.social_tumblr is not False:
            url = website_id.social_tumblr
            return request.redirect(url, local=False)
