# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ranjith R(odoo@cybrosys.com)
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
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    """For adding the Whatsapp Inquiry function"""

    @http.route(['/whatsapp/inquiry/<int:product>'], type='http',
                auth="public", website=True)
    def whatsapp_product_inquiry(self, **kw):
        """Redirect to whatsapp web page"""
        return werkzeug.utils.redirect("https://wa.me/%s?text=%s" % (
            request.website.get_current_website().company_id.whatsapp_number,
            request.website.get_current_website().company_id.message +
            '\nProduct Url: ' +
            request.website.get_base_url() +
            request.env['product.product'].browse(kw['product']).website_url))
