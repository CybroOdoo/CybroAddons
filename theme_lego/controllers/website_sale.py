# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fouzan M (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import http
from odoo.addons.payment.controllers import portal as payment_portal


class WebsiteSale(payment_portal.PaymentPortal):
    """
    HTTP Controller class for handling requests related to the website sale.
    """

    @http.route(['/shop/cart'], type='http', auth="public", website=True,
                sitemap=False)
    def cart(self, **post):
        """
        Render the shopping cart page with title 'CHECKOUT' on the banner.
        """
        result = super().cart(**post)
        result.qcontext['title'] = 'CHECKOUT'
        return result

    @http.route(['/shop/payment'], type='http', auth='public',
                website=True, sitemap=False)
    def shop_payment(self, **post):
        """
        Render the shopping cart page with title 'CONFIRMATION' on the banner.
        """
        result = super().shop_payment(**post)
        result.qcontext['title'] = 'CONFIRMATION'
        return result

    @http.route(['/shop/checkout'], type='http', auth="public",
                website=True, sitemap=False)
    def checkout(self, **post):
        """
        Render the address page with title 'SHIPPING' on the banner.
        """
        result = super().checkout(**post)
        result.qcontext['title'] = 'SHIPPING'
        return result
