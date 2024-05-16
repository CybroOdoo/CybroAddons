# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
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
#############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers import portal


class ReservationCustomerPortal(portal.CustomerPortal):

    def _get_reservation_domain(self):
        """It returns the login person"""
        return [('partner_id', '=', request.env.user.partner_id.id)]

    @http.route('/my/reservation/requests',
                type='http', auth='user', website=True)
    def portal_my_reservation_orders(self):
        """List out the reservation Order"""
        domain = self._get_reservation_domain()
        domain.append(('is_reservation_order', '=', 'True'))
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
        return request.render(
            "website_product_reservation.portal_my_reservation_requests_form",
            {'record_reservation_requests': request.env[
                'sale.order'].sudo().browse(reservation_id)})

    @http.route(['/my/reservation/requests/form/id=<int:reservation_id>'],
                type='http',
                auth="user", website=True)
    def get_my_reservation_request_form_cancel(self, reservation_id):
        """ Cancel the reservation from website"""
        cancel = request.env[
                'sale.order'].sudo().browse(reservation_id)
        cancel.action_cancel_reservation()
        return request.render(
            "website_product_reservation.portal_my_reservation_requests_form",
            {'record_reservation_requests': request.env[
                'sale.order'].sudo().browse(reservation_id)})

    @http.route(['/my/reservation/requests/form/confirm=<int:reservation_id>'],
                type='http',
                auth="user", website=True)
    def get_my_reservation_request_form_confirm(self, reservation_id):
        """Confirm the reservation from website"""
        confirm = request.env[
            'sale.order'].sudo().browse(reservation_id)
        confirm.action_make_draft()
        confirm.action_confirm()
        return request.render(
            "website_product_reservation.portal_my_reservation_requests_form",
            {'record_reservation_requests': request.env[
                'sale.order'].sudo().browse(reservation_id)})


class Return(portal.CustomerPortal):
    """This will take the count of total courier requests"""

    def _prepare_home_portal_values(self, counters):
        """This will return the certificates count"""
        values = super(Return, self)._prepare_home_portal_values(counters)
        values.update({
            'reservation_count': request.env[
                'sale.order'].sudo().search_count(
                [('partner_id', '=', request.env.user.partner_id.id),
                 ('is_reservation_order', '=', 'True')])
        })
        return values
