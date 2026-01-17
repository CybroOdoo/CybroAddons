# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys (<https://www.cybrosys.com>)
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
from odoo.addons.website.controllers.main import Website
from odoo.http import request

class ZenWebsite(Website):
    @http.route(['/about_theme_zen'], type='http', auth='public', website=True)
    def about_page(self, **kwargs):
        return request.render('theme_zen.zen_about_page', {})

    @http.route(['/services_theme_zen'], type='http', auth='public', website=True)
    def services_page(self, **kwargs):
        return request.render('theme_zen.zen_service_page', {})

    @http.route(['/portfolio_theme_zen'], type='http', auth='public', website=True)
    def portfolio_page(self, **kwargs):
        return request.render('theme_zen.zen_portfolio_page', {})