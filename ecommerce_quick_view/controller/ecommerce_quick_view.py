# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class QuickViewWebsiteSale(WebsiteSale):
    """ Controller for quick view functionality """
    @http.route('/c_quick_view/get_quick_view_html', type='json',
                auth='public', website=True)
    def get_quick_view_html(self, category='', search='', **kwargs):
        """ Generate quick view page based on given attributes """
        product_id = kwargs.get('product_id')
        product = request.env['product.template'].browse([product_id]) \
            if product_id else False
        if not product:
            return False
        value = request.env["ir.ui.view"]._render_template(
            "ecommerce_quick_view.c_product_quick_view",
            self._prepare_product_values(product, category,
                                         search, **kwargs))
        return value
