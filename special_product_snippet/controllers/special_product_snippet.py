# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import json
from odoo import http
from odoo.http import request


class SpecialProduct(http.Controller):
    """ Getting product details  and passing returning
        the values and rendering the templates from js"""

    @http.route('/website/snippet/special/render', type='json', auth='public',
                website=True)
    def render_template(self, params):
        res = json.loads(params)
        product = request.env['product.template'].sudo().search_read(
            [('id', '=', res['id'])])
        qcontext = {}
        for rec in product:
            qcontext['display_name'] = rec['display_name']
            qcontext['list_price'] = rec['list_price']
            qcontext['website_url'] = rec['website_url']
            qcontext[
                'image_url'] = '/web/image/product.template/%s/image_1920' % \
                               rec['id']
        return {
            'qcontext': qcontext
        }
