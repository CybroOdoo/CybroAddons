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
from odoo.addons.portal.controllers import portal


class ReservationCustomerPortal(portal.CustomerPortal):

    def _get_reservation_domain(self):
        """It returns the login person"""
        return [('partner_id', '=', request.env.user.partner_id.id)]

    def _check_reservation_access(self, reservation_id):
        """Fetch reservation order ensuring it exists and belongs to the current user."""
        domain = [('id', '=', reservation_id), ('is_reservation_order', '=', True)]
        if not request.env.user.has_group('sales_team.group_sale_salesman'):
            domain.append(('partner_id', '=', request.env.user.partner_id.id))
        order = request.env['sale.order'].sudo().search(domain, limit=1)
        if not order:
            raise NotFound()
        return order

    @http.route('/my/reservation/requests',
                type='http', auth='user', website=True)
    def portal_my_reservation_orders(self):
        """List out the reservation Order"""
        domain = self._get_reservation_domain()
        domain.append(('is_reservation_order', '=', True))
        values = {
            'reservation_request': request.env['sale.order'].sudo().search(
                domain),
        }
        return request.render(
            "website_product_reservation.portal_my_reservation_requests_tree",
            values)

    @http.route(['/my/reservation/requests/form/<int:reservation_id>'],
                type='http',
                auth="user", website=True)
    def get_my_reservation_request_form(self, reservation_id):
        """Form view of reservation from website"""
        order = self._check_reservation_access(reservation_id)
        return request.render(
            "website_product_reservation.portal_my_reservation_requests_form",
            {'record_reservation_requests': order})

    @http.route([
        '/my/reservation/requests/cancel/<int:reservation_id>',
        '/my/reservation/requests/form/id=<int:reservation_id>',
    ], type='http', auth="user", methods=['POST'], website=True)
    def get_my_reservation_request_form_cancel(self, reservation_id):
        """ Cancel the reservation from website"""
        order = self._check_reservation_access(reservation_id)
        order.action_cancel_reservation()
        return request.redirect(f'/my/reservation/requests/form/{order.id}')

    @http.route([
        '/my/reservation/requests/confirm/<int:reservation_id>',
        '/my/reservation/requests/form/confirm=<int:reservation_id>',
    ], type='http', auth="user", methods=['POST'], website=True)
    def get_my_reservation_request_form_confirm(self, reservation_id):
        """Confirm the reservation from website"""
        order = self._check_reservation_access(reservation_id)
        order.action_make_draft()
        order.action_confirm()
        return request.redirect(f'/my/reservation/requests/form/{order.id}')


class Return(portal.CustomerPortal):
    """Controller for portal reservation counters."""

    def _prepare_portal_counter_values(self, counter):
        if counter == 'reservation_count':
            return 'sale.order', [
                ('partner_id', '=', request.env.user.partner_id.id),
                ('is_reservation_order', '=', True),
            ], 'sudo'
        return super()._prepare_portal_counter_values(counter)

    def _prepare_home_portal_values(self, counters):
        """Return the count of reservations for the customer portal."""
        values = {}
        if hasattr(super(), '_prepare_home_portal_values'):
            values = super()._prepare_home_portal_values(counters)
        if 'reservation_count' in counters:
            values.update({
                'reservation_count': request.env[
                    'sale.order'].sudo().search_count(
                    [('partner_id', '=', request.env.user.partner_id.id),
                     ('is_reservation_order', '=', True)])
            })
        return values
