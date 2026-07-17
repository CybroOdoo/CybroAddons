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


class SavoraController(http.Controller):
    _RESERVATION_PREFIX = "Table Reservation:"

    @staticmethod
    def _get_reservation_config():
        """Read reservation time-slot settings from ir.config_parameter.
        Returns (start_hour: float, end_hour: float, interval_min: int).
        """
        ICP = request.env['ir.config_parameter'].sudo()
        start = float(ICP.get_param('restaurant.reservation_start_time', '17.0'))
        end = float(ICP.get_param('restaurant.reservation_end_time', '23.0'))
        interval = int(ICP.get_param('restaurant.reservation_slot_interval', '30'))
        return start, end, interval

    @staticmethod
    def _generate_slot_labels(start_hour, end_hour, interval_min):
        """Build a list of slot label strings (e.g. '05:00 PM') from config."""
        from datetime import datetime, timedelta
        slots = []
        # start_hour is a float like 17.0  ->  17:00
        sh = int(start_hour)
        sm = int(round((start_hour - sh) * 60))
        eh = int(end_hour)
        em = int(round((end_hour - eh) * 60))
        cursor = datetime(2000, 1, 1, sh, sm)
        end_dt = datetime(2000, 1, 1, eh, em)
        delta = timedelta(minutes=interval_min)
        while cursor <= end_dt:
            slots.append(cursor.strftime('%I:%M %p'))
            cursor += delta
        return slots

    def _get_active_reservations(self, start_dt, stop_dt):
        """
        Returns active reservations (calendar.event) that overlap with the given time range.
        :param start_dt: The start datetime of the range.
        :param stop_dt: The end datetime of the range.
        :return: A recordset of calendar.event records.
        """
        return request.env['calendar.event'].sudo().search([
            ('active', '=', True),
            '|', ('name', '=like', f'{self._RESERVATION_PREFIX}%'), ('is_restaurant_reservation', '=', True),
            ('start', '<', stop_dt),
            ('stop', '>', start_dt),
        ])

    @http.route('/menu_test', type='http', auth="public")
    def menu_test(self, **post):
        """
        A simple test route to verify that the menu controller is active.
        """
        return "Route /menu_test is working"

    @http.route(['/menu'], type='http', auth="public", website=True)
    def savora_menu(self, **post):
        """
        Renders the dedicated Menu Page with eCommerce categories and products.
        """
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info("Savora Menu controller called")
        try:
            website = request.website
            # Fetch root categories
            domain = [('parent_id', '=', False)]
            if hasattr(request.env['product.public.category'], 'website_id'):
                domain += ['|', ('website_id', '=', False), ('website_id', '=', website.id)]
            categories = request.env['product.public.category'].sudo().search(domain, order="sequence, id")
            _logger.info("Found %s root categories", len(categories))
            menu_data = []
            for top_cat in categories:
                # Check for sub-categories
                sub_domain = [('parent_id', '=', top_cat.id)]
                if hasattr(request.env['product.public.category'], 'website_id'):
                    sub_domain += ['|', ('website_id', '=', False), ('website_id', '=', website.id)]
                sub_cats = request.env['product.public.category'].sudo().search(sub_domain, order="sequence, id")
                sub_categories_list = []
                if not sub_cats:
                    # Top category has no children, so we show it as a category section
                    p_domain = [
                        ('public_categ_ids', 'in', top_cat.id),
                        ('website_published', '=', True),
                        ('sale_ok', '=', True)
                    ]
                    if hasattr(request.env['product.template'], 'website_id'):
                        p_domain += [('website_id', 'in', [False, website.id])]
                    products = request.env['product.template'].sudo().search(p_domain, order="website_sequence, id")
                    if products:
                        sub_categories_list.append({
                            'category': top_cat,
                            'products': products
                        })
                else:
                    # Top category has children, loop through them
                    for sub_cat in sub_cats:
                        p_domain = [
                            ('public_categ_ids', 'in', sub_cat.id),
                            ('website_published', '=', True),
                            ('sale_ok', '=', True)
                        ]
                        if hasattr(request.env['product.template'], 'website_id'):
                            p_domain += [('website_id', 'in', [False, website.id])]
                        products = request.env['product.template'].sudo().search(p_domain, order="website_sequence, id")
                        if products:
                            sub_categories_list.append({
                                'category': sub_cat,
                                'products': products
                            })
                if sub_categories_list:
                    menu_data.append({
                        'top_category': top_cat,
                        'sub_categories': sub_categories_list
                    })
            values = {
                'menu_data': menu_data,
            }
            _logger.info("Rendering menu with %s top categories", len(menu_data))
            return request.render("theme_savora_restaurant.savora_menu_page", values)
        except Exception as e:
            _logger.error("Error in savora_menu: %s", e, exc_info=True)
            return request.render("theme_savora_restaurant.savora_menu_page", {
                'menu_data': [],
                'error': str(e)
            })

    @http.route(['/story'], type='http', auth="public", website=True)
    def savora_story(self, **post):
        """
        Renders the Our Story page.
        """
        return request.render("theme_savora_restaurant.savora_story_page")

    @http.route(['/reviews'], type='http', auth="public", website=True)
    def savora_reviews(self, **post):
        """
        Renders the dedicated Review Page.
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
        }
        return request.render("theme_savora_restaurant.savora_reviews_page", values)

    @http.route(['/reviews/submit'], type='http', auth="public", methods=['POST'], website=True, csrf=True)
    def submit_review(self, **post):
        """
        Submits a guest review.
        """
        name = post.get('name')
        rating = int(post.get('rating', 5))
        review_text = post.get('review_text')
        if name and review_text:
            request.env['theme.restaurant.review'].sudo().create({
                'name': name,
                'rating': rating,
                'review_text': review_text,
                'is_published': True,  # Automatically public
                'website_id': request.website.id,
            })
        return request.redirect('/reviews?submitted=1')

    @http.route(['/gallery'], type='http', auth="public", website=True)
    def savora_gallery(self, **post):
        """
        Renders the dedicated Gallery Page.
        """
        return request.render("theme_savora_restaurant.savora_gallery_page")

    @http.route(['/reservations'], type='http', auth="public", website=True)
    def savora_reservations(self, **post):
        """
        Renders the custom Reservation Experience System page.
        Passes the configured reservation hours to the template.
        """
        from datetime import datetime
        start_hour, end_hour, _interval = self._get_reservation_config()
        # Convert float hours to readable strings  (17.0 → "5:00 PM")
        sh, sm = int(start_hour), int(round((start_hour - int(start_hour)) * 60))
        eh, em = int(end_hour), int(round((end_hour - int(end_hour)) * 60))
        start_label = datetime(2000, 1, 1, sh, sm).strftime('%I:%M %p').lstrip('0')
        end_label = datetime(2000, 1, 1, eh, em).strftime('%I:%M %p').lstrip('0')
        values = {
            'reservation_start_label': start_label,
            'reservation_end_label': end_label,
        }
        return request.render("theme_savora_restaurant.savora_reservation_page", values)

    @http.route(['/reservations/get_slots'], type='json', auth="public", website=True)
    def get_slots(self, date_str, **kwargs):
        """
        Generates available reservation slots for a specific date.
        Slot range and interval are read from the reservation config
        parameters set in Website → Settings.
        """
        from datetime import datetime, timedelta
        import pytz
        try:
            day_start_local = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return {'error': 'Invalid date format'}

        start_hour, end_hour, interval_min = self._get_reservation_config()
        slot_labels = self._generate_slot_labels(start_hour, end_hour, interval_min)
        reservation_duration = timedelta(minutes=interval_min)

        tz_name = request.env.context.get('tz') or request.env.user.tz or 'UTC'
        user_tz = pytz.timezone(tz_name)

        day_stop_local = day_start_local + timedelta(days=1)
        day = day_start_local.date()

        # Convert bounds to UTC
        utc_day_start = user_tz.localize(day_start_local).astimezone(pytz.utc).replace(tzinfo=None)
        utc_day_stop = user_tz.localize(day_stop_local).astimezone(pytz.utc).replace(tzinfo=None)

        reservations = self._get_active_reservations(utc_day_start, utc_day_stop)
        reserved_ranges = [(event.start, event.stop) for event in reservations]

        today_local = datetime.now(user_tz).date()
        now_time_utc = datetime.utcnow()
        available_times = []

        for slot_label in slot_labels:
            slot_start_local = datetime.strptime(f"{date_str} {slot_label}", '%Y-%m-%d %I:%M %p')
            slot_stop_local = slot_start_local + reservation_duration

            utc_slot_start = user_tz.localize(slot_start_local).astimezone(pytz.utc).replace(tzinfo=None)
            utc_slot_stop = user_tz.localize(slot_stop_local).astimezone(pytz.utc).replace(tzinfo=None)

            if day == today_local and utc_slot_start < now_time_utc:
                continue
            if any(rs < utc_slot_stop and re > utc_slot_start for rs, re in reserved_ranges):
                continue
            available_times.append(slot_label)

        return {'available_times': available_times}

    @http.route(['/reservations/submit'], type='json', auth="public", website=True, csrf=False)
    def submit_reservation(self, **kwargs):
        """
        Submits the reservation and creates a standard Odoo calendar event (Community compatible).
        """
        from datetime import datetime, timedelta
        import pytz
        try:
            if not kwargs.get('date') or not kwargs.get('time'):
                return {'error': 'Reservation date and time are required.'}

            _start_h, _end_h, interval_min = self._get_reservation_config()
            dt_str = f"{kwargs.get('date')} {kwargs.get('time')}"
            local_start_dt = datetime.strptime(dt_str, '%Y-%m-%d %I:%M %p')
            local_stop_dt = local_start_dt + timedelta(minutes=interval_min)

            tz_name = request.env.context.get('tz') or request.env.user.tz or 'UTC'
            user_tz = pytz.timezone(tz_name)

            utc_start_dt = user_tz.localize(local_start_dt).astimezone(pytz.utc).replace(tzinfo=None)
            utc_stop_dt = user_tz.localize(local_stop_dt).astimezone(pytz.utc).replace(tzinfo=None)

            if self._get_active_reservations(utc_start_dt, utc_stop_dt):
                return {'error': 'This reservation time is no longer available. Please choose another slot.'}
            event = request.env['calendar.event'].sudo().create({
                'name': f"{self._RESERVATION_PREFIX} {kwargs.get('name')} ({kwargs.get('party_size')} guests)",
                'start': utc_start_dt,
                'stop': utc_stop_dt,
                'allday': False,
                'is_restaurant_reservation': True,
                'party_size': int(kwargs.get('party_size') or 1),
                'guest_name': kwargs.get('name'),
                'guest_phone': kwargs.get('phone'),
                'guest_email': kwargs.get('email'),
                'description': f"Party Size: {kwargs.get('party_size')}\nPhone: {kwargs.get('phone')}\nEmail: {kwargs.get('email')}\nNotes: {kwargs.get('notes')}",
            })
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

    @http.route(['/savora/cart/data'], type='json', auth="public", website=True)
    def savora_cart_data(self, **kwargs):
        """
        Returns cart data as JSON to populate the custom sidebar.
        """
        order = request.website.sale_get_order()
        if not order:
            return {'lines': [], 'total': '$0.00', 'count': 0}

        lines = []
        for line in order.website_order_line:
            if not line.product_id:
                continue
            lines.append({
                'id': line.id,
                'name': line.name_short or line.product_id.name,
                'qty': int(line.product_uom_qty),
                'price': request.env['ir.qweb.field.monetary'].value_to_html(line.price_reduce_taxexcl,
                                                                             {'display_currency': order.currency_id}),
                'image': f"/web/image/product.product/{line.product_id.id}/image_128",
            })

        total_html = request.env['ir.qweb.field.monetary'].value_to_html(order.amount_total,
                                                                         {'display_currency': order.currency_id})
        return {
            'lines': lines,
            'total': total_html,
            'count': order.cart_quantity,
        }