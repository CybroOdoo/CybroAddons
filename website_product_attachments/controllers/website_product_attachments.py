# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleAttachments(WebsiteSale):
    """Show product attachments on the product page and serve them."""

    @http.route()
    def product(self, product, **kwargs):
        res = super().product(product, **kwargs)
        if getattr(res, 'qcontext', None) is not None:
            res.qcontext['attachments'] = request.env[
                'ir.attachment'].sudo().search([
                    ('res_model', '=', 'product.template'),
                    ('res_id', '=', product.id),
                    ('access_token', '=', False),
                ], order='id')
        return res

    @http.route('/attachment/download', type='http', auth='public')
    def download_attachment(self, attachment_id):
        """Download a public attachment of a published product."""
        try:
            attachment_id = int(attachment_id)
        except (ValueError, TypeError):
            return request.redirect('/shop')
        attachment = request.env['ir.attachment'].sudo().search([
            ('id', '=', attachment_id),
            ('res_model', '=', 'product.template'),
            ('access_token', '=', False),
        ], limit=1)
        if not attachment:
            return request.redirect('/shop')
        product = request.env['product.template'].sudo().browse(
            attachment.res_id)
        if not (product.exists() and product.is_published
                and (not product.website_id
                     or product.website_id == request.website)):
            return request.redirect('/shop')
        if attachment.type == 'url':
            if attachment.url:
                return request.redirect(attachment.url, local=False)
            raise NotFound()
        if attachment.type == 'binary':
            return attachment._to_http_stream().get_response()
        raise NotFound()
