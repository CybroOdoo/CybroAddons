# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
from odoo import http
from odoo.http import request
from datetime import datetime, timedelta


class SavoraController(http.Controller):

    @http.route(['/gallery'], type='http', auth="public", website=True)
    def savora_gallery(self, **post):
        """
        Renders the Gallery page.
        """
        page = request.env['website.page'].search([('url', '=', '/gallery')], limit=1)
        return request.render("theme_restaurant.savora_gallery_page", {'main_object': page})

    @http.route(['/menu'], type='http', auth="public", website=True)
    def savora_menu(self, **post):
        """
        Renders the Dinner Menu Page with dynamic products from ALL eCommerce categories.
        """
        Category = request.env['product.public.category']
        Product = request.env['product.template']
        prod_sudo = Product.sudo()
        categories = Category.sudo().search([('parent_id', '=', False)], order='sequence, id')
        menu_data = []
        for categ in categories:
            products = prod_sudo.search([
                ('public_categ_ids', 'child_of', categ.id),
                ('website_published', '=', True),
                ('sale_ok', '=', True),
            ], order='website_sequence, id')
            if products:
                menu_data.append({
                    'category': categ,
                    'products': products,
                })
        values = {
            'menu_data': menu_data,
            'main_object': request.env['website.page'].search([('url', '=', '/menu')], limit=1),
        }
        return request.render("theme_restaurant.savora_menu_page", values)

    @http.route(['/story'], type='http', auth="public", website=True)
    def savora_story(self, **post):
        """
        Renders the dedicated Our Story Page.
        """
        page = request.env['website.page'].search([('url', '=', '/story')], limit=1)
        return request.render("theme_restaurant.savora_story_page", {'main_object': page})

    @http.route(['/reservations'], type='http', auth="public", website=True)
    def savora_reservations(self, **post):
        """
        Renders the custom Reservation Experience System page.
        """
        page = request.env['website.page'].search([('url', '=', '/reservations')], limit=1)
        return request.render("theme_restaurant.savora_reservation_page", {'main_object': page})

    @http.route(['/reviews'], type='http', auth="public", website=True)
    def savora_reviews(self, **post):
        """
        Renders the dynamic Review Page.
        """
        reviews = request.env['theme.restaurant.review'].sudo().search([
            ('active', '=', True),
            ('is_published', '=', True),
            '|', ('website_id', '=', False), ('website_id', '=', request.website.id),
        ], order='review_date desc, sequence asc, id desc')
        review_count = len(reviews)
        average_rating = round(sum(reviews.mapped('rating')) / review_count, 1) if review_count else 0.0
        values = {
            'reviews': reviews,
            'review_count': review_count,
            'average_rating': average_rating,
            'summary_note': (
                f"BASED ON {review_count} GUEST REVIEWS"
                if review_count else
                "NO GUEST REVIEWS PUBLISHED YET"
            ),
            'main_object': request.env['website.page'].search([('url', '=', '/reviews')], limit=1),
        }
        return request.render("theme_restaurant.savora_reviews_page", values)

    @http.route(['/reviews/submit'], type='http', auth="public", methods=['POST'], website=True, csrf=True)
    def submit_review(self, **post):
        """
        Handles review submission.
        """
        name = post.get('name')
        rating = int(post.get('rating', 5))
        review_text = post.get('review_text')
        if name and review_text:
            request.env['theme.restaurant.review'].sudo().create({
                'name': name,
                'rating': rating,
                'review_text': review_text,
                'is_published': True,
                'website_id': request.website.id,
            })
        return request.redirect('/reviews?submitted=1')


    @http.route(
            ['/reservations/get_slots'],
            type='json',
            auth="public",
            website=True
        )
    def get_slots(self, date_str, **kwargs):
        """
        Fetch available reservation slots dynamically
        from Website Settings.
        """
        try:
            day = datetime.strptime(date_str, '%Y-%m-%d')
        except Exception:
            return {'error': 'Invalid date format'}
        icp = request.env['ir.config_parameter'].sudo()
        start_time = float(
            icp.get_param(
                'restaurant.reservation_start_time',
                default=17.0
            )
        )
        end_time = float(
            icp.get_param(
                'restaurant.reservation_end_time',
                default=23.0
            )
        )
        interval = int(
            icp.get_param(
                'restaurant.reservation_slot_interval',
                default=30
            )
        )
        start_dt = day.replace(
            hour=int(start_time),
            minute=int((start_time % 1) * 60),
            second=0
        )
        end_dt = day.replace(
            hour=int(end_time),
            minute=int((end_time % 1) * 60),
            second=0
        )
        base_slots = []
        current_slot = start_dt
        while current_slot <= end_dt:
            base_slots.append(
                current_slot.strftime('%I:%M %p')
            )
            current_slot += timedelta(minutes=interval)
        day_start = day.replace(
            hour=0,
            minute=0,
            second=0
        )
        day_end = day.replace(
            hour=23,
            minute=59,
            second=59
        )
        existing_events = request.env[
            'calendar.event'
        ].sudo().search([
            ('start', '>=', day_start),
            ('start', '<=', day_end),
            ('name', 'ilike', 'Reservation'),
        ])
        busy_times = {
            event.start.strftime('%I:%M %p')
            for event in existing_events
        }
        available_times = [
            slot for slot in base_slots
            if slot not in busy_times
        ]
        return {
            'available_times': available_times
        }

    @http.route(['/reservations/submit'], type='json', auth="public", website=True, csrf=False)
    def submit_reservation(self, **kwargs):
        """
        Submits the reservation and creates a standard Odoo calendar event.
        Compatible with Community version.
        """
        from datetime import datetime, timedelta
        try:
            # Parse Date and Time
            dt_str = f"{kwargs.get('date')} {kwargs.get('time')}"
            start_dt = datetime.strptime(dt_str, '%Y-%m-%d %I:%M %p')
            duration = 1.5  # Default 1.5 hours for a table
            stop_dt = start_dt + timedelta(hours=duration)
            # Create standard Odoo Calendar Event
            vals = {
                'name': f"Reservation for {kwargs.get('name')} ({kwargs.get('party_size')} guests)",
                'start': start_dt,
                'stop': stop_dt,
                'allday': False,
                'description': f"Guests: {kwargs.get('party_size')}\nNotes: {kwargs.get('notes')}\nPhone: {kwargs.get('phone')}\nEmail: {kwargs.get('email')}",
            }
            # If user is logged in, link to partner
            if not request.env.user._is_public():
                vals['partner_ids'] = [(4, request.env.user.partner_id.id)]
            event = request.env['calendar.event'].sudo().create(vals)
            # Create the attendee record if email provided
            if kwargs.get('email'):
                partner = request.env['res.partner'].sudo().search([('email', '=', kwargs.get('email'))], limit=1)
                if not partner:
                    partner = request.env['res.partner'].sudo().create({
                        'name': kwargs.get('name'),
                        'email': kwargs.get('email'),
                        'phone': kwargs.get('phone'),
                    })
                request.env['calendar.attendee'].sudo().create({
                    'event_id': event.id,
                    'partner_id': partner.id,
                    'email': kwargs.get('email'),
                    'state': 'accepted',
                })
            return {'success': True, 'event_id': event.id}
        except Exception as e:
            return {'error': str(e)}
