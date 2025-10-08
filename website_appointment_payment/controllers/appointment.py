# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
################################################################################
import uuid
import pytz
from dateutil.relativedelta import relativedelta
from odoo import fields, http, Command, _
from odoo.http import request, route
from odoo.addons.appointment.controllers.appointment import \
    AppointmentController
from odoo.addons.appointment.controllers.calendar import \
    AppointmentCalendarController
import logging
from odoo.addons.base.models.ir_qweb import keep_query

_logger = logging.getLogger(__name__)


class AppointmentAccountPayment(AppointmentController):

    @http.route()
    def appointment_form_submit(
            self, appointment_type_id, datetime_str, duration_str,
            staff_user_id, name, phone, email, **kwargs):
        """Override: when a payment step is necessary, we create the appointment
            booking model to store all relevant information
            instead of creating a calendar.event.  It will
            be transformed to a 'calendar.event' on payment (or confirmation).
             See make_event on appointment.booking.
            Redirects to payment if needed. See redirect_to_payment"""
        appointment = request.env['appointment.type'].sudo().browse(
            appointment_type_id)
        partner = request.env['res.partner'].search([('email', '=like', email)])
        if not partner:
            partner = request.env['res.partner'].sudo().create({
                'name': name,
                'email': email
            })
        if appointment.has_payment_step and appointment.product_id.lst_price:
            invoice_id = request.env['account.move'].sudo().create({
                'move_type': 'out_invoice',
                'partner_id': partner.id,
                'invoice_line_ids': [Command.create({
                    'product_id': appointment.product_id.id
                })]
            })
            invoice_id.action_post()
            currency = request.env.user.company_id.currency_id
            tokens = request.env['payment.token']
            show_tokenize_input_mapping = {}
            for provider_sudo in request.env['payment.provider'].sudo().search(
                    [('is_published', '=', True)]):
                show_tokenize_input = provider_sudo.allow_tokenization \
                                      and not provider_sudo._is_tokenization_required(
                    sale_order_id=False) and request.env.user._is_public()
                show_tokenize_input_mapping[
                    provider_sudo.id] = show_tokenize_input
            values = {
                'providers': request.env['payment.provider'].sudo().search(
                    [('is_published', '=', True)]),
                'tokens': tokens,
                'amount': invoice_id.amount_total,
                'show_tokenize_input': show_tokenize_input_mapping,
                'user': request.env.user.partner_id,
                'access_token': invoice_id._portal_ensure_token(),
                'currency': currency,
                'transaction_route': f'/invoice/transaction/{invoice_id.id}',
                'landing_route': f'/payment/success/{appointment.id}'
                                 f'?mail={email}&date={datetime_str}'
                                 f'&duration={duration_str}&name={name}'
                                 f'&phone={phone}&invoice={invoice_id.id}',
                'errors': []
            }
            return request.render(
                "website_appointment_payment.appointment_payment", values)
        return super().appointment_form_submit(
            appointment_type_id, datetime_str, duration_str, staff_user_id,
            name, phone, email, **kwargs
        )

    @http.route('/payment/success/<int:appointment_id>', type='http',
                auth='public')
    def appointment_payment(self, appointment_id, **kwargs):
        """An Event is created after the payment step and redirected to the
        booking confirmation/summary page"""
        appointment = request.env['appointment.type'].browse(
            appointment_id)
        timezone = request.session.get('timezone') or appointment.appointment_tz
        tz_session = pytz.timezone(timezone)
        date_start = tz_session.localize(
            fields.Datetime.from_string(kwargs.get('date'))).astimezone(
            pytz.utc).replace(
            tzinfo=None)
        duration_hours = int(float(kwargs.get('duration')))
        date_end = date_start + relativedelta(hours=duration_hours)
        description_bits = []
        description = ''
        description_bits.append(_('Mobile: %s', kwargs.get('phone')))
        description_bits.append(_('Email: %s', kwargs.get('mail')))
        description = '<ul>' + ''.join(
            ['<li>%s</li>' % bit for bit in description_bits]) + '</ul>'
        event = request.env['calendar.event'].sudo().create({
            'name': appointment.name,
            'start': date_start,
            'stop': date_end,
            'duration': kwargs.get('duration'),
            'location': appointment.location_id.id,
            'appointment_type_id': appointment.id,
            'user_id': appointment.staff_user_ids.id,
            'invoice_ids': [(4, int(kwargs.get('invoice')))],
            'description': description,
            'access_token': uuid.uuid4().hex,
            'videocall_location': '/calendar/join_videocall/{access_token}'
        })
        partner = self._get_customer_partner() or request.env[
            'res.partner'].sudo().search(
            [('email', '=like', kwargs.get('mail'))],
            limit=1)
        return request.redirect(
            '/calendar/view/%s?partner_id=%s&%s' % (
                event.access_token, partner.id, keep_query('*', state='new')))


class AppointmentCancel(AppointmentCalendarController):

    @route(['/calendar/cancel/<string:access_token>',
            '/calendar/<string:access_token>/cancel',
            ], type='http', auth="public", website=True)
    def appointment_cancel(self, access_token, partner_id, **kwargs):
        """If the appointment is cancelled, credit note is created"""
        event = request.env['calendar.event'].sudo().search(
            [('access_token', '=', access_token)], limit=1)
        if event.invoice_ids:
            reverse_invoice = request.env[
                'account.move.reversal'].sudo().create({
                    'reason': "Appointment Cancelled",
                    'move_ids': event.invoice_ids[0],
                    'journal_id': event.invoice_ids.journal_id.id
            })
            reverse_invoice.reverse_moves()
            reversed_invoice = request.env['account.move'].sudo().search(
                [('reversed_entry_id', '=', event.invoice_ids[0].id)])
            reversed_invoice.action_post()
            journal = request.env['account.journal'].sudo().search(
                [('type', '=', 'bank'),
                 ],
                limit=1)
            register_payments = request.env[
                'account.payment.register'].with_context(
                active_model='account.move',
                active_ids=reversed_invoice.ids).sudo().create({
                    'journal_id': journal.id,
            })
            register_payments._create_payments()
        return super().appointment_cancel(access_token, partner_id, **kwargs)
