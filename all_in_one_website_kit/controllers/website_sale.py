# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Yadhukrishnan K (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
################################################################################
import base64
import io
from werkzeug.utils import redirect
from odoo import http
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    """ The class WebsiteProductBarcode is used for getting product with scanned
        barcode"""

    @http.route([
        '/shop/barcodeproduct'], type='json', auth="user", website=True,
        methods=['GET', 'POST'])
    def product_barcode(self, **kwargs):
        """ checking the is scanned or not  and passes the corresponding
            values"""
        barcode_product = request.env['product.product'].search(
            [('barcode', '=', kwargs.get('last_code'))])
        if barcode_product:
            return {
                'type': 'ir.actions.act_url',
                'url': '/shop/%s' % slug(barcode_product.product_tmpl_id)
            }
        else:
            return False

    @http.route(['/shop/<model("product.template"):product>'], type='http',
                auth="public", website=True)
    def product(self, product, category='', search='', **kwargs):
        """supering the controller to pass the values"""
        res = super(WebsiteSale, self).product(product, category='', search='',
                                               **kwargs)
        res.qcontext['attachments'] = request.env[
            'ir.attachment'].sudo().search(
            [('res_model', '=', 'product.template'),
             ('res_id', '=', product.id)], order='id')
        return res

    def _get_attribute_exclusion(self, product, reference_product=None):
        """check the product variant"""
        parent_combination = request.env['product.template.attribute.value']
        if reference_product:
            parent_combination |= reference_product.product_template_attribute_value_ids
            if reference_product.env.context.get('no_variant_attribute_values'):
                # Add "no_variant" attribute values' exclusions
                # They are kept in the context since they are not linked to this
                # product variant
                parent_combination |= reference_product.env.context.get(
                    'no_variant_attribute_values')
        return product._get_attribute_exclusions(parent_combination)

    @http.route(['/attachment/download', ], type='http', auth='public')
    def download_attachment(self, attachment_id):
        """To download the document of the product"""
        # Check if this is a valid attachment id
        attachment = request.env['ir.attachment'].sudo().browse(
            int(attachment_id))
        if attachment:
            attachment = attachment[0]
        else:
            return redirect('/shop')
        if attachment["type"] == "url":
            if attachment["url"]:
                return redirect(attachment["url"])
            else:
                return request.not_found()
        elif attachment["datas"]:
            data = io.BytesIO(base64.standard_b64decode(attachment["datas"]))
            return http.send_file(data, filename=attachment['name'],
                                  as_attachment=True)
        else:
            return request.not_found()
