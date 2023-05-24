# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sigha CK (odoo@cybrosys.com)
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
###############################################################################
from odoo import http
from odoo.http import request


class WebsiteProduct(http.Controller):
    """
    HTTP Controller class for handling requests related to the website products.
    """

    @http.route('/get_deal_of_the_week', auth="public", type='json')
    def get_deal_of_the_week(self):
        """JSON endpoint that fetches the products from the backend marked
            as 'Deal of the Week'.Returns a rendered HTTP response with the
            fetched product information."""
        product_ids = request.env['product.template'].sudo().search([
            ('deal_check', '=', True)], limit=9)
        values = {
            'product_ids': product_ids
        }
        response = http.Response(template='theme_lego.deal_week',
                                 qcontext=values)
        return response.render()
