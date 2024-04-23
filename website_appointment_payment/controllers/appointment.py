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
import pytz
from dateutil.relativedelta import relativedelta
from werkzeug.exceptions import NotFound
from odoo import fields, http
from odoo.http import request
from odoo.addons.appointment.controllers.appointment import \
    AppointmentController
from odoo.addons.base.models.ir_qweb import keep_query
from odoo.addons.payment import utils


class AppointmentAccountPayment(AppointmentController):

    @http.route()
    def appointment_form_submit(
            self, appointment_type_id, datetime_str, duration_str,
            staff_user_id, name, phone, email, **kwargs
    ):
        """ Override: when a payment step is necessary, we create the appointment
            booking model to store all relevant information
            instead of creating a calendar.event.  It will
            be transformed to a calendar.event on payment (or confirmation).
             See make_event on appointment.booking.
            Redirects to payment if needed. See redirect_to_payment"""
        if kwargs.get('invite_token'):
            appointment_invite_id = request.env[
                'appointment.invite'].sudo().search(
                [('access_token', '=', kwargs.get('invite_token'))]).id
        else:
            appointment_invite_id = False
        appointment = request.env['appointment.type'].browse(
            appointment_type_id)
        timezone = request.session.get('timezone') or appointment.appointment_tz
        tz_session = pytz.timezone(timezone)
        date_start = tz_session.localize(
            fields.Datetime.from_string(datetime_str)).astimezone(
            pytz.utc).replace(
            tzinfo=None)
        duration = float(duration_str)
        date_end = date_start + relativedelta(hours=duration)
        if appointment.has_payment_step and appointment.product_id.lst_price:
            appointment_booking = request.env[
                'appointment.booking'].sudo().create([{
                'appointment_type_id': appointment_type_id,
                'appointment_invite_id': appointment_invite_id,
                'name': name,
                'product_id': appointment.product_id.id,
                'staff_user_id': staff_user_id,
                'start': date_start,
                'duration': duration,
                'stop': date_end,
            }])
            return self.redirect_to_payment(appointment_booking)
        return super().appointment_form_submit(
            appointment_type_id, datetime_str, duration_str, staff_user_id,
            name, phone, email, **kwargs
        )

    def redirect_to_payment(self, appointment_booking):
        """Booking Page is redirected to Payment Page"""
        invoice_id = appointment_booking.sudo().make_invoice()
        if not invoice_id:
            raise NotFound()
        return request.redirect(
            "/payment/pay?appointment_type_id={aid}&invoice_id={"
            "iid}&partner_id={pid}&amount={amount}&access_token={token}&{"
            "args}".format(
                aid=appointment_booking.appointment_type_id.id,
                iid=invoice_id.id,
                pid=appointment_booking.partner_id.id,
                amount=invoice_id.amount_total,
                token=utils.generate_access_token(invoice_id.partner_id.id,
                                                  invoice_id.amount_total,
                                                  invoice_id.currency_id.id),
                args=keep_query('*')
            ))
