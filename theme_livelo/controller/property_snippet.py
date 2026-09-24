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


class PropertySnippetController(http.Controller):

    @http.route('/get_property_list', auth="public", type='json', website=True)
    def get_property_list(self):
        """Get properties for the dynamic snippet."""
        domain = [('is_property', '=', True)]
        fields = ['id', 'name', 'list_price', 'listing_type', 'location', 'is_featured', 'bed', 'bath', 'squarefeet', 'website_url', 'property_type']
        properties = request.env['product.template'].sudo().search_read(domain, fields=fields, limit=18)
        for prop in properties:
            prop['formatted_price'] = '{:,}'.format(int(prop['list_price'])) if prop.get('list_price') else '0'
        return {
            'properties': properties,
        }
