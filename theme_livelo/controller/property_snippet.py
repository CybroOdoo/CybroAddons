# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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


class ThemeLiveloPropertySnippet(http.Controller):
    """Controller to dynamically fetch and render featured properties for snippets."""

    @http.route('/theme_livelo/get_featured_properties', type='jsonrpc', auth='public', website=True, readonly=True)
    def get_featured_properties(self, **kwargs):
        Product = request.env['product.template'].sudo()
        base_domain = [('is_property', '=', True)]
        order = 'is_featured desc, id desc'
        limit = 9

        properties_all = Product.search(base_domain, order=order, limit=limit)
        properties_apt = Product.search(base_domain + [('property_type', '=', 'apartment')], order=order, limit=limit)
        properties_villa = Product.search(base_domain + [('property_type', '=', 'villa')], order=order, limit=limit)
        properties_studio = Product.search(base_domain + [('property_type', '=', 'studio')], order=order, limit=limit)
        properties_house = Product.search(base_domain + [('property_type', '=', 'house')], order=order, limit=limit)
        properties_office = Product.search(base_domain + [('property_type', '=', 'office')], order=order, limit=limit)

        values = {
            'properties_all': properties_all,
            'properties_apt': properties_apt,
            'properties_villa': properties_villa,
            'properties_studio': properties_studio,
            'properties_house': properties_house,
            'properties_office': properties_office,
        }
        html = request.env['ir.qweb']._render('theme_livelo.property_tabs_content', values)
        return {'html': html}
