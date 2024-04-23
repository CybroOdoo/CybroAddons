# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from werkzeug.exceptions import NotFound
from odoo import http
from odoo.addons.payment.controllers import portal
from odoo.addons.base.models.ir_qweb import keep_query
from odoo.http import request


class AppointmentAccountPaymentPortal(portal.PaymentPortal):

    @http.route(
        '/appointment/<int:appointment_type_id>/invoice/<string:invoice_token'
        '>/post_payment',
        type='http', auth="public", website=True, sitemap=False)
    def appointment(self, invoice_token):
        """if event is created its is redirected to appointment confirmation
        page"""
        invoice_sudo = request.env['account.move'].sudo().search(
            [('access_token', '=', invoice_token)], limit=1)
        if not invoice_sudo:
            raise NotFound()
        booking = invoice_sudo.calendar_booking_ids
        if not booking:
            raise NotFound()
        if booking.calender_event_id:
            return request.redirect(
                "/calendar/view/{event_token}?partner_id={pid}&{args}".format(
                    event_token=booking.calender_event_id.access_token,
                    pid=invoice_sudo.partner_id.id,
                    args=keep_query('*')
                ))
        return request.redirect(
            f"/calendar_booking/{booking.booking_token}/view?{keep_query('*')}")

    def _get_custom_rendering_context_values(self, **kwargs):
        """appointment details are added to rendering the page"""
        rendering_context_values = super()._get_custom_rendering_context_values(
            **kwargs)
        appointment_type_id = self._cast_as_int(
            kwargs.get('appointment_type_id'))
        if not appointment_type_id:
            return rendering_context_values
        invoice_sudo = request.env['account.move'].sudo().browse(
            int(kwargs.get('invoice_id'))).exists()
        if not invoice_sudo or not invoice_sudo.calendar_booking_ids:
            raise NotFound()
        booking_sudo = invoice_sudo.calendar_booking_ids[0]
        appointment_type_sudo = booking_sudo.appointment_type_id
        if (booking_sudo.calender_event_id or not appointment_type_sudo or
                appointment_type_sudo.id != appointment_type_id):
            raise NotFound()
        invoice_token = invoice_sudo._portal_ensure_token()
        rendering_context_values.update({
            'access_token': invoice_token,
            'appointment_type': appointment_type_sudo,
            'booking': booking_sudo,
            'cancel_booking_route': f"/calendar_booking/{booking_sudo.booking_token}/cancel?{keep_query('*')}",
            'invoice_state': invoice_sudo.payment_state,
            'landing_route': "/appointment/{aid}/invoice/{"
                             "inv_token}/post_payment?partner_id={pid}".format(
                                aid=appointment_type_sudo.id,
                                inv_token=invoice_token,
                                pid=invoice_sudo.partner_id.id,
                                ),
            'transaction_route': f'/invoice/transaction/{invoice_sudo.id}',
        })
        return rendering_context_values

    def _get_payment_page_template_xmlid(self, **kwargs):
        """Redirected to payment page"""
        if kwargs.get('appointment_type_id'):
            return 'website_appointment_payment.appointment_payment'
        return super()._get_payment_page_template_xmlid(**kwargs)
