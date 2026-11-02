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
from urllib.parse import quote_plus

from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request


class WhatsappProductInquiry(http.Controller):
    """Open WhatsApp with an inquiry about a website product."""

    @http.route('/whatsapp/inquiry/<int:product_id>', type='http',
                auth='public', website=True, sitemap=False)
    # pylint: disable=unused-argument
    def whatsapp_product_inquiry(self, product_id, **kwargs):
        """Redirect to WhatsApp with the inquiry message and the product
        link, addressed to the WhatsApp number of the website company."""
        product = self.env['product.product'].browse(product_id).exists()
        if not product or not product.website_published:
            raise NotFound()
        website = self.env.website
        company = website.company_id
        if not company.whatsapp_number:
            return request.redirect(product.website_url)
        message = '\n'.join(filter(None, [
            company.message,
            f'Product Url: {website.get_base_url()}{product.website_url}',
        ]))
        return request.redirect(
            f'https://wa.me/{company.whatsapp_number}'
            f'?text={quote_plus(message)}', local=False)
