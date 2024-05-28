# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen (<https://www.cybrosys.com>)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.form import WebsiteForm


class WebsiteSaleForm(WebsiteForm):
    """
    Class representing a form for ecommerce checkout.
    Inherits:
    WebsiteForm: The base class for website forms, providing common
    functionalities.
    Usage:
    1. Create an instance of `WebsiteSaleForm` and customize it as needed.
    2. Use the instance to handle the checking out in your shop.
    """
    @http.route('/website/form/shop.sale.order', type='http', auth="public",
                methods=['POST'], website=True)
    def website_form_sale_order(self, **kwargs):
        """
        This function is called when the user submits the checkout form for a
        sales order on the website. It first calls the parent method `website_
        form_sale_order` to handle the submission of the form and create the
        sales order. Then, it retrieves the created sales order from the
        website session and stores its ID in the user's session. Finally,
        it redirects the user to the payment status page.

        :param kwargs: Optional keyword arguments.
        :return: A redirect to the payment status page.
        """
        super(WebsiteSaleForm, self).website_form_saleorder(**kwargs)
        order = request.website.sale_get_order()
        if request.session.get('sale_last_order_id') is None and order:
            request.session['sale_last_order_id'] = order.id
        return request.redirect('/payment/status')
