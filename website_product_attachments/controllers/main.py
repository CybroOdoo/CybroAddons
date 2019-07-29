# -*- coding: utf-8 -*-

import base64
from werkzeug.utils import redirect
import io
from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):

    @http.route(['/shop/product/<model("product.template"):product>'], type='http', auth="public", website=True)
    def product(self, product, category='', search='', **kwargs):
        product_context = dict(request.env.context, active_id=product.id)
        ProductCategory = request.env['product.public.category']
        Rating = request.env['rating.rating']
        if category:
            category = ProductCategory.browse(int(category)).exists()

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [map(int, v.split("-")) for v in attrib_list if v]
        attrib_set = set([v[1] for v in attrib_values])
        keep = QueryURL('/shop', category=category and category.id, search=search, attrib=attrib_list)
        categs = ProductCategory.search([('parent_id', '=', False)])
        pricelist = request.website.get_current_pricelist()
        from_currency = request.env.user.company_id.currency_id
        to_currency = pricelist.currency_id
        compute_currency = lambda price: from_currency.compute(price, to_currency)
        # get the rating attached to a mail.message, and the rating stats of the product
        ratings = Rating.search([('message_id', 'in', product.website_message_ids.ids)])
        rating_message_values = dict([(record.message_id.id, record.rating) for record in ratings])
        rating_product = product.rating_get_stats([('website_published', '=', True)])
        if not product_context.get('pricelist'):
            product_context['pricelist'] = pricelist.id
            product = product.with_context(product_context)

        attachments = request.env['ir.attachment'].search(
            [('res_model', '=', 'product.template'),
             ('res_id', '=', product.id)], order='id')

        values = {
            'search': search,
            'category': category,
            'pricelist': pricelist,
            'attrib_values': attrib_values,
            'compute_currency': compute_currency,
            'attrib_set': attrib_set,
            'keep': keep,
            'categories': categs,
            'main_object': product,
            'product': product,
            '_get_attribute_exclusions': self._get_attribute_exclusions,
            'rating_message_values': rating_message_values,
            'rating_product': rating_product,
            'attachments': attachments
        }
        return request.render("website_sale.product", values)

    @http.route(['/attachment/download',], type='http', auth='public')
    def download_attachment(self, attachment_id):
        # Check if this is a valid attachment id
        attachment = request.env['ir.attachment'].sudo().search_read(
            [('id', '=', int(attachment_id))],
            ["name", "datas", "file_type", "res_model", "res_id", "type", "url"]
        )

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
            return http.send_file(data, filename=attachment['name'], as_attachment=True)
        else:
            return request.not_found()



