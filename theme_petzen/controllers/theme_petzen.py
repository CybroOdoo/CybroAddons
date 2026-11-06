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

from odoo import http
from odoo.http import request
from odoo.tools import email_normalize

_logger = logging.getLogger(__name__)


class PetzenServices(http.Controller):
    """Serve Petzen pages and their public website endpoints."""

    # ── Pages ────────────────────────────────────────────────────────────────

    @http.route(['/services'], type='http', auth="public", website=True,
                sitemap=True)
    def services(self, **_kw):
        """Render the services page."""
        return request.render("theme_petzen.services_page_template", {})

    @http.route(['/about'], type='http', auth="public", website=True,
                sitemap=True)
    def about(self, **_kw):
        """Render the about page."""
        return request.render("theme_petzen.about_page_template", {})

    @http.route(['/reviews'], type='http', auth="public", website=True,
                sitemap=True)
    def reviews(self, **_kw):
        """Render the customer reviews page."""
        return request.render("theme_petzen.reviews_page_template", {})

    @http.route(['/contact'], type='http', auth="public", website=True,
                sitemap=True)
    def contact(self, **_kw):
        """Render Odoo's contact page."""
        return request.render("website.contactus", {})

    # ── Forms ────────────────────────────────────────────────────────────────

    @http.route(
        ['/petzen/reviews/customer_types'], type='json', auth="public",
        website=True
    )
    def review_customer_types(self, **_kw):
        """Options of the "I am a…" select of the review form (petzen.review.customer_type)."""
        return [{'value': value, 'label': label} for value, label in
                self._petzen_customer_types()]

    def _petzen_customer_types(self):
        """(value, translated label) of petzen.review.customer_type."""
        review_model = request.env['petzen.review']
        return review_model._fields['customer_type']._description_selection(
            review_model.env
        )

    @http.route(
        ['/petzen/reviews/approved'], type='json', auth="public", website=True
    )
    def approved_reviews(self, limit=12, **_kw):
        """Approved petzen.review records for the reviews page (static/src/js/reviews.js).
        Only public data: no e-mail address."""
        try:
            limit = min(max(int(limit or 12), 1), 60)
        except (TypeError, ValueError):
            limit = 12
        reviews = request.env['petzen.review'].sudo().search(
            [('state', '=', 'approved')], limit=limit
        )
        labels = dict(self._petzen_customer_types())
        return [{
            'customer_type': labels.get(review.customer_type) or labels.get(
                'verified', ''),
            'name': review.name or '',
            'initials': ''.join(
                part[0] for part in (review.name or '?').split()[:2]).upper(),
            'rating': min(max(review.rating or 0, 0), 5),
            'review': review.review or '',
        } for review in reviews]

    @http.route(['/reviews/submit'], type='json', auth="public", website=True)
    def submit_review(self, **kw):
        """Save a petzen.review; it is shown on /reviews once approved."""
        name = (kw.get('name') or '').strip()
        email = (kw.get('email') or '').strip()
        review = (kw.get('review') or '').strip()
        if not name or not email or not review:
            return {'success': False,
                    'error': request.env._('Please fill in all required fields.')}
        if not email_normalize(email):
            return {'success': False,
                    'error': request.env._('Please enter a valid email address.')}
        try:
            rating = min(max(int(kw.get('rating') or 5), 1), 5)
        except (TypeError, ValueError):
            rating = 5
        customer_type = kw.get('customer_type') or 'verified'
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
        except Exception:  # pylint: disable=broad-exception-caught
            _logger.exception("Petzen: could not save review")
            return {'success': False,
                    'error': request.env._('Something went wrong. Please try again.')}
        return {'success': True}

    @http.route(['/services/book'], type='json', auth="public", website=True)
    def book_service(self, **kw):
        """Create a CRM lead from the service booking form."""
        values = {
            key: (kw.get(key) or '').strip()
            for key in (
                'pet_name', 'pet_type', 'service', 'owner_name', 'email',
                'phone',
                'date', 'notes',
            )
        }
        required_fields = (
            'pet_name', 'pet_type', 'service', 'owner_name', 'email', 'date'
        )
        if not all(values[key] for key in required_fields):
            return {'success': False,
                    'error': request.env._('Please fill in all required fields.')}
        if not email_normalize(values['email']):
            return {'success': False,
                    'error': request.env._('Please enter a valid email address.')}

        description = '\n'.join([
            f"Service: {values['service']}",
            f"Pet: {values['pet_name']} ({values['pet_type']})",
            f"Preferred date: {values['date']}",
        ])
        if values['notes']:
            description += f"\n\nNotes:\n{values['notes']}"
        return self._create_lead({
            'name': f"[Petzen Booking] {values['service']} for {values['pet_name']}",
            'contact_name': values['owner_name'],
            'email_from': values['email'],
            'phone': values['phone'] or False,
            'description': description,
        })

    @http.route(['/petzen/newsletter'], type='json', auth="public",
                website=True)
    def newsletter(self, email=None, **_kw):
        """Subscribe an email address through a CRM lead."""
        email = (email or '').strip()
        if not email_normalize(email):
            return {'success': False,
                    'error': request.env._('Please enter a valid email address.')}
        return self._create_lead({
            'name': '[Petzen] Newsletter subscription',
            'email_from': email,
            'description': 'Subscribed from the website footer.',
        })

    def _create_lead(self, values):
        """Create a CRM lead from website form values and return the JSON result."""
        try:
            request.env['crm.lead'].sudo().create(
                dict(values, type='lead')
            )
        except Exception:  # pylint: disable=broad-exception-caught
            _logger.exception("Petzen: could not create lead")
            return {'success': False,
                    'error': request.env._('Something went wrong. Please try again.')}
        return {'success': True}

    # ── "Petzen Products" snippet ────────────────────────────────────────────

    @http.route(['/petzen/snippet/products'], type='json', auth="public",
                website=True)
    def snippet_products(self, limit=12, **_kw):
        """Products of the "Pets Categories" for the s_petzen_products snippet."""
        try:
            limit = min(max(int(limit or 12), 1), 48)
        except (TypeError, ValueError):
            limit = 12
        return request.website._petzen_snippet_products(limit=limit)

    # ── "Petzen Categories" snippet ──────────────────────────────────────────

    @http.route(
        ['/petzen/snippet/categories'], type='json', auth="public", website=True
    )
    def snippet_categories(self, limit=5, **_kw):
        """Category tiles for the s_petzen_categories snippet (same data as the
        shop page "Shop by Category" block)."""
        try:
            limit = min(max(int(limit or 5), 1), 20)
        except (TypeError, ValueError):
            limit = 5
        return request.website._petzen_category_cards(limit=limit)
