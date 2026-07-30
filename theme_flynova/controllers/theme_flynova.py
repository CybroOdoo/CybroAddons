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

    def _flynova_process_tickets(self, event, post):
        """
        Parse ticket quantities from a POST payload and build a structured tickets list.

        Iterates over the raw POST data looking for keys in the format
        ``nb_register-<ticket_id>`` and resolves each ticket ID against the
        database, discarding IDs that don't belong to the given event or have
        a quantity of zero.

        Args:
            event (event.event): The event record for which tickets are being
                registered.
            post (dict): The raw POST parameters from the HTTP request.

        Returns:
            list[dict]: A list of dicts, each containing:
                - ``id`` (int): The ticket record ID.
                - ``ticket`` (event.event.ticket): The ticket browse record.
                - ``name`` (str): The ticket name.
                - ``quantity`` (int): The requested quantity.
            Returns an empty list when no valid ticket quantities are found.
        """
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
        """
        Handle the ticket-selection step and render the attendee registration form.

        Validates ticket quantities from the POST body, checks seat availability
        when the event has a seat limit, and pre-fills the first-attendee fields
        for authenticated users. Redirects to the event's register page if no
        valid tickets are found.

        Args:
            event (event.event): The event record resolved from the URL slug.
            **post: Additional POST parameters, including ``nb_register-<id>``
                keys for ticket quantities and an optional ``event_slot_id``.

        Returns:
            werkzeug.wrappers.Response: A rendered HTML response for the
            ``theme_flynova.flynova_registration_page`` template, or an HTTP
            redirect to ``/event/<id>/register`` when no tickets are selected.
        """
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
        """
        Subscribe an email address to the newsletter mailing list.

        Extracts the ``email`` field from the POST body, normalises it to
        lowercase, and creates a ``mailing.contact`` record if one does not
        already exist for that address. Errors during contact creation are
        silently ignored so the redirect always succeeds.

        Args:
            **post: POST parameters. Expected key:
                - ``email`` (str): The email address to subscribe.

        Returns:
            werkzeug.wrappers.Response: An HTTP redirect to the Contact Us
            page.
        """
        email = (post.get('email') or '').strip().lower()
        if email:
            try:
                MailingContact = request.env['mailing.contact'].sudo()
                if not MailingContact.search([('email', '=', email)], limit=1):
                    MailingContact.create({'name': email, 'email': email})
            except Exception:  # noqa: BLE001
                pass
        return request.redirect('/contactus-thank-you')


class FlynovaThemeController(http.Controller):

    @http.route(['/about-us', '/about', '/aboutus'], type='http', auth='public', website=True)
    def about_page(self, **kwargs):
        """
        Render the Flynova "About Us" static page.

        Args:
            **kwargs: Unused query-string parameters forwarded by Odoo.

        Returns:
            werkzeug.wrappers.Response: Rendered HTML for
            ``theme_flynova.page_about``.
        """
        return request.render('theme_flynova.page_about', {})

    @http.route('/explore', type='http', auth='public', website=True)
    def explore_page(self, **kwargs):
        """
        Render the Explore page with destination data and featured highlights.

        Queries all hotel products for their unique ``location_name`` values to
        populate the destination list, and fetches up to four tour/hotel
        products that have a primary image to use as visual highlights.

        Args:
            **kwargs: Unused query-string parameters forwarded by Odoo.

        Returns:
            werkzeug.wrappers.Response: Rendered HTML for
            ``theme_flynova.page_explore`` with context keys:
                - ``explore_destinations`` (list[str]): Sorted destination names.
                - ``explore_highlights`` (product.template recordset): Up to
                  four featured products.
        """
        Product = request.env['product.template'].sudo()
        destinations = Product.read_group(
            [('flynova_listing_type', '=', 'hotel'),
             ('location_name', '!=', False), ('location_name', '!=', '')],
            ['location_name'], ['location_name']
        )
        explore_highlights = Product.search([
            ('flynova_listing_type', 'in', ['hotel','tour']),
            ('image_1920', '!=', False),
        ], limit=4)
        return request.render('theme_flynova.page_explore', {
            'explore_destinations': sorted([d['location_name'] for d in destinations]),
            'explore_highlights': explore_highlights,
        })


class FlynovaHome(WebsiteController):

    @http.route('/', type='http', auth='public', website=True, sitemap=True)
    def index(self, **kw):
        """
        Override the website home page to inject hero-section destination data.

        Calls the parent ``Website.index`` handler, then appends a sorted list
        of unique destination names (derived from all service products) into the
        response's QWeb context so the hero search widget can populate its
        dropdown.

        Args:
            **kw: Keyword arguments passed through from Odoo's routing layer.

        Returns:
            werkzeug.wrappers.Response: The home-page response produced by the
            parent controller, augmented with the ``hero_destinations`` context
            key when the response exposes a ``qcontext`` attribute.
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
        """
        Handle the hero-section search form and redirect to the filtered listing.

        Reads destination, date, guest count, and listing type from the POST
        body, builds a query-string from any non-default values, and redirects
        the user to ``/tours`` or ``/hotels`` with those filters applied.

        Args:
            **kwargs: POST parameters. Expected keys:
                - ``destination`` (str): Destination name filter.
                - ``date_in`` (str): Check-in / start date (``YYYY-MM-DD``).
                - ``date_out`` (str): Check-out / end date (``YYYY-MM-DD``).
                - ``guests`` (str): Number of guests.
                - ``listing_type`` (str): ``'tour'`` or ``'hotel'``
                  (defaults to ``'hotel'``).

        Returns:
            werkzeug.wrappers.Response: An HTTP redirect to the appropriate
            listing page with active filters encoded as query-string parameters.
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

    @staticmethod
    def _get_product_domain(parent_category_name):
        """
        Build the base ORM domain for querying tour or hotel service products.

        Constructs a domain that matches service-type products belonging to the
        given category hierarchy OR carrying the matching
        ``flynova_listing_type`` flag, so products can be discovered via either
        mechanism.

        Args:
            parent_category_name (str): Top-level category name — either
                ``'Tours'`` or ``'Hotels'``.

        Returns:
            list: An Odoo ORM domain list ready to pass to
            ``product.template.search()`` or ``search_count()``.
        """
        listing_type = 'tour' if parent_category_name == 'Tours' else 'hotel'
        return [
            ('type', '=', 'service'),
            '|',
            ('flynova_listing_type', '=', listing_type),
            ('categ_id.parent_id.name', '=', parent_category_name),
        ]

    def _get_products_list(self, parent_category_name, page=1, destination=None, max_price=None, duration=None, package=None, **kwargs):
        """
        Fetch a paginated, filtered product listing and render the index template.

        Applies optional filters (destination, price ceiling, duration, package
        category) on top of the base domain, paginates the results using
        Odoo's website pager, and collects all distinct filter values so the
        template can render the filter sidebar.

        Args:
            parent_category_name (str): ``'Tours'`` or ``'Hotels'``, used to
                determine the domain, URL, and template.
            page (int): Current page number (1-indexed). Defaults to ``1``.
            destination (str | None): Location filter string.
            max_price (str | None): Upper price bound (converted to float).
            duration (str | None): Comma-separated duration values to include.
            package (str | None): Product category ID to restrict results to.
            **kwargs: Additional query-string parameters forwarded by Odoo.

        Returns:
            werkzeug.wrappers.Response: Rendered HTML for either
            ``theme_flynova.flynova_tour_index`` or
            ``theme_flynova.flynova_hotel_index`` with product, pager, and
            filter context data.
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
            url_args={'destination': destination, 'max_price': max_price, 'duration': duration, 'package': package}
        )

        products = Product.search(domain, limit=ppg, offset=pager['offset'])

        all_products = Product.search(self._get_product_domain(parent_category_name))
        all_destinations = sorted(list(set(all_products.mapped('location_name')) - {False, ''}))
        all_durations = sorted(list(set(all_products.mapped('duration')) - {False}))
        all_packages = request.env['product.category'].sudo().search([('parent_id.name', '=', parent_category_name)])

        template = 'theme_flynova.flynova_tour_index' if parent_category_name == 'Tours' else 'theme_flynova.flynova_hotel_index'

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
        """
        Redirect legacy ``/packages`` URLs to the appropriate listing page.

        The ``/packages`` route is kept for backwards compatibility. Requests
        are immediately redirected to ``/hotels`` when ``type='hotel'`` is
        supplied, and to ``/tours`` otherwise.

        Args:
            page (int): Page number from the URL pattern (ignored).
            destination (str | None): Unused; forwarded implicitly via redirect.
            type (str | None): ``'hotel'`` to redirect to hotels, anything
                else redirects to tours.
            max_price (str | None): Unused.
            duration (str | None): Unused.
            **kwargs: Additional query-string parameters (ignored).

        Returns:
            werkzeug.wrappers.Response: An HTTP redirect to ``/hotels`` or
            ``/tours``.
        """
        if type == 'hotel':
            return request.redirect('/hotels')
        return request.redirect('/tours')

    @http.route(['/tours', '/tours/page/<int:page>'],
                type='http', auth='public', website=True, sitemap=True)
    def tours_list(self, page=1, **kwargs):
        """
        Render the paginated tour listing page.

        Args:
            page (int): Current page number. Defaults to ``1``.
            **kwargs: Filter parameters (``destination``, ``max_price``,
                ``duration``, ``package``) passed through to
                :meth:`_get_products_list`.

        Returns:
            werkzeug.wrappers.Response: Rendered HTML for the tour index.
        """
        return self._get_products_list('Tours', page, **kwargs)

    @http.route(['/hotels', '/hotels/page/<int:page>'],
                type='http', auth='public', website=True, sitemap=True)
    def hotels_list(self, page=1, **kwargs):
        """
        Render the paginated hotel listing page.

        Args:
            page (int): Current page number. Defaults to ``1``.
            **kwargs: Filter parameters (``destination``, ``max_price``,
                ``duration``, ``package``) passed through to
                :meth:`_get_products_list`.

        Returns:
            werkzeug.wrappers.Response: Rendered HTML for the hotel index.
        """
        return self._get_products_list('Hotels', page, **kwargs)

    @http.route('/tour/<model("product.template"):product>',
                type='http', auth='public', website=True, sitemap=True)
    def tour_detail(self, product, **kwargs):
        """
        Render the detail page for a single tour product.

        Validates that the resolved product is actually a tour (via the
        ``flynova_listing_type`` flag or its parent category), then fetches all
        active extra services to display on the booking form.

        Args:
            product (product.template): The product record resolved from the
                URL slug.
            **kwargs: Additional query-string parameters (unused).

        Returns:
            werkzeug.wrappers.Response: Rendered HTML for
            ``theme_flynova.flynova_tour_detail``, or an HTTP redirect to
            ``/tours`` if the product is not a tour.
        """
        is_tour = product.flynova_listing_type == 'tour' or product.categ_id.parent_id.name == 'Tours'
        if not is_tour:
            return request.redirect('/tours')
        extra_services = request.env['flynova.extra.service'].sudo().search([])
        return request.render('theme_flynova.flynova_tour_detail', {
            'product': product,
            'main_object': product,
            'extra_services': extra_services,
        })

    @http.route('/hotel/<model("product.template"):hotel>',
                type='http', auth='public', website=True, sitemap=True)
    def hotel_detail(self, hotel, **kwargs):
        """
        Render the detail page for a single hotel product.

        Validates that the resolved product is actually a hotel (via the
        ``flynova_listing_type`` flag or its parent category), then fetches all
        active extra services to display on the booking form.

        Args:
            hotel (product.template): The hotel product record resolved from
                the URL slug.
            **kwargs: Additional query-string parameters (unused).

        Returns:
            werkzeug.wrappers.Response: Rendered HTML for
            ``theme_flynova.flynova_hotel_detail``, or an HTTP redirect to
            ``/hotels`` if the product is not a hotel.
        """
        is_hotel = hotel.flynova_listing_type == 'hotel' or hotel.categ_id.parent_id.name == 'Hotels'
        if not is_hotel:
            return request.redirect('/hotels')
        extra_services = request.env['flynova.extra.service'].sudo().search([])
        return request.render('theme_flynova.flynova_hotel_detail', {
            'product': hotel,
            'main_object': hotel,
            'extra_services': extra_services,
        })

    @http.route('/booking/slot/submit',
                type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def booking_slot_submit(self, **kwargs):
        """
        Process the booking form submission and build a sale order for payment.

        Validates the product, date range, and guest counts from the POST body.
        Gets or creates a website sale order, clears any existing lines, writes
        the booking metadata, then adds order lines for adults (full price),
        children (50 % price), and any selected extra services (per-guest price).
        Stores the sale order ID in the session so the payment page can verify
        ownership.

        Args:
            **kwargs: POST parameters. Expected keys:
                - ``product_id`` (str): ID of the ``product.template`` to book.
                - ``date_begin`` (str): Start date of the booking.
                - ``date_end`` (str | None): End date of the booking.
                - ``adult_qty`` (str): Number of adult guests (default ``1``).
                - ``child_qty`` (str): Number of child guests (default ``0``).
                - ``extra_service_<id>`` (any): Presence of this key indicates
                  the extra service with that ID was selected.

        Returns:
            werkzeug.wrappers.Response: An HTTP redirect to the payment page
            ``/booking/payment/<order_id>``, or to ``/`` when validation fails.
        """
        product_id = int(kwargs.get('product_id', 0))
        product = request.env['product.template'].sudo().browse(product_id)
        if not product.exists():
            return request.redirect('/')

        date_begin = kwargs.get('date_begin')
        date_end = kwargs.get('date_end')
        if not date_begin:
            return request.redirect(request.httprequest.referrer or '/')
        if date_end and date_end < date_begin:
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

        # Odoo 18: use sale_get_order with force_create=True to get or create a cart
        sale_order = request.website.sale_get_order(force_create=True)
        if not sale_order:
            return request.redirect('/')

        # Store sale order id in session for payment page ownership check
        request.session['sale_order_id'] = sale_order.id

        # Clear existing lines to ensure we only have the current booking
        sale_order.order_line.sudo().unlink()

        sale_order.sudo().write({
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
        """
        Render the payment page for a confirmed booking sale order.

        Verifies the order is still in draft state and belongs to the current
        session or authenticated user. Fetches compatible payment providers,
        methods, and saved tokens for the order's partner, then renders the
        payment template with all required context for Odoo's payment widget.

        Args:
            order (sale.order): The sale order record resolved from the URL.
            **kwargs: Additional query-string parameters (unused).

        Returns:
            werkzeug.wrappers.Response: Rendered HTML for
            ``theme_flynova.booking_payment``, or an HTTP redirect to ``/``
            if the order is invalid, not in draft, or doesn't belong to the
            current user/session.
        """
        if not order or order.state != 'draft':
            return request.redirect('/')

        if order.id != request.session.get('sale_order_id'):
            if order.partner_id != request.env.user.partner_id:
                return request.redirect('/')

        booking_product = order.booking_product_id or order.order_line[:1].product_id.product_tmpl_id
        if not booking_product:
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

        values = {
            'order': order,
            'sale_order': order,
            'website_sale_order': order,
            'product': booking_product,
            'main_object': booking_product,
            'seo_object': booking_product,
            'edit_in_backend': False,
            'providers_sudo': providers_sudo,
            'payment_methods_sudo': payment_methods_sudo,
            'tokens_sudo': tokens_sudo,
            'amount': order.amount_total,
            'currency': order.currency_id,
            'partner_id': order.partner_id.id,
            'access_token': order._portal_ensure_token(),
            'transaction_route': f'/shop/payment/transaction/{order.id}',
            'landing_route': f'/booking/confirmation/{order.id}',
            'show_tokenize_input_mapping': {
                provider.id: (
                    provider.allow_tokenization
                    and not provider._is_tokenization_required()
                )
                for provider in providers_sudo
            },
        }
        return request.render('theme_flynova.booking_payment', values)

    @http.route('/booking/confirmation/<model("sale.order"):order>', type='http', auth="public", website=True)
    def booking_confirmation(self, order, **kwargs):
        """
        Custom confirmation page to avoid Odoo's default website_sale redirect logic.
        """
        if not order:
            return request.redirect('/')
        
        booking_product = order.booking_product_id or (order.order_line and order.order_line[0].product_id.product_tmpl_id)
        
        values = {
            'order': order,
            'product': booking_product,
        }
        return request.render('theme_flynova.booking_confirmation', values)
