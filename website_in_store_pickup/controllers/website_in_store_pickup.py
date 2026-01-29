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
from odoo import http
from odoo.http import request
from odoo.addons.website_sale_delivery.controllers.main import (
    WebsiteSaleDelivery)
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteInStorePickup(WebsiteSaleDelivery):
    """ Inherited  Controller to check the carrier and update in corresponding
     sale order"""

    @http.route(['/shop/check_carrier'], type='json', auth='public',
                methods=['POST'], website=True, csrf=False)
    def check_carrier(self, **post):
        """To check the carrier details and returns the relevant details
        whether the delivery method is store pick or not and returns the
        available stores"""
        carrier_id = int(post.get('carrier_id'))
        carrier = request.env['delivery.carrier'].browse(carrier_id)
        store = carrier.store_ids
        sale_order_id = http.request.session.get('sale_order_id')
        if sale_order_id:
            sale_order = http.request.env['sale.order'].sudo().browse(
                sale_order_id)
            if not carrier.is_store_pick:
                sale_order.write({
                    'partner_invoice_id': sale_order.partner_id.id,
                    'partner_shipping_id': sale_order.partner_id.id,
                })
        return {
            'is_store_pick': carrier.is_store_pick,
            'store_ids': carrier.store_ids.read(),
            'store_id': store.read(),
        }

    @http.route(['/shop/update_address'], type='json', auth='public',
                methods=['POST'], website=True, csrf=False)
    def update_address(self, **post):
        """To update the address of store address to sale order on choosing
        the store for pickup"""
        if post.get('store_id'):
            store_address = request.env['stock.warehouse'].browse(
                int(post['store_id']))
            if post['store_id']:
                sale_order_id = http.request.session.get('sale_order_id')
                if sale_order_id:
                    sale_order = http.request.env['sale.order'].sudo().browse(
                        sale_order_id)
                    sale_order.write({
                        'partner_invoice_id': store_address.partner_id.id,
                        'partner_shipping_id': store_address.partner_id.id
                    })
                    return {
                        'store_id': store_address.partner_id.read()
                    }
            return {
                'store_id': store_address.partner_id.read()
            }


class WebsiteSaleInStorePickup(WebsiteSale):
    @http.route('/shop/payment', type='http', auth='public', website=True,
                sitemap=False)
    def shop_payment(self, **post):
        """ Payment step. This page proposes several payment means based on
        available payment.acquirer. State at this point :

         - a draft sales order with lines; otherwise, clean context / session
           and back to the shop
         - no transaction in context / session, or only a draft one, if the
           customer did go to a payment.acquirer website but closed the tab
           without paying / canceling
        """
        order = request.website.sale_get_order()
        redirection = self.checkout_redirection(
            order) or self.checkout_check_address(order)
        if redirection:
            return redirection
        render_values = self._get_shop_payment_values(order, **post)
        render_values['only_services'] = order and order.only_services or False
        if render_values['errors']:
            render_values.pop('acquirers', '')
            render_values.pop('tokens', '')
        return request.render("website_sale.payment", render_values)
