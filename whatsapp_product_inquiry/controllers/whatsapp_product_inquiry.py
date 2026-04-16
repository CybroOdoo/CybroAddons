# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ISMAIL C A(odoo@cybrosys.com)
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

###############################################################################
import werkzeug
from odoo import http
from odoo.http import request
from urllib.parse import quote_plus
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    """Inherit WebsiteSale to add a WhatsApp product inquiry route."""
    @http.route(['/whatsapp/inquiry/<int:product>'], type='http', auth="public",
                website=True)
    def whatsapp_product_inquiry(self, product, **kw):
        """Redirect to WhatsApp web page with product details."""
        company = request.website.get_current_website().company_id
        product_obj = request.env['product.product'].browse(product)
        message = (company.message + '\nProduct Url: ' +
                   request.website.get_base_url() + product_obj.website_url)
        encoded_message = quote_plus(message)
        return werkzeug.utils.redirect("https://wa.me/%s?text=%s" % (
            company.whatsapp_number, encoded_message))
