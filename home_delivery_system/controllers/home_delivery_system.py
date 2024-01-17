"""Delivery persons jobs"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri v (odoo@cybrosys.com)
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
#############################################################################
from odoo import http
from odoo.http import request


class WebsitePage(http.Controller):
    """Redirecting to the corresponding pages"""

    @http.route('/my_jobs', type='http', auth='public', website=True)
    def my_jobs(self, **kw):
        """Delivery persons jobs"""
        if kw.get('order_id'):
            order = request.env['stock.picking'].sudo().search(
                [('sale_id', '=', int(kw.get('order_id')))])
            order.write({
                'is_complete': True
            })
            assigned_delivery_orders = request.env[
                'stock.picking'].sudo().search(
                [('delivery_boy_id', '!=', False),
                 ('delivery_boy_id.user_id', '=', request.env.user.id),
                 ('is_complete', '=', False),
                 ('delivery_state', '!=', 'accept')])
        else:
            assigned_delivery_orders = request.env[
                'stock.picking'].sudo().search(
                [('delivery_boy_id', '!=', False),
                 ('delivery_boy_id.user_id', '=', request.env.user.id),
                 ('is_complete', '=', False)])
        values = []
        deliver_boy_jobs = {}
        if not len(assigned_delivery_orders) == 0:
            for rec in assigned_delivery_orders:
                values.append({
                    'id': rec.id,
                    'order': rec.origin,
                    'customer': rec.partner_id.name,
                    'address': rec.partner_id.street,
                    'distance': rec.distance,
                    'price': request.env['sale.order'].sudo().search(
                        [('name', '=', rec.origin)]).amount_total,
                })
                deliver_boy_jobs['delivery'] = values
            return request.render('home_delivery_system.website_my_jobs',
                                  deliver_boy_jobs)
        else:
            return request.render('home_delivery_system.website_my_jobs',
                                  deliver_boy_jobs)

    @http.route('/broadcasted_order', type='http', auth='public', website=True)
    def broadcasted_order(self):
        """To view broadcast orders in the website"""
        broadcast_order = request.env['stock.picking'].sudo().search(
            [('is_broadcast_order', '=', True)])
        values = []
        broadcasts_order = {}
        if not len(broadcast_order) == 0:
            for rec in broadcast_order:
                values.append({
                    'id': rec.id,
                    'order': rec.origin,
                    'customer': rec.partner_id.name,
                    'address': rec.partner_id.street,
                    'distance': rec.distance,
                    'price': request.env['sale.order'].sudo().search(
                        [('name', '=', rec.origin)]).amount_total,
                })
                broadcasts_order['broadcast'] = values
        return http.request.render(
            'home_delivery_system.website_broadcast_order', broadcasts_order)

    @http.route('/completed_order', type='http', auth='public', website=True)
    def completed_order(self):
        """Delivery persons completed orders"""
        completed_order = request.env['stock.picking'].sudo().search(
            [('is_complete', '!=', False)])
        values = []
        completed_orders = {}
        if not len(completed_order) == 0:
            for rec in completed_order:
                values.append({
                    'id': rec.id,
                    'order': rec.origin,
                    'customer': rec.partner_id.name,
                    'address': rec.partner_id.street,
                    'distance': rec.distance,
                    'price': request.env['sale.order'].sudo().search(
                        [('name', '=', rec.origin)]).amount_total,
                    'status': 'Paid'
                })
                completed_orders['completed'] = values
        return http.request.render(
            'home_delivery_system.website_completed_order', completed_orders)

    @http.route('/delivery/option/<int:orderid>', methods=['POST', 'GET'],
                type='http', auth='public', website=True)
    def delivery(self, orderid):
        """The delivery person deliver the orders"""
        delivery_order = request.env['stock.picking'].sudo().search(
            [('id', '=', orderid)])
        values = []
        product = []
        delivery_order_details = {}
        values.append({
            'id': delivery_order.sale_id.id,
            'order': delivery_order.sale_id.name,
            'customer': delivery_order.sale_id.partner_id.name,
            'address': delivery_order.sale_id.partner_id.street,
            'street': delivery_order.sale_id.partner_id.street2 or '',
            'city': delivery_order.sale_id.partner_id.city or '',
            'zip': delivery_order.sale_id.partner_id.zip or '',
            'country': delivery_order.sale_id.partner_id.country_id.name or '',
            'phone': delivery_order.sale_id.partner_id.phone,
            'price': delivery_order.sale_id.amount_total,
            'payment': delivery_order.payment_status,
        })
        for rec in delivery_order.sale_id.order_line:
            product.append({
                'product': rec.product_id.name,
                'qty': rec.product_uom_qty,
                'total': delivery_order.sale_id.amount_total
            })
        delivery_order_details['delivery_order'] = values
        delivery_order_details['product'] = product
        return http.request.render(
            'home_delivery_system.website_delivery_option',
            delivery_order_details)

    @http.route('/delivery/issue', methods=['POST', 'GET'], type='http',
                auth='public', website=True)
    def issue(self, **POST):
        """It returns the delivery person can post an issue,while any
        issue arrived at the time of delivery"""
        order = request.env['sale.order'].browse(int(POST.get('id')))
        order.write({
            'note': POST.get('message')
        })
        values = []
        product = []
        delivery_order_details = {}
        values.append({
            'id': order.id,
            'order': order.name,
            'customer': order.partner_id.name,
            'address': order.partner_id.street,
            'street': order.partner_id.street2 or '',
            'city': order.partner_id.city or '',
            'zip': order.partner_id.zip or '',
            'country': order.partner_id.country_id.name or '',
            'phone': order.partner_id.phone,
            'price': order.amount_total,
            'payment': request.env['stock.picking'].sudo().search(
                [('sale_id', '=', order.id)]).payment_status,
        })
        for rec in order.order_line:
            product.append({
                'product': rec.product_id.name,
                'qty': rec.product_uom_qty,
                'total': order.amount_total
            })
        delivery_order_details['delivery_order'] = values
        delivery_order_details['product'] = product
        return http.request.render(
            'home_delivery_system.website_delivery_option',
            delivery_order_details)
