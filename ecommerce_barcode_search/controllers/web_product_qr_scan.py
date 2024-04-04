# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from odoo.addons.http_routing.models.ir_http import slug
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteProductBarcode(WebsiteSale):
    """ Inheriting WebsiteSale for making Barcode Scanner in Website
      orders.
      """
    @http.route(['/shop/barcodeproduct'], type='json', auth="user", website=True, methods=['GET', 'POST'])
    def product_barcode(self,**kwargs):
        """get the last code from barcode detection and pass the url of that product"""
        input_data = kwargs.get('last_code')
        barcode_product = request.env['product.product'].search([('barcode', '=', input_data)])
        if barcode_product:
            return {
                        'type': 'ir.actions.act_url',
                        'url': '/shop/%s' % slug(barcode_product.product_tmpl_id)
                    }
        else:
            return False
