# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Junaidul Ansar M (odoo@cybrosys.com)
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
from odoo.addons.website_sale.controllers.main import WebsiteSale


class PaymentController(WebsiteSale):
    @http.route('/shop/payment/validate', type='http', auth="public",
                website=True, sitemap=False)
    def shop_payment_validate(self, sale_order_id=None, **post):
        """
        Validates the payment for the sale order and updates the seat
        reservation status for event-related products. Overrides the default
        `shop_payment_validate` method from `WebsiteSale` to handle seat
        booking reservations.
        """
        res = super(
            PaymentController, self).shop_payment_validate(
            sale_order_id=sale_order_id, **post)
        last_order_id = request.session['sale_last_order_id']
        order = request.env['sale.order'].sudo().browse(last_order_id).exists()
        for line in order.order_line:
            if line.product_id.detailed_type == 'event':
                if line.event_id.is_seat_booking:
                    event_id_ticket = line.event_ticket_id.id
                    registrations = request.env[
                        'event.registration'].sudo().search(
                        [('sale_order_line_id', '=', line.id)])
                    for registration in registrations:
                        unique_column_id = registration.unique_column_id
                        seat_record = request.env[
                            'seat.arrangement.line'].sudo().search([
                            ('seat_manage_id.current_event_id', '=',
                             event_id_ticket),
                        ])
                        if seat_record:
                            column_record = seat_record.column_ids.filtered(
                                lambda
                                    c: c.unique_seat_identifier == unique_column_id)
                            column_record.write(
                                {'reservation_status': 'reserved'})
        return res
