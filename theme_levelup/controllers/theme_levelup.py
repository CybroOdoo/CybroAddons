# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anurudh P(odoo@cybrosys.com)
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
from odoo import http
from odoo.http import request


class MenuController(http.Controller):
    """This controller will be used to redirect to the
    mentioned pages by clicking the menus."""

    @http.route('/about', website=True, type='http', auth='public', csrf=False)
    def about_page(self):
        """This router will be redirected to the about page."""
        return request.render('theme_levelup.about_page')

    @http.route('/portfolio', website=True, type='http', auth='public',
                csrf=False)
    def portfolio_page(self):
        """This router will be redirected to the portfolio page."""
        return request.render('theme_levelup.portfolio_page')

    @http.route('/team', website=True, type='http', auth='public', csrf=False)
    def team_page(self):
        """This router will be redirected to the team page."""
        return request.render('theme_levelup.team_page')

    @http.route('/service', website=True, type='http', auth='public',
                csrf=False)
    def service_page(self):
        """This router will be redirected to the service page."""
        return request.render('theme_levelup.service_page')

    @http.route('/blog_snippet', auth="public", type='json', website=True)
    def latest_blog(self):
        """This router will be redirected to the blog page."""
        return request.env['blog.post'].sudo().search_read([], limit=3)
