# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fasluca @ cybrosys,(odoo@cybrosys.com)
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
#
#############################################################################
# -*- coding: utf-8 -*-

import base64
from werkzeug.utils import redirect
import io
from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):

    @http.route(['/shop/<model("product.template"):product>'], type='http',
                auth="public", website=True)
    def product(self, product, category='', search='', **kwargs):
        res = super(WebsiteSale, self).product(product, category='', search='',
                                               **kwargs)
        attachments = request.env['ir.attachment'].sudo().search(
            [('res_model', '=', 'product.template'),
             ('res_id', '=', product.id)], order='id')
        res.qcontext['attachments'] = attachments
        return res

    def _get_attribute_exclusion(self, product, reference_product=None):
        parent_combination = request.env['product.template.attribute.value']
        if reference_product:
            parent_combination |= reference_product.product_template_attribute_value_ids
            if reference_product.env.context.get('no_variant_attribute_values'):
                # Add "no_variant" attribute values' exclusions
                # They are kept in the context since they are not linked to this product variant
                parent_combination |= reference_product.env.context.get(
                    'no_variant_attribute_values')
        return product._get_attribute_exclusions(parent_combination)

    @http.route(['/attachment/download', ], type='http', auth='public')
    def download_attachment(self, attachment_id):
        # Check if this is a valid attachment id
        attachment = request.env['ir.attachment'].sudo().search(
            [('id', '=', int(attachment_id))])

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
