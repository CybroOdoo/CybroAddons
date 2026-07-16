# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from urllib.parse import urlencode

from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import Website as WebsiteController


class FlynovaEventController(http.Controller):
    """Handle Flynova event registration and newsletter routes."""

    def _flynova_process_tickets(self, event, post):
        """Process ticket quantities from a regular POST and return a tickets list."""
        ticket_order = {}
        for key, value in post.items():
            parts = key.split('nb_register-')
            if len(parts) == 2:
                try:
                    qty = int(value)
                    if qty > 0:
                        ticket_order[int(parts[1])] = qty
                except (ValueError, TypeError):
                    pass
        if not ticket_order:
            return []
        ticket_dict = {
            t.id: t for t in request.env['event.event.ticket'].sudo().search([
                ('id', 'in', list(ticket_order.keys())),
                ('event_id', '=', event.id),
            ])
        }
        return [
            {
                'id': tid,
                'ticket': ticket_dict[tid],
                'name': ticket_dict[tid].name,
                'quantity': count,
            }
            for tid, count in ticket_order.items()
            if tid in ticket_dict
        ]

    @http.route(
        ['/flynova/event/<model("event.event"):event>/registration/new'],
        type='http', auth='public', methods=['POST'], website=True, csrf=True,
    )
    def flynova_registration_new(self, event, **post):
        """Handle ticket selection and render the attendee form as a full HTML page."""
        tickets = self._flynova_process_tickets(event, post)
        if not tickets:
            return request.redirect('/event/%s/register' % event.id)
        availability_check = True
        if event.seats_limited:
            ordered_seats = sum(t['quantity'] for t in tickets)
            if event.seats_available < ordered_seats:
                availability_check = False
        default_first_attendee = {}
        if not request.env.user._is_public():
            default_first_attendee = {
                'name': request.env.user.name,
                'email': request.env.user.email or '',
                'phone': request.env.user.phone or '',
            }
        return request.render('theme_flynova.flynova_registration_page', {
            'event': event,
            'main_object': event,
            'tickets': tickets,
            'availability_check': availability_check,
            'limit_check': True,
            'default_first_attendee': default_first_attendee,
            'event_slot_id': post.get('event_slot_id', False),
        })

    @http.route(
        '/flynova/newsletter/subscribe',
        type='http', auth='public', methods=['POST'], website=True, csrf=True,
    )
    def newsletter_subscribe(self, **post):
        """Custom HTTP newsletter subscription handler."""
        email = (post.get('email') or '').strip().lower()
        if email:
            try:
                MailingContact = request.env['mailing.contact'].sudo()
                if not MailingContact.search([('email', '=', email)], limit=1):
                    MailingContact.create({'name': email, 'email': email})
            except Exception:  # noqa: BLE001
                pass
        return request.redirect('/contactus')


class FlynovaThemeController(http.Controller):
    """Render static Flynova website pages."""

    @http.route(['/about-us', '/about', '/aboutus'], type='http', auth='public', website=True)
    def about_page(self, **kwargs):
        """Render the static About Us page.

        Returns:
            werkzeug.wrappers.Response: The rendered 'page_about' QWeb template.
        """
        return request.render('theme_flynova.flynova_page_about', {})

    @http.route('/explore', type='http', auth='public', website=True)
    def explore_page(self, **kwargs):
        """Render the Explore page with destination and highlight data.

        Fetches a sorted list of unique hotel destinations and up to four
        featured products (hotels or tours with images) to display as
        highlights on the explore page.

        Returns:
            werkzeug.wrappers.Response: The rendered 'page_explore' QWeb
                template with 'explore_destinations' and 'explore_highlights'
                context values.
        """
        Product = request.env['product.template'].sudo()
        destinations = Product.read_group(
            [('flynova_listing_type', '=', 'hotel'),
             ('location_name', '!=', False), ('location_name', '!=', '')],
            ['location_name'], ['location_name']
        )
        explore_highlights = Product.search([
            ('flynova_listing_type', 'in', ['hotel', 'tour']),
            ('image_1920', '!=', False),
        ], limit=4)
        return request.render('theme_flynova.flynova_page_explore', {
            'explore_destinations': sorted([d['location_name'] for d in destinations]),
            'explore_highlights': explore_highlights,
        })


class FlynovaHome(WebsiteController):
    """Customize the website home page and booking search behavior."""

    @http.route('/', type='http', auth='public', website=True, sitemap=True)
    def index(self, **kw):
        """Override the website home page to inject destination data into the hero section.

        Collects all unique, non-empty location names from service products and
        adds them to the response's QWeb context as 'hero_destinations' so the
        home page hero can render a destination selector.

        Args:
            **kw: Additional keyword arguments passed through to the parent controller.

        Returns:
            werkzeug.wrappers.Response: The standard website index response with
                'hero_destinations' injected into the QWeb context when available.
        """
        Product = request.env['product.template'].sudo()
        all_products = Product.search([('type', '=', 'service')])
        destinations = sorted(set(all_products.mapped('location_name')) - {False, ''})
        response = super().index(**kw)
        if hasattr(response, 'qcontext'):
            response.qcontext['hero_destinations'] = destinations
        return response

    @http.route('/booking/search', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def booking_search(self, **kwargs):
        """Handle the main booking search form and redirect to the appropriate listing page.

        Reads destination, check-in/out dates, guest count, and listing type from
        the POST body and builds a redirect URL to either '/hotels' or '/tours'
        with the relevant query string parameters appended.

        Args:
            **kwargs: POST fields including 'destination', 'date_in', 'date_out',
                'guests', and 'listing_type'.

        Returns:
            werkzeug.wrappers.Response: A redirect to the filtered hotels or tours page.
        """
        destination  = (kwargs.get('destination') or '').strip()
        date_in      = (kwargs.get('date_in') or '').strip()
        date_out     = (kwargs.get('date_out') or '').strip()
        guests       = (kwargs.get('guests') or '').strip()
        listing_type = (kwargs.get('listing_type') or 'hotel').strip()

        base = '/tours' if listing_type == 'tour' else '/hotels'

        params = {}
        if destination and destination != 'All Destinations':
            params['destination'] = destination
        if date_in:
            params['date_in'] = date_in
        if date_out:
            params['date_out'] = date_out
        if guests and guests != '1':
            params['guests'] = guests

        redirect_url = f'{base}?{urlencode(params)}' if params else base
        return request.redirect(redirect_url)


class FlynovaBooking(http.Controller):
    """Handle Flynova product listings, detail pages, and booking flow."""

    @staticmethod
    def _get_product_domain(parent_category_name):
        """Build the base Odoo search domain for a given listing category.

        Returns a domain that matches service products whose Flynova listing
        type or whose parent product category matches the supplied name.

        Args:
            parent_category_name (str): Either 'Tours' or 'Hotels'.

        Returns:
            list: An Odoo-compatible search domain list.
        """
        listing_type = 'tour' if parent_category_name == 'Tours' else 'hotel'
        return [
            ('type', '=', 'service'),
            '|',
            ('flynova_listing_type', '=', listing_type),
            ('categ_id.parent_id.name', '=', parent_category_name),
        ]

    def _get_products_list(
            self, parent_category_name, page=1, destination=None,
            max_price=None, duration=None, package=None, **kwargs):
        """Fetch and render a paginated, filtered product listing page.

        Applies optional filters for destination, price, duration, and package
        category on top of the base domain for the given listing type. Builds
        a website pager and collects aggregated filter options (all destinations,
        durations, and packages) for the sidebar.

        Args:
            parent_category_name (str): 'Tours' or 'Hotels' — determines the
                base domain and which template to render.
            page (int): Current page number for pagination. Defaults to 1.
            destination (str | None): Location name to filter by.
            max_price (str | None): Upper price limit as a string; parsed to float.
            duration (str | None): Comma-separated duration values to filter by.
            package (str | None): Product category ID to filter by.
            **kwargs: Any additional URL parameters (ignored).

        Returns:
            werkzeug.wrappers.Response: The rendered tour or hotel index template
                with products, pager, filter options, and active filter state.
        """
        Product = request.env['product.template'].sudo()
        domain = self._get_product_domain(parent_category_name)

        if destination and destination != 'All Destinations':
            domain += [('location_name', 'ilike', destination)]

        if duration:
            durations = duration.split(',') if isinstance(duration, str) else duration
            domain += [('duration', 'in', durations)]

        if package:
            domain += [('categ_id.id', '=', int(package))]

        if max_price:
            try:
                domain += [('list_price', '<=', float(max_price))]
            except (ValueError, TypeError):
                pass

        total = Product.search_count(domain)
        ppg = 6
        url = '/tours' if parent_category_name == 'Tours' else '/hotels'

        pager = request.website.pager(
            url=url,
            total=total,
            page=page,
            step=ppg,
            url_args={
                'destination': destination,
                'max_price': max_price,
                'duration': duration,
                'package': package,
            }
        )

        products = Product.search(domain, limit=ppg, offset=pager['offset'])

        all_products = Product.search(self._get_product_domain(parent_category_name))
        all_destinations = sorted(list(set(all_products.mapped('location_name')) - {False, ''}))
        all_durations = sorted(list(set(all_products.mapped('duration')) - {False}))
        all_packages = request.env['product.category'].sudo().search([('parent_id.name', '=', parent_category_name)])

        template = (
            'theme_flynova.flynova_tour_index'
            if parent_category_name == 'Tours'
            else 'theme_flynova.flynova_hotel_index'
        )

        return request.render(template, {
            'products': products,
            'destinations': all_destinations,
            'available_durations': all_durations,
            'packages': all_packages,
            'pager': pager,
            'active_filters': {
                'destination': destination,
                'max_price': max_price or 5000,
                'duration': duration.split(',') if isinstance(duration, str) else (duration or []),
                'package': int(package) if package else None,
            },
            'page_type': parent_category_name,
        })

    @http.route(['/packages', '/packages/page/<int:page>'],
                type='http', auth='public', website=True, sitemap=True)
    def packages_list(self, page=1, destination=None, type=None, max_price=None, duration=None, **kwargs):
        """Redirect legacy '/packages' URLs to the appropriate listing page.

        Preserves backward compatibility by forwarding hotel package requests
        to '/hotels' and everything else to '/tours'.

        Args:
            page (int): Unused page number kept for route compatibility.
            destination (str | None): Unused; kept for route compatibility.
            type (str | None): Listing type; 'hotel' redirects to '/hotels'.
            max_price (str | None): Unused; kept for route compatibility.
            duration (str | None): Unused; kept for route compatibility.
            **kwargs: Additional URL parameters (ignored).

        Returns:
            werkzeug.wrappers.Response: A redirect to '/hotels' or '/tours'.
        """
        if type == 'hotel':
            return request.redirect('/hotels')
        return request.redirect('/tours')

    @http.route(['/tours', '/tours/page/<int:page>'],
                type='http', auth='public', website=True, sitemap=True)
    def tours_list(self, page=1, **kwargs):
        """Render the paginated tours listing page.

        Args:
            page (int): Current page number. Defaults to 1.
            **kwargs: Optional filter parameters forwarded to _get_products_list
                (destination, max_price, duration, package).

        Returns:
            werkzeug.wrappers.Response: The rendered tour index template.
        """
        return self._get_products_list('Tours', page, **kwargs)

    @http.route(['/hotels', '/hotels/page/<int:page>'],
                type='http', auth='public', website=True, sitemap=True)
    def hotels_list(self, page=1, **kwargs):
        """Render the paginated hotels listing page.

        Args:
            page (int): Current page number. Defaults to 1.
            **kwargs: Optional filter parameters forwarded to _get_products_list
                (destination, max_price, duration, package).

        Returns:
            werkzeug.wrappers.Response: The rendered hotel index template.
        """
        return self._get_products_list('Hotels', page, **kwargs)

    @http.route('/tour/<model("product.template"):product>',
                type='http', auth='public', website=True, sitemap=True)
    def tour_detail(self, product, **kwargs):
        """Render the detail page for a single tour product.

        Validates that the product is classified as a tour. If not, redirects
        the visitor to the tours listing page.

        Args:
            product (product.template): The tour product record resolved from
                the URL slug.
            **kwargs: Additional URL parameters.

        Returns:
            werkzeug.wrappers.Response: The rendered tour detail template with
                the product and available extra services, or a redirect to
                '/tours' if the product is not a tour.
        """
        is_tour = product.flynova_listing_type == 'tour' or product.categ_id.parent_id.name == 'Tours'
        if not is_tour:
            return request.redirect('/tours')
        extra_services = request.env['flynova.extra.service'].sudo().search([])

        guests = kwargs.get('guests', '1')
        if not guests or not guests.isdigit() or int(guests) < 1:
            guests = '1'

        return request.render('theme_flynova.flynova_tour_detail', {
            'product': product,
            'main_object': product,
            'extra_services': extra_services,
            'date_in': kwargs.get('date_in', ''),
            'date_out': kwargs.get('date_out', ''),
            'guests': guests,
        })

    @http.route('/hotel/<model("product.template"):hotel>',
                type='http', auth='public', website=True, sitemap=True)
    def hotel_detail(self, hotel, **kwargs):
        """Render the detail page for a single hotel product.

        Validates that the product is classified as a hotel. If not, redirects
        the visitor to the hotels listing page.

        Args:
            hotel (product.template): The hotel product record resolved from
                the URL slug.
            **kwargs: Additional URL parameters.

        Returns:
            werkzeug.wrappers.Response: The rendered hotel detail template with
                the product and available extra services, or a redirect to
                '/hotels' if the product is not a hotel.
        """
        is_hotel = hotel.flynova_listing_type == 'hotel' or hotel.categ_id.parent_id.name == 'Hotels'
        if not is_hotel:
            return request.redirect('/hotels')
        extra_services = request.env['flynova.extra.service'].sudo().search([])

        guests = kwargs.get('guests', '1')
        if not guests or not guests.isdigit() or int(guests) < 1:
            guests = '1'

        return request.render('theme_flynova.flynova_hotel_detail', {
            'product': hotel,
            'main_object': hotel,
            'extra_services': extra_services,
            'date_in': kwargs.get('date_in', ''),
            'date_out': kwargs.get('date_out', ''),
            'guests': guests,
        })

    @http.route('/booking/slot/submit',
                type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def booking_slot_submit(self, **kwargs):
        """Process a booking form submission and populate the current sale order.

        Resolves the selected product, reads guest counts, booking dates, and
        any selected extra services from the POST data. Clears existing order
        lines and creates new ones for adults, children (at 50% price), and
        each active extra service (multiplied by total guest count).

        Args:
            **kwargs: POST fields including 'product_id', 'date_begin',
                'date_end', 'adult_qty', 'child_qty', and any number of
                'extra_service_<id>' boolean flags.

        Returns:
            werkzeug.wrappers.Response: A redirect to the booking payment page
                for the populated sale order, or a redirect to '/' / the
                referring page if validation fails.
        """
        product_id = int(kwargs.get('product_id', 0))
        product = request.env['product.template'].sudo().browse(product_id)
        if not product.exists():
            return request.redirect('/')

        date_begin = kwargs.get('date_begin')
        date_end = kwargs.get('date_end')
        if not date_begin:
            return request.redirect(request.httprequest.referrer or '/')

        adult_qty = int(kwargs.get('adult_qty', 1))
        child_qty = int(kwargs.get('child_qty', 0))

        # Collect selected extra service IDs (posted as 'extra_service_<id>')
        selected_service_ids = []
        for key in kwargs:
            if key.startswith('extra_service_'):
                try:
                    selected_service_ids.append(int(key.replace('extra_service_', '')))
                except ValueError:
                    pass

        sale_order = request.cart or request.website._create_cart()

        # Clear existing lines to ensure we only have the current booking
        sale_order.order_line.unlink()

        sale_order.write({
            'booking_date': date_begin,
            'booking_date_end': date_end,
            'adult_qty': adult_qty,
            'child_qty': child_qty,
            'is_booking_order': True,
            'booking_product_id': product.id,
        })

        product_variant = product.product_variant_id

        # Add Adults line
        if adult_qty > 0:
            request.env['sale.order.line'].sudo().create({
                'order_id': sale_order.id,
                'name': f"{product.name} (Adults)",
                'product_id': product_variant.id,
                'product_uom_qty': adult_qty,
                'price_unit': product.list_price,
            })

        # Add Children line (at 50% price)
        if child_qty > 0:
            request.env['sale.order.line'].sudo().create({
                'order_id': sale_order.id,
                'name': f"{product.name} (Children)",
                'product_id': product_variant.id,
                'product_uom_qty': child_qty,
                'price_unit': product.list_price * 0.5,
            })

        # Add each selected extra service as a line in the order (multiplied by guest count)
        if selected_service_ids:
            ExtraService = request.env['flynova.extra.service'].sudo()
            services = ExtraService.browse(selected_service_ids).filtered('active')
            total_guests = max(adult_qty + child_qty, 1)
            for svc in services:
                request.env['sale.order.line'].sudo().create({
                    'order_id': sale_order.id,
                    'name': f'[Extra Service] {svc.name}',
                    'product_id': product_variant.id,
                    'product_uom_qty': total_guests,
                    'price_unit': svc.price,
                })

        return request.redirect(f'/booking/payment/{sale_order.id}')

    @http.route('/booking/payment/<model("sale.order"):order>',
                type='http', auth='public', website=True)
    def payment_page(self, order, **kwargs):
        """Render the booking payment page for a draft sale order.

        Validates that the order is still in draft state and belongs to the
        current user (or is the active session cart). Fetches compatible
        payment providers, methods, and saved tokens for the order partner,
        then renders the payment template with all required context values.

        Args:
            order (sale.order): The sale order record resolved from the URL.
            **kwargs: Additional URL parameters (ignored).

        Returns:
            werkzeug.wrappers.Response: The rendered 'booking_payment' QWeb
                template, or a redirect to '/' if the order is invalid or
                does not belong to the current user.
        """
        if not order or order.state != 'draft':
            return request.redirect('/')

        if order.id != request.session.get('sale_order_id'):
            if order.partner_id != request.env.user.partner_id:
                return request.redirect('/')

        providers_sudo = request.env['payment.provider'].sudo()._get_compatible_providers(
            order.company_id.id, order.partner_id.id, order.amount_total, currency_id=order.currency_id.id
        )
        payment_methods_sudo = request.env['payment.method'].sudo()._get_compatible_payment_methods(
            providers_sudo.ids, order.partner_id.id, currency_id=order.currency_id.id
        )
        tokens_sudo = request.env['payment.token'].sudo().search([
            ('partner_id', '=', order.partner_id.id),
            ('provider_id', 'in', providers_sudo.ids),
        ])

        request.session['sale_last_order_id'] = order.id

        values = {
            'order': order,
            'sale_order': order,
            'website_sale_order': order,
            'main_object': order,
            'product': order.booking_product_id,
            'providers_sudo': providers_sudo,
            'payment_methods_sudo': payment_methods_sudo,
            'tokens_sudo': tokens_sudo,
            'amount': order.amount_total,
            'currency': order.currency_id,
            'partner_id': order.partner_id.id,
            'access_token': order._portal_ensure_token(),
            'transaction_route': f'/shop/payment/transaction/{order.id}',
            'landing_route': '/booking/payment/validate',
            'show_tokenize_input_mapping': {
                provider.id: (
                    provider.allow_tokenization
                    and not provider._is_tokenization_required()
                )
                for provider in providers_sudo
            },
        }
        return request.render('theme_flynova.flynova_booking_payment', values)

    @http.route('/booking/payment/validate', type='http', auth='public', website=True)
    def booking_payment_validate(self, **kwargs):
        """Validate a completed booking payment and redirect to the confirmation page."""
        order_id = (
            request.session.get('sale_last_order_id')
            or request.session.get('sale_order_id')
        )
        if not order_id:
            return request.redirect('/')
        order = request.env['sale.order'].sudo().browse(order_id).exists()
        if not order:
            return request.redirect('/')
        request.website.sale_reset()
        return request.redirect(f'/booking/confirmation/{order.id}')

    @http.route('/booking/confirmation/<model("sale.order"):order>',
                type='http', auth='public', website=True)
    def booking_confirmation(self, order, **kwargs):
        """Render the booking confirmation page after a successful payment."""
        if not order or order.state not in ('sale', 'done'):
            order_id = request.session.get('sale_last_order_id')
            if order_id:
                order = request.env['sale.order'].sudo().browse(order_id).exists()
            if not order or order.state not in ('sale', 'done', 'draft'):
                return request.redirect('/')
        return request.render('theme_flynova.flynova_booking_confirmation', {
            'order': order,
            'main_object': order,
            'product': order.booking_product_id,
        })
