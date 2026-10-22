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
from odoo import http
from odoo.http import request
from odoo.tools.mimetypes import guess_mimetype
from odoo.addons.website_sale.controllers import main

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIMETYPES = {
    'application/pdf',
    'image/gif',
    'image/jpeg',
    'image/png',
    'image/webp',
    'text/plain',
    'text/csv',
    'application/msword',
    'application/vnd.ms-excel',
    'application/vnd.oasis.opendocument.spreadsheet',
    'application/vnd.oasis.opendocument.text',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}


class WebsiteSaleFileUpload(main.WebsiteSale):
    """Let customers attach files to their order on the payment page"""

    def _get_order_attachments(self, order):
        """Return the files the current visitor uploaded on the order"""
        return request.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', order.id),
            ('create_uid', '=', request.env.uid),
        ])

    def _upload_attachment(self, order, upload):
        """Attach the uploaded file to the order and return an error, if any"""
        content = upload.read(MAX_FILE_SIZE + 1)
        if not content:
            return request.env._("The file is empty.")
        if len(content) > MAX_FILE_SIZE:
            return request.env._("The file is larger than 10 MB.")
        mimetype = guess_mimetype(content)
        if mimetype not in ALLOWED_MIMETYPES:
            return request.env._(
                "This file type is not allowed. Upload a PDF, an image, a "
                "text file, a document or a spreadsheet.")
        request.env['ir.attachment'].sudo().create({
            'name': upload.filename,
            'res_name': upload.filename,
            'type': 'binary',
            'res_model': 'sale.order',
            'res_id': order.id,
            'raw': content,
            'mimetype': mimetype,
        })
        return False

    @http.route()
    def shop_payment(self, **post):
        """Upload the posted file and list the visitor's files"""
        upload = post.pop('attachment', None)
        response = super().shop_payment(**post)
        order = request.cart
        # The parent redirects when the cart is empty or the checkout is
        # incomplete: there is no page to add the files to
        if not order or not hasattr(response, 'qcontext'):
            return response
        error = upload and self._upload_attachment(order, upload)
        response.qcontext.update({
            'attachment': self._get_order_attachments(order),
            'attachment_error': error,
        })
        return response

    @http.route('/shop/attachments', type='jsonrpc', auth='public',
                website=True, sitemap=False)
    def shop_attachments(self, attachment_id=None, **post):
        """Delete a file the visitor uploaded on the current cart"""
        order = request.cart
        if not order or not attachment_id:
            return 0
        try:
            attachment_id = int(attachment_id)
        except (ValueError, TypeError):
            return 0
        attachment = self._get_order_attachments(order).filtered(
            lambda att: att.id == attachment_id)
        if not attachment:
            return 0
        attachment.unlink()
        return 1
