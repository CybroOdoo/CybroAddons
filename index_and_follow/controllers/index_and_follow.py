# -*- coding: utf-8 -*-
#############################################################################
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
"""Controllers for website index and follow functionality."""
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebIndexJson(http.Controller):
    """ Controller for website index and follow """

    @http.route('/web_index', type='jsonrpc', auth='user')
    def web_index(self, index, product):
        """ Route for index """
        if not request.env.user.has_group('base.group_user'):
            return {'error': 'Access Denied'}
        product_rec = request.env['product.template'].browse(int(product))
        if product_rec.exists():
            product_rec.sudo().write({'is_index': bool(index)})
        return {'success': True}


class WebIndex(WebsiteSale):
    """ Class for website_sale """

    def _prepare_product_values(self, product, category=None, **kwargs):
        """ Function for access user along with product """
        if category:
            kwargs['category'] = category
        res = super()._prepare_product_values(product, **kwargs)
        res.update({
            'page_index': product.is_index,
            'product_rec': product,
            'user': request.env.user.has_group('base.group_user')
        })
        return res
