# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Shafna K(odoo@cybrosys.com)
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
###############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.website_sale_delivery.controllers.main import (
    WebsiteSaleDelivery)


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
        store = request.env['stock.warehouse'].search(
            [('is_store', '=', True)])
        carrier = request.env['delivery.carrier'].browse(carrier_id)
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
