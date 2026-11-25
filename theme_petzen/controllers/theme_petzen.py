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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import logging
from datetime import timedelta

from markupsafe import Markup

from odoo import fields, http
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import email_normalize

_logger = logging.getLogger(__name__)

# Anti-spam of the public forms (review, booking): a hidden "website" field
# that only bots fill in, and a maximum number of submissions per email
# address within PETZEN_THROTTLE_DELAY.
PETZEN_HONEYPOT_FIELD = 'website_url'
PETZEN_THROTTLE_LIMIT = 3
PETZEN_THROTTLE_DELAY = timedelta(hours=1)
PETZEN_MAX_TEXT_LENGTH = 2000

# Services that can be booked from the /services page (options of the
# "Service" select of views/services_templates.xml): (value, lead label).
PETZEN_BOOKING_SERVICES = [
    ('grooming', 'Grooming & Spa'),
    ('veterinary', 'Veterinary Care'),
    ('training', 'Training & Behavior'),
]


class ThemePetzen(http.Controller):
    """Pages, forms and dynamic snippet data of the Petzen theme."""

    # ── Pages ────────────────────────────────────────────────────────────────

    @http.route(['/services'], type='http', auth='public', website=True,
                sitemap=True)
    def services(self, **_kwargs):
        """Render the Services page."""
        return request.render('theme_petzen.services_page_template', {})

    @http.route(['/about'], type='http', auth='public', website=True,
                sitemap=True)
    def about(self, **_kwargs):
        """Render the About page."""
        return request.render('theme_petzen.about_page_template', {})

    @http.route(['/reviews'], type='http', auth='public', website=True,
                sitemap=True)
    def reviews(self, **_kwargs):
        """Render the Reviews page (approved reviews and review form)."""
        return request.render('theme_petzen.reviews_page_template', {})

    @http.route(['/contact'], type='http', auth='public', website=True,
                sitemap=True)
    def contact(self, **_kwargs):
        """Render Odoo's contact us page (styled by the theme) at /contact."""
        return request.render('website.contactus', {})

    # ── Reviews ──────────────────────────────────────────────────────────────

    @http.route(['/petzen/reviews/customer_types'], type='jsonrpc',
                auth='public', website=True)
    def review_customer_types(self, **_kwargs):
        """Return the options of the "I am a…" select of the review form
        (petzen.review.customer_type)."""
        return [{'value': value, 'label': label}
                for value, label in self._petzen_customer_types()]

    def _petzen_customer_types(self):
        """Return the (value, translated label) pairs of
        petzen.review.customer_type."""
        Review = request.env['petzen.review']
        return Review._fields['customer_type']._description_selection(
            Review.env)

    @http.route(['/petzen/reviews/approved'], type='jsonrpc', auth='public',
                website=True)
    def approved_reviews(self, limit=12, **_kwargs):
        """Return the approved reviews shown on the /reviews page
        (static/src/js/reviews.js). Only public data: no email address."""
        try:
            limit = min(max(int(limit or 12), 1), 60)
        except (TypeError, ValueError):
            limit = 12
        reviews = request.env['petzen.review'].sudo().search(
            [('state', '=', 'approved')], limit=limit)
        labels = dict(self._petzen_customer_types())
        return [{
            'customer_type': (labels.get(review.customer_type)
                              or labels.get('verified', '')),
            'name': review.name or '',
            'initials': ''.join(
                part[0] for part in (review.name or '?').split()[:2]).upper(),
            'rating': min(max(review.rating or 0, 0), 5),
            'review': review.review or '',
        } for review in reviews]

    @http.route(['/reviews/submit'], type='jsonrpc', auth='public',
                website=True)
    def submit_review(self, **kwargs):
        """Save a review from the review form; it is shown on /reviews once
        approved in the backend."""
        if self._petzen_is_bot(kwargs):
            # answer as if it worked: never tell a bot why it was ignored
            return {'success': True}
        name = (kwargs.get('name') or '').strip()
        email = (kwargs.get('email') or '').strip()
        review = (kwargs.get('review') or '').strip()[:PETZEN_MAX_TEXT_LENGTH]
        if not name or not email or not review:
            return {
                'success': False,
                'error': request.env._('Please fill in all required fields.')
            }
        if not email_normalize(email):
            return {
                'success': False,
                'error': request.env._('Please enter a valid email address.')
            }
        if self._petzen_is_throttled('petzen.review', 'email', email):
            return {
                'success': False,
                'error': request.env._(
                    'You have already sent several reviews recently. '
                    'Please try again later.')
            }
        try:
            rating = min(max(int(kwargs.get('rating') or 5), 1), 5)
        except (TypeError, ValueError):
            rating = 5
        customer_type = kwargs.get('customer_type') or 'verified'
        if customer_type not in dict(self._petzen_customer_types()):
            customer_type = 'verified'
        try:
            request.env['petzen.review'].sudo().create({
                'name': name,
                'email': email,
                'rating': rating,
                'review': review,
                'customer_type': customer_type,
            })
        except UserError:
            _logger.exception("Petzen: could not save review")
            return {
                'success': False,
                'error': request.env._('Something went wrong. Please try again.')
            }
        return {'success': True}

    # ── Anti-spam ────────────────────────────────────────────────────────────

    def _petzen_is_bot(self, values):
        """Return whether a form was filled in by a bot: the hidden honeypot
        field is empty for every human visitor."""
        return bool((values.get(PETZEN_HONEYPOT_FIELD) or '').strip())

    def _petzen_is_throttled(self, model, email_field, email):
        """Return whether ``email`` already sent PETZEN_THROTTLE_LIMIT records
        of ``model`` within PETZEN_THROTTLE_DELAY."""
        since = fields.Datetime.now() - PETZEN_THROTTLE_DELAY
        count = request.env[model].sudo().search_count([
            (email_field, '=ilike', email),
            ('create_date', '>=', since),
        ], limit=PETZEN_THROTTLE_LIMIT)
        return count >= PETZEN_THROTTLE_LIMIT

    # ── Service booking (CRM lead) ───────────────────────────────────────────

    @http.route(['/petzen/booking'], type='jsonrpc', auth='public',
                website=True)
    def submit_booking(self, **kwargs):
        """Create a CRM lead from the booking form of the /services page; the
        team confirms the slot with the customer."""
        if self._petzen_is_bot(kwargs):
            return {'success': True}
        name = (kwargs.get('name') or '').strip()
        email = (kwargs.get('email') or '').strip()
        phone = (kwargs.get('phone') or '').strip()
        date = (kwargs.get('date') or '').strip()
        notes = (kwargs.get('notes') or '').strip()[:PETZEN_MAX_TEXT_LENGTH]
        services = dict(PETZEN_BOOKING_SERVICES)
        service = kwargs.get('service')
        if not name or not email or service not in services:
            return {
                'success': False,
                'error': request.env._('Please fill in all required fields.')
            }
        if not email_normalize(email):
            return {
                'success': False,
                'error': request.env._('Please enter a valid email address.')
            }
        try:
            date = fields.Date.to_date(date) if date else False
        except ValueError:
            date = False
        if date and date < fields.Date.context_today(request.env.user):
            return {
                'success': False,
                'error': request.env._('Please choose today or a later date.')
            }
        if self._petzen_is_throttled('crm.lead', 'email_from', email):
            return {
                'success': False,
                'error': request.env._(
                    'You have already sent several requests recently. '
                    'Please try again later.')
            }
        service_label = services[service]
        description = [f'Service: {service_label}']
        if date:
            description.append(f'Preferred date: {fields.Date.to_string(date)}')
        if notes:
            description.append(f'Notes: {notes}')
        return self._create_lead({
            'name': f'[Petzen] Booking: {service_label}',
            'contact_name': name,
            'email_from': email,
            'phone': phone,
            'description': Markup('<br/>').join(description),
        })

    # ── Newsletter (CRM lead) ────────────────────────────────────────────────

    @http.route(['/petzen/newsletter'], type='jsonrpc', auth='public',
                website=True)
    def newsletter(self, email=None, **_kwargs):
        """Create a CRM lead from the newsletter form of the footer."""
        email = (email or '').strip()
        if not email_normalize(email):
            return {
                'success': False,
                'error': request.env._('Please enter a valid email address.')
            }
        return self._create_lead({
            'name': '[Petzen] Newsletter subscription',
            'email_from': email,
            'description': 'Subscribed from the website footer.',
        })

    def _create_lead(self, values):
        """Create a CRM lead and return the result expected by the forms."""
        try:
            request.env['crm.lead'].sudo().create(
                dict(values, type='lead')
            )
        except UserError:
            _logger.exception("Petzen: could not create lead")
            return {
                'success': False,
                'error': request.env._('Something went wrong. Please try again.')
            }
        return {'success': True}

    # ── Dynamic snippets ─────────────────────────────────────────────────────

    @http.route(['/petzen/snippet/products'], type='jsonrpc', auth='public',
                website=True)
    def snippet_products(self, limit=12, **_kwargs):
        """Return the tabs and product cards of the "Petzen Products" snippet
        (static/src/js/products_snippet.js)."""
        try:
            limit = min(max(int(limit or 12), 1), 48)
        except (TypeError, ValueError):
            limit = 12
        return request.website._petzen_snippet_products(limit=limit)

    @http.route(['/petzen/snippet/categories'], type='jsonrpc', auth='public',
                website=True)
    def snippet_categories(self, limit=5, **_kwargs):
        """Return the tiles of the "Petzen Categories" snippet
        (static/src/js/categories_snippet.js)."""
        try:
            limit = min(max(int(limit or 5), 1), 20)
        except (TypeError, ValueError):
            limit = 5
        cards = request.website._petzen_category_cards(limit=limit)
        return [{key: card[key] for key in
                 ('name', 'key', 'icon', 'image', 'url', 'count')}
                for card in cards]
