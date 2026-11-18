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
import re
from datetime import timedelta

from odoo import fields, http
from odoo.http import request
from odoo.tools import plaintext2html
from odoo.tools.misc import format_date

from ..models.website import LISTING_SORTS

EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}$')
PHONE_RE = re.compile(r'^[+()\d\s.-]{7,20}$')
BOOKING_DAYS = 12
LISTINGS_PER_PAGE = 12
WEEKDAY_HOURS = (9, 10, 11, 12, 13, 14, 15, 16, 17)
SATURDAY_HOURS = (10, 11, 12, 13, 14, 15)


class PropelleWebsite(http.Controller):
    """Pages and data routes of the Propelle theme."""

    def _listing_page(self, listing_type, page=1, **kwargs):
        """Render the Buy or the Rent page, one page of listings at a time.

        The choices of the filter bar and the sorting come from the query
        string, so a filtered page can be shared and every page of the
        listings has its own address.

        :param str listing_type: ``sale`` or ``rent``.
        :param int page: number of the page of listings.
        :param kwargs: the query string (``location``, ``type``, ``min``,
            ``max``, ``beds``, ``furnished`` and ``sort``).
        :return: the rendered page.
        """
        website = request.env.website
        filters = {
            'location': kwargs.get('location') or 'all',
            'type': kwargs.get('type') or 'all',
            'min': self._to_int(kwargs.get('min')),
            'max': self._to_int(kwargs.get('max')),
            'beds': self._to_int(kwargs.get('beds')),
            'furnished': kwargs.get('furnished') or 'all',
        }
        sort = kwargs.get('sort') if kwargs.get('sort') in LISTING_SORTS \
            else 'newest'
        total = website._propelle_listing_count(listing_type, filters)
        base_url = '/rent' if listing_type == 'rent' else '/buy'
        url_args = {key: value for key, value in dict(
            filters, sort=sort).items() if value not in (0, 'all', 'newest')}
        pager = website.pager(
            url=base_url, total=total, page=page,
            step=LISTINGS_PER_PAGE, url_args=url_args)
        listings = website._propelle_listings(
            listing_type, filters, sort, offset=pager['offset'],
            limit=LISTINGS_PER_PAGE)
        return request.render('theme_propelle.{}_page'.format(
            'rent' if listing_type == 'rent' else 'buy'), {
            'listing_type': listing_type,
            'listings': listings,
            'total': total,
            'pager': pager,
            'filters': filters,
            'sort': sort,
            'cities': website._propelle_cities(),
            'property_types': website._propelle_property_types(),
            'budgets': website._propelle_budgets(listing_type),
            'stats': website._propelle_listing_stats(listing_type),
        })

    @http.route(['/buy', '/buy/page/<int:page>'], type='http',
                auth='public', website=True, sitemap=True)
    def propelle_buy(self, page=1, **kwargs):
        """Homes for sale."""
        return self._listing_page('sale', page, **kwargs)

    @http.route(['/rent', '/rent/page/<int:page>'], type='http',
                auth='public', website=True, sitemap=True)
    def propelle_rent(self, page=1, **kwargs):
        """Homes for rent."""
        return self._listing_page('rent', page, **kwargs)

    @http.route('/projects', type='http', auth='public', website=True,
                sitemap=True)
    def propelle_projects(self, **kwargs):
        """New developments."""
        website = request.env.website
        projects = website._propelle_projects()
        selling = projects.filtered(lambda p: p.state == 'selling')
        soon = projects.filtered(lambda p: p.state == 'soon')
        priced = (selling or projects).filtered('price_from')
        cheapest = min(priced, key=lambda p: p.price_from) if priced else None
        return request.render('theme_propelle.projects_page', {
            'projects': projects,
            'featured': (projects.filtered('is_featured') or selling)[:3],
            'open_projects': projects.filtered(
                lambda p: p.state != 'completed'),
            'facts': [
                (str(len(selling)), request.env._('Selling now')),
                (str(len(soon)), request.env._('Coming soon')),
                (cheapest.price_label if cheapest else '-',
                 request.env._('Prices from')),
            ],
        })

    @http.route('/booking', type='http', auth='public', website=True,
                sitemap=False)
    def propelle_booking(self, **kwargs):
        """Booking of a viewing or of a valuation."""
        website = request.env.website
        properties = request.env['propelle.property'].sudo()
        listings = properties.search([('is_published', '=', True)])
        today = fields.Date.context_today(request.env.user)
        days = []
        offset = 1
        while len(days) < BOOKING_DAYS:
            day = today + timedelta(days=offset)
            offset += 1
            if day.weekday() != 6:
                days.append(fields.Date.to_string(day))
        return request.render('theme_propelle.booking_page', {
            'listing_data': [l._propelle_card_values() for l in listings],
            'days': days,
            'cities': website._propelle_cities(),
        })

    @http.route('/propelle/data', type='jsonrpc', auth='public', website=True)
    def propelle_data(self, **kwargs):
        """Cities, property types, budgets and counts used by the search
        panel and the snippets of the static pages."""
        website = request.env.website
        return {
            'cities': website._propelle_cities(),
            'types': website._propelle_property_types(),
            'budgets': {
                'sale': website._propelle_budgets('sale'),
                'rent': website._propelle_budgets('rent'),
            },
            'counts': website._propelle_counts(),
        }

    @http.route('/propelle/booking/request', type='jsonrpc', auth='public',
                website=True)
    def propelle_booking_request(self, **post):
        """Create a lead from the request of a viewing or of a valuation.

        :return: dictionary with the reference of the request, or with an
            ``error`` message.
        """
        env = request.env
        mode = 'valuation' if post.get('mode') == 'sell' else 'view'
        name = (post.get('name') or '').strip()
        email = (post.get('email') or '').strip()
        phone = (post.get('phone') or '').strip()
        date = fields.Date.to_date(post.get('date'))
        hour = self._to_int(post.get('hour'))
        if len(name) < 2 or not EMAIL_RE.match(email) \
                or not PHONE_RE.match(phone):
            return {'error': env._('Please check your contact details.')}
        if not date or date <= fields.Date.context_today(env.user) \
                or hour not in self._open_hours(date):
            return {'error': env._('Please choose another day and time.')}
        when = '{} {}'.format(
            format_date(env, date, date_format='full'),
            self._hour_label(hour))
        lines = []
        if mode == 'view':
            listing = env['propelle.property'].sudo().search([
                ('id', '=', self._to_int(post.get('home'))),
                ('is_published', '=', True),
            ], limit=1)
            if not listing:
                return {'error': env._('Please choose a home to view.')}
            title = env._('Viewing request: %(home)s', home=listing.name)
            lines += [
                env._('Home: %(home)s (%(place)s)', home=listing.name,
                      place=listing.location),
                env._('Viewing: %(kind)s', kind=env._('Video call')
                      if post.get('kind') == 'Video call'
                      else env._('In person')),
            ]
        else:
            address = (post.get('address') or '').strip()
            if len(address) < 5:
                return {'error': env._('Please enter the property address.')}
            title = env._('Valuation request: %(address)s', address=address)
            lines += [
                env._('Address: %(address)s', address=address),
                env._('City: %(city)s', city=post.get('city') or '-'),
                env._('Property type: %(kind)s',
                      kind=post.get('ptype') or '-'),
                env._('Bedrooms: %(beds)s', beds=post.get('beds') or '-'),
            ]
        lines.append(env._('Preferred time: %(when)s', when=when))
        notes = (post.get('notes') or '').strip()
        if notes:
            lines.append(env._('Notes: %(notes)s', notes=notes))
        lead = env['crm.lead'].sudo().create({
            'name': title,
            'contact_name': name,
            'email_from': email,
            'phone': phone,
            'description': plaintext2html('\n'.join(lines)),
        })
        return {'reference': 'PRP-{:05d}'.format(lead.id),
                'time': self._hour_label(hour)}

    @http.route('/propelle/alert', type='jsonrpc', auth='public',
                website=True)
    def propelle_alert(self, email=None, city=None, **kwargs):
        """Register a request for new listing alerts as a lead.

        :param email: email of the visitor.
        :param city: name of the city to watch.
        :return: dictionary telling whether the request was saved.
        """
        email = (email or '').strip()
        if not EMAIL_RE.match(email):
            return {'error': request.env._(
                "That email address doesn't look right.")}
        city_record = request.env['propelle.city'].sudo().search(
            [('name', '=', city)], limit=1)
        label = city_record.display_name or request.env._('all cities')
        request.env['crm.lead'].sudo().create({
            'name': request.env._('Listing alert: %(city)s', city=label),
            'email_from': email,
            'description': request.env._(
                'Asked to be emailed when new homes are listed in %(city)s.',
                city=label),
        })
        return {'saved': True, 'city': label}

    @staticmethod
    def _open_hours(date):
        """Hours a visit can start at on the given day: 9am to 5pm on
        weekdays, 10am to 3pm on Saturday, closed on Sunday.

        :param date: the day.
        :return: tuple of hours.
        """
        if date.weekday() == 6:
            return ()
        return SATURDAY_HOURS if date.weekday() == 5 else WEEKDAY_HOURS

    @staticmethod
    def _hour_label(hour):
        """Label of an hour, for example ``2:00 pm``."""
        return '{}:00 {}'.format(
            hour - 12 if hour > 12 else hour, 'pm' if hour >= 12 else 'am')

    @staticmethod
    def _to_int(value):
        """Integer of a posted value, or 0."""
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
