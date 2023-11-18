# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Amaya Aravind(odoo@cybrosys.com)
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
    @http.route(['/website/sm/facebook'], type="http", auth="public")
    def facebook(self):
        """ when clicking on the facebook icon in the website, it will enter
            to this controller,and it will redirect to the link that in the
            configuration settings of website module."""
        values = request.env['res.config.settings'].sudo().default_get(
            list(request.env['res.config.settings'].fields_get()))
        if values['facebook_link'] is not False:
            url = values['facebook_link']
            return request.redirect(url, local=False)

    @http.route(['/website/sm/twitter'], type="http", auth="public")
    def twitter(self):
        """ when clicking on the twitter icon in the website, it will enter to
            this controller,and it will redirect to the link that in the
            configuration settings of website module."""
        values = request.env['res.config.settings'].sudo().default_get(
            list(request.env['res.config.settings'].fields_get()))
        if values['twitter_link'] is not False:
            url = values['twitter_link']
            return request.redirect(url, local=False)

    @http.route(['/website/sm/linkedin'], type="http", auth="public")
    def linkedin(self):
        """ when clicking on the LinkedIn icon in the website, it will enter
            to this controller,and it will redirect to the link that in the
            configuration settings of website module."""
        values = request.env['res.config.settings'].sudo().default_get(
            list(request.env['res.config.settings'].fields_get()))
        if values['linkedin_link'] is not False:
            url = values['linkedin_link']
            return request.redirect(url, local=False)

    @http.route(['/website/sm/instagram'], type="http", auth="public")
    def instagram(self):
        """ when clicking on the instagram icon in the website, it will enter
            to this controller,and it will redirect to the link that in the
            configuration settings of website module."""
        values = request.env['res.config.settings'].sudo().default_get(
            list(request.env['res.config.settings'].fields_get()))
        if values['instagram_link'] is not False:
            url = values['instagram_link']
            return request.redirect(url, local=False)

    @http.route(['/website/sm/whatsapp'], type="http", auth="public")
    def whatsapp(self):
        """ when clicking on the whatsapp icon in the website, it will enter
            to this controller,and it will redirect to the
            link - 'https://api.whatsapp.com/send?phone='with the number that
            in the configuration settings of website module."""
        values = request.env['res.config.settings'].sudo().default_get(
            list(request.env['res.config.settings'].fields_get()))
        if values['whatsapp_link'] is not False:
            url = 'https://api.whatsapp.com/send?phone=' + values[
                'whatsapp_link']
            return request.redirect(url, local=False)

    @http.route(['/website/sm/github'], type="http", auth="public")
    def github(self):
        """ when clicking on the gitHub icon in the website, it will enter to
            this controller,and it will redirect to the link that in the
            configuration settings of website module."""
        values = request.env['res.config.settings'].sudo().default_get(
            list(request.env['res.config.settings'].fields_get()))
        if values['github_link'] is not False:
            url = values['github_link']
            return request.redirect(url, local=False)

    @http.route(['/website/sm/youtube'], type="http", auth="public")
    def youtube(self):
        """ when clicking on the YouTube icon in the website, it will enter to
            this controller,and it will redirect to the link that in the
            configuration settings of website module."""
        values = request.env['res.config.settings'].sudo().default_get(
            list(request.env['res.config.settings'].fields_get()))
        if values['youtube_link'] is not False:
            url = values['youtube_link']
            return request.redirect(url, local=False)

    @http.route(['/website/sm/google/plus'], type="http", auth="public")
    def google_plus(self):
        """ when clicking on the Google plus icon in the website, it will enter
            to this controller,and it will redirect to the link that in the
            configuration settings of website module."""
        values = request.env['res.config.settings'].sudo().default_get(
            list(request.env['res.config.settings'].fields_get()))
        if values['google_plus_link'] is not False:
            url = values['google_plus_link']
            return request.redirect(url, local=False)

    @http.route(['/website/sm/snapchat'], type="http", auth="public")
    def snapchat(self):
        """ when clicking on the snapchat icon in the website, it will enter
            to this controller,and it will redirect to the link that in the
            configuration settings of website module."""
        values = request.env['res.config.settings'].sudo().default_get(
            list(request.env['res.config.settings'].fields_get()))
        if values['snapchat_link'] is not False:
            url = values['snapchat_link']
            return request.redirect(url, local=False)

    @http.route(['/website/sm/flickr'], type="http", auth="public")
    def flickr(self):
        """ when clicking on the flickr icon in the website, it will enter
            to this controller,and it will redirect to the link that in the
            configuration settings of website module."""
        values = request.env['res.config.settings'].sudo().default_get(
            list(request.env['res.config.settings'].fields_get()))
        if values['flickr_link'] is not False:
            url = values['flickr_link']
            return request.redirect(url, local=False)

    @http.route(['/website/sm/quora'], type="http", auth="public")
    def quora(self):
        """ when clicking on the quora icon in the website, it will enter to
            this controller,and it will redirect to the link that in the
            configuration settings of website module."""
        values = request.env['res.config.settings'].sudo().default_get(
            list(request.env['res.config.settings'].fields_get()))
        if values['quora_link'] is not False:
            url = values['quora_link']
            return request.redirect(url, local=False)

    @http.route(['/website/sm/pinterest'], type="http", auth="public")
    def pinterest(self):
        """ when clicking on the pinterest icon in the website, it will enter
            to this controller,and it will redirect to the link that in the
            configuration settings of website module."""
        values = request.env['res.config.settings'].sudo().default_get(
            list(request.env['res.config.settings'].fields_get()))
        if values['pinterest_link'] is not False:
            url = values['pinterest_link']
            return request.redirect(url, local=False)

    @http.route(['/website/sm/dribble'], type="http", auth="public")
    def dribble(self):
        """ when clicking on the dribble icon in the website, it will enter to
            this controller,and it will redirect to the link that in the
            configuration settings of website module."""
        values = request.env['res.config.settings'].sudo().default_get(
            list(request.env['res.config.settings'].fields_get()))
        if values['dribble_link'] is not False:
            url = values['dribble_link']
            return request.redirect(url, local=False)

    @http.route(['/website/sm/tumblr'], type="http", auth="public")
    def tumblr(self):
        """ when clicking on the tumblr icon in the website, it will enter to
            this controller,and it will redirect to the link that in the
            configuration settings of website module."""
        values = request.env['res.config.settings'].sudo().default_get(
            list(request.env['res.config.settings'].fields_get()))
        if values['tumblr_link'] is not False:
            url = values['tumblr_link']
            return request.redirect(url, local=False)
