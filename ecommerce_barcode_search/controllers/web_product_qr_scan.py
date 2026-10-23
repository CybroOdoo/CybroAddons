# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER 
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteProductBarcode(WebsiteSale):
    """ Inheriting WebsiteSale for making Barcode Scanner in Website
      orders.
      """
    @http.route(['/shop/barcode/product'], type='jsonrpc', auth="public", website=True)
    def product_barcode(self, **kwargs):
        """get the last code from barcode detection and pass the url of that product"""
        input_data = kwargs.get('last_code')
        slug = request.env['ir.http']._slug
        barcode_product = request.env['product.product'].search([('barcode', '=', input_data)], limit=1)
        request.session['barcode'] = input_data
        request.session['barcode_product'] = barcode_product.id if barcode_product else False
        if barcode_product:
            url = barcode_product.website_url
            sep = '&' if '?' in url else '?'
            return {
                'type': 'ir.actions.act_url',
                'url': f'{url}{sep}extra_param=true',
            }
        else:
            return False

    @http.route()
    def product(self, product, category='', search='', **kwargs):
        is_barcode_scanned = kwargs.get('extra_param', 'false')
        is_barcode_scanned = is_barcode_scanned.lower() == 'true'
        res = super().product(product=product, category=category, search=search, **kwargs)
        if is_barcode_scanned and hasattr(res, 'qcontext'):
            combination_info = product._get_combination_info(is_barcode=True)
            res.qcontext['combination_info'] = combination_info
            if combination_info.get('product_id'):
                res.qcontext['product_variant'] = request.env['product.product'].browse(
                    combination_info['product_id']
                )
        return res
