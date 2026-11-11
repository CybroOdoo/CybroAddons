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
import logging
from datetime import datetime, time
import pytz
from odoo import fields, http
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class SalonBookingWeb(http.Controller):
    """Route to do salon website operations."""

    def _get_user_timezone(self):
        """Helper method to get user timezone or fallback to UTC"""
        user_tz = request.env.user.tz
        if user_tz and isinstance(user_tz, str):
            return user_tz
        return 'UTC'  # Fallback to UTC if timezone is not set or invalid

    def _get_active_stage_ids(self, codes):
        """Ids of the stages with the given codes (resolved by XML id)."""
        stage_model = request.env['salon.stage']
        return [s for s in (stage_model._get_stage_id(c) for c in codes) if s]

    def _resolve_timezone(self, candidate=None):
        """Return a valid pytz timezone name to interpret the date/time
        the visitor typed on the website.

        Anonymous visitors are logged in as the Public User, whose ``tz``
        field is normally empty, so ``_get_user_timezone`` silently falls
        back to UTC. If that fallback is used to interpret a booking
        typed in, say, IST, the time saved on the record ends up several
        hours off from what the customer actually asked for - this is
        the root cause of bookings looking "wrong" once they reach the
        backend. To avoid that, the website widget detects the visitor's
        browser timezone (``Intl.DateTimeFormat().resolvedOptions().timeZone``)
        and sends it along as ``tz``; we use it here when it is a valid
        timezone name, and only fall back to the user/UTC timezone when
        it isn't available (e.g. JS blocked, or an older cached page).
        """
        if candidate:
            try:
                pytz.timezone(candidate)
                return candidate
            except pytz.exceptions.UnknownTimeZoneError:
                _logger.info("Unknown timezone received: %s", candidate)
        return self._get_user_timezone()

    @http.route(route='/page/salon_details', type='jsonrpc', auth='public',
                csrf=False)
    def salon_details(self, name, date, salon_time, phone, email, chair,
                      service_list, tz=None):
        """Create a salon booking from website data and store the booking time in UTC."""
        user_tz = self._resolve_timezone(tz)
        try:
            dates_time = date + " " + salon_time + ":00"
            date_and_time = (
                pytz.timezone(user_tz)
                .localize(datetime.strptime(dates_time, '%Y-%m-%d %H:%M:%S'))
                .astimezone(pytz.UTC)
                .replace(tzinfo=None)
            )
        except (ValueError, TypeError):
            # Malformed date/time coming from the form (e.g. a browser
            # that didn't enforce the input type). Report it instead of
            # letting the request crash with a generic server error.
            return {'result': False,
                    'error': "Please select a valid date and time."}

        try:
            # Savepoint: a rejected booking (e.g. chair already taken) must
            # not stay in the database once the error is returned.
            with request.env.cr.savepoint():
                request.env['salon.booking'].create({
                    'name': name,
                    'phone': phone,
                    'time': date_and_time,
                    'email': email,
                    'chair_id': chair,
                    'service_ids': [(6, 0, request.env['salon.service'].sudo()
                                     .search([('id', 'in', service_list)]).ids)],
                })
        except ValidationError as error:
            # The chosen chair/time is no longer available (e.g. someone
            # else just booked it). Return the reason instead of a 500.
            return {'result': False, 'error': error.args[0]}
        except Exception:
            # Any other unexpected failure (missing chair, bad service
            # id, etc.) - fail politely on the website instead of
            # bubbling up a raw server error to the visitor.
            return {'result': False,
                    'error': "We couldn't submit your booking. Please check "
                             "your details and try again."}

        return {'result': True}

    @http.route('/page/salon_check_date', type='jsonrpc', auth="public")
    def salon_check(self, **kwargs):
        """Fetch salon booking details for a given date, grouped by chair."""
        year, month, day = map(int, kwargs['check_date'].split('-'))
        user_tz = self._resolve_timezone(kwargs.get('tz'))
        date_start = pytz.timezone(user_tz).localize(
            datetime(year, month, day, hour=0, minute=0, second=0)).astimezone(
            pytz.UTC).replace(tzinfo=None)
        date_end = (pytz.timezone(user_tz).
                    localize(datetime(year, month, day, hour=23, minute=59,
                                      second=59)).astimezone(pytz.UTC).
                    replace(tzinfo=None))
        # Active stages: Draft, Open, Invoiced (all stages that block a chair slot)
        active_stages = self._get_active_stage_ids(
            ['draft', 'open', 'invoiced'])
        chairs = request.env['salon.chair'].sudo().search(
            [('active_booking_chairs', '=', True)])
        order_obj = request.env['salon.order'].sudo().search(
            [('chair_id', 'in', chairs.ids),
             ('stage_id', 'in', active_stages), ('start_time', '>=', date_start),
             ('start_time', '<=', date_end)])
        order_details = {
            chair.id: {
                'name': chair.name,
                'orders': [],
            }
            for chair in chairs
        }
        for order in order_obj:
            data = {
                'number': order.id,
                'start_time_only': fields.Datetime.to_string(pytz.UTC.localize(
                    order.start_time).astimezone(pytz.timezone(
                    user_tz)).replace(tzinfo=None))[11:16],
                'end_time_only': fields.Datetime.to_string(pytz.UTC.localize(
                    order.end_time).astimezone(pytz.timezone(
                    user_tz)).replace(tzinfo=None))[11:16],
            }
            if order.chair_id.id in order_details:
                order_details[order.chair_id.id]['orders'].append(data)
        return order_details

    @http.route('/page/salon_management/salon_booking_thank_you',
                type='http', auth="public", website=True, csrf=False)
    def return_thank_you(self, **post):
        """Render the salon booking thank-you page."""
        return request.render('salon_management.salon_booking_thank_you', {})

    @http.route('/salon_booking_form', type='http',
                auth="public", website=True)
    def chair_info(self, **post):
        """Route function that render while clicking Booking menu from website.
           Returns data to booking website"""
        salon_service_obj = request.env['salon.service'].sudo().search([])
        salon_working_hours_obj = request.env['salon.working.hours'].sudo().search([])
        salon_holiday_obj = request.env['salon.holiday'].sudo().search(
            [('holiday', '=', True)])
        date_check = datetime.today().date()
        user_tz = self._get_user_timezone()
        date_start = (pytz.timezone(user_tz).localize(
            datetime.combine(date_check, time(hour=0, minute=0, second=0))).
                      astimezone(pytz.UTC).replace(tzinfo=None))
        date_end = (pytz.timezone(user_tz).localize(
            datetime.combine(date_check, time(hour=23, minute=59, second=59))).
                    astimezone(pytz.UTC).replace(tzinfo=None))
        active_stages = self._get_active_stage_ids(
            ['draft', 'open', 'invoiced'])
        order_obj = request.env['salon.order'].sudo().search(
            [('chair_id.active_booking_chairs', '=', True),
             ('stage_id', 'in', active_stages), ('start_time', '>=', date_start),
             ('start_time', '<=', date_end)])
        return request.render(
            'salon_management.salon_booking_form', {
                'chair_details': request.env['salon.chair'].sudo().search([]),
                'order_details': order_obj,
                'salon_services': salon_service_obj,
                'date_search': date_check,
                'holiday': salon_holiday_obj,
                'working_time': salon_working_hours_obj}
        )


class SalonOrders(http.Controller):
    """Returns the chairs for dashboard"""

    @http.route(route='/salon/chairs', type="jsonrpc", auth="user")
    def get_salon_chair(self, products_per_slide=3):
        """Return the chairs for the (backend) dashboard. Access rights of
        the logged-in user apply, so only salon users get any data."""
        stage_model = request.env['salon.stage']
        active_stages = [s for s in (stage_model._get_stage_id('open'),
                                     stage_model._get_stage_id('invoiced'))
                         if s]
        chairs = []
        for chair in request.env['salon.chair'].search([]):
            orders = request.env['salon.order'].search_count(
                [("chair_id", "=", chair.id),
                 ("stage_id", "in", active_stages)])
            chairs.append({'name': chair.name,
                           'id': chair.id,
                           'orders': orders,
                           'stylist': chair.user_id.name or '',
                           'collection_today': chair.collection_today,
                           'busy': bool(orders)})
        return chairs
