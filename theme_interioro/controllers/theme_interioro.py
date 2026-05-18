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
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class InterioroWebsite(http.Controller):
    """
    Controller for Interioro theme custom pages.
    """

    @http.route('/about', website=True, type='http', auth='public', csrf=False)
    def about(self, **kw):
        """ Render about us page """
        return request.render('theme_interioro.about_page')

    @http.route('/products', website=True, type='http', auth='public', csrf=False)
    def products(self, **kw):
        """ Render interior products and template"""
        products = request.env['interioro.product'].sudo().search(
            [('is_published', '=', True)])
        return request.render('theme_interioro.products_page', {'products': products})

    @http.route('/products/<string:slug>', website=True, type='http', auth='public', csrf=False)
    def product_detail(self, slug, **kw):
        """ Get product detail of selected interior product """
        product = request.env['interioro.product'].sudo().search(
            [('slug', '=', slug), ('is_published', '=', True)], limit=1)
        if not product:
            return request.not_found()
        return request.render('theme_interioro.product_detail_page', {'product': product})

    @http.route('/services', website=True, type='http', auth='public', csrf=False)
    def services(self, **kw):
        """ Render services """
        services = request.env['interioro.service'].sudo().search(
            [('is_published', '=', True)])
        return request.render('theme_interioro.services_page', {'services': services})

    @http.route('/services/<string:slug>', website=True, type='http', auth='public', csrf=False)
    def service_detail(self, slug, **kw):
        """ Get service details """
        service = request.env['interioro.service'].sudo().search(
            [('slug', '=', slug), ('is_published', '=', True)], limit=1)
        if not service:
            return request.not_found()
        return request.render('theme_interioro.service_detail_page', {'service': service})
