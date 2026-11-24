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
import re
from datetime import timedelta

from odoo import fields, http
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.tools import plaintext2html

REFERENCE_PREFIX = {
    'court': 'BK', 'session': 'SE', 'membership': 'MB', 'contact': 'CT'}
TAG_XMLID = {
    'court': 'theme_aerocourt.crm_tag_court',
    'session': 'theme_aerocourt.crm_tag_session',
    'membership': 'theme_aerocourt.crm_tag_membership',
    'contact': 'theme_aerocourt.crm_tag_contact',
}
SLOT_RE = re.compile(r'^(\d{2}):00$')
EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}$')


class AeroCourtController(http.Controller):
    """Availability of the courts and the requests of the AeroCourt pages."""

    @http.route(['/journal', '/article'], type='http', auth='public',
                website=True, sitemap=False)
    def journal_redirect(self, **kwargs):
        """The Journal is the blog of Odoo: old links end up there."""
        return request.redirect('/blog', code=301)

    @staticmethod
    def _to_date(value):
        """Read a date sent by a visitor.

        :param value: text such as ``2026-11-20``.
        :return: the date, or ``False`` when the text is not a date.
        """
        try:
            return fields.Date.to_date(value)
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _to_number(value, cast=float):
        """Read a number sent by a visitor.

        :param value: text or number.
        :param cast: ``int`` or ``float``.
        :return: the number, ``0`` when it is not a number.
        """
        try:
            return cast(value or 0)
        except (TypeError, ValueError):
            return 0

    def _website(self):
        """Website of the current request.

        :return: the website record.
        """
        return request.env['website'].browse(
            request.env.context['website_id'])

    @http.route('/aerocourt/availability', type='jsonrpc', auth='public',
                website=True)
    def availability(self, date_from, date_to):
        """Courts already taken for each day and slot of a date range.

        :param str date_from: first day, ISO format.
        :param str date_to: last day, ISO format.
        :return: dictionary {day: {slot: [court numbers]}}.
        """
        start = fields.Date.to_date(date_from)
        end = min(fields.Date.to_date(date_to),
                  start + timedelta(days=370))
        leads = request.env['crm.lead'].sudo().search([
            ('aerocourt_kind', '=', 'court'),
            ('aerocourt_date', '>=', start),
            ('aerocourt_date', '<=', end),
        ])
        taken = {}
        for lead in leads:
            day = fields.Date.to_string(lead.aerocourt_date)
            taken.setdefault(day, {}).setdefault(
                lead.aerocourt_slot, []).append(lead.aerocourt_court)
        return taken

    @http.route('/aerocourt/request', type='jsonrpc', auth='public',
                website=True)
    def submit_request(self, kind, **values):
        """Create the CRM lead of a booking, session, membership or message.

        :param str kind: ``court``, ``session``, ``membership`` or ``contact``.
        :return: dictionary with the reference (and the court for a booking),
            or an ``error`` message.
        """
        if kind not in REFERENCE_PREFIX:
            return {'error': request.env._("Unknown request.")}
        name = (values.get('name') or '').strip()[:120]
        phone = (values.get('phone') or '').strip()[:40]
        email = (values.get('email') or '').strip()[:120]
        if not name or not (phone or email):
            return {'error': request.env._("Please give your name and a phone number "
                               "or an email.")}
        if email and not EMAIL_RE.match(email):
            return {'error': request.env._("That email does not look right.")}
        try:
            lead_values = getattr(self, '_%s_values' % kind)(values)
        except ValidationError as error:
            return {'error': str(error.args[0])}
        website = self._website()
        lead = request.env['crm.lead'].sudo().create({
            'contact_name': name,
            'phone': phone,
            'email_from': email,
            'type': 'opportunity',
            'company_id': website.company_id.id,
            'aerocourt_kind': kind,
            'tag_ids': [(6, 0, [request.env.ref(TAG_XMLID[kind]).id])],
            **lead_values,
        })
        reference = '%s-%05d' % (REFERENCE_PREFIX[kind], lead.id)
        lead.aerocourt_reference = reference
        lead.name = '%s · %s' % (reference, lead.name)
        return {'reference': reference, 'court': lead.aerocourt_court}

    def _court_values(self, values):
        """Check a court request and give it the first free court.

        :param dict values: date, slot, rentalCount and total of the request.
        :return: values of the lead.
        :raise ValidationError: when the slot cannot be booked.
        """
        website = self._website()
        day = self._to_date(values.get('date'))
        today = fields.Date.context_today(request.env['crm.lead'])
        if not day or day < today or day > today + timedelta(
                days=website.aerocourt_booking_days):
            raise ValidationError(request.env._("That day cannot be booked."))
        match = SLOT_RE.match(values.get('slot') or '')
        hour = int(match.group(1)) if match else -1
        if not website.aerocourt_open_hour <= hour < website.aerocourt_close_hour:
            raise ValidationError(request.env._("That time is outside our opening hours."))
        rentals = max(0, min(self._to_number(values.get('rentalCount'), int), 8))
        # One request at a time per slot, so that two visitors cannot get the
        # same court.
        request.env.cr.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s))",
            ['aerocourt:%s:%s' % (day, values['slot'])])
        taken = request.env['crm.lead'].sudo().search([
            ('aerocourt_kind', '=', 'court'),
            ('aerocourt_date', '=', day),
            ('aerocourt_slot', '=', values['slot']),
        ]).mapped('aerocourt_court')
        free = [
            '%02d' % number
            for number in range(1, website.aerocourt_court_count + 1)
            if '%02d' % number not in taken]
        if not free:
            raise ValidationError(
                request.env._("Sorry, that slot has just been taken. Please pick another."))
        total = website.aerocourt_court_rate + rentals * website.aerocourt_rental_fee
        return {
            'name': request.env._("Court %(court)s on %(day)s at %(slot)s",
                      court=free[0], day=day, slot=values['slot']),
            'aerocourt_date': day,
            'aerocourt_slot': values['slot'],
            'aerocourt_court': free[0],
            'aerocourt_rental_count': rentals,
            'aerocourt_total': total,
            'expected_revenue': total,
            'description': plaintext2html(request.env._(
                "Court booking request\nDay: %(day)s\nSlot: %(slot)s\n"
                "Court: %(court)s\nRental rackets: %(rentals)s\n"
                "Total: %(total)s",
                day=day, slot=values['slot'], court=free[0],
                rentals=rentals, total=total)),
        }

    def _session_values(self, values):
        """Lead values of a coaching session request.

        :param dict values: session title, time and price of the request.
        :return: values of the lead.
        """
        title = (values.get('sessionTitle') or '').strip()[:120]
        time_label = (values.get('sessionTime') or '').strip()[:60]
        day = self._to_date(values.get('date'))
        return {
            'name': request.env._("Session: %(title)s", title=title),
            'aerocourt_date': day,
            'aerocourt_slot': time_label,
            'aerocourt_total': self._to_number(values.get('price')),
            'description': plaintext2html(request.env._(
                "Session booking request\nSession: %(title)s\n"
                "Time: %(time)s", title=title, time=time_label)),
        }

    def _membership_values(self, values):
        """Lead values of a membership application.

        :param dict values: plan and start of the request.
        :return: values of the lead.
        """
        plan = (values.get('plan') or '').strip()[:60]
        start = (values.get('start') or '').strip()[:60]
        return {
            'name': request.env._("Membership: %(plan)s", plan=plan),
            'description': plaintext2html(request.env._(
                "Membership application\nPlan: %(plan)s\nStart: %(start)s",
                plan=plan, start=start)),
        }

    def _contact_values(self, values):
        """Lead values of a message from the contact page.

        :param dict values: topic and message of the request.
        :return: values of the lead.
        """
        topic = (values.get('topic') or '').strip()[:80]
        message = (values.get('message') or '').strip()[:2000]
        return {
            'name': request.env._("Contact: %(topic)s", topic=topic or request.env._("Enquiry")),
            'description': plaintext2html(message),
        }
